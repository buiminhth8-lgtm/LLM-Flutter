"""Admin module for managing API users and hashed keys."""

from __future__ import annotations

import json
import secrets
import time
from pathlib import Path

from .auth import Role, normalize_role
from .security import hash_api_key, redact_secret

WEAK_PASSWORDS = {"admin", "123456", "password", "admin123", "12345678", "qwerty"}


def generate_api_key(prefix: str = "sk-llmstudio") -> str:
    """Generate a secure random API key."""
    return f"{prefix}-{secrets.token_hex(20)}"


def _hash_secret(secret: str) -> str:
    from argon2 import PasswordHasher

    return PasswordHasher().hash(secret)


def _verify_secret(secret: str, stored: str) -> bool:
    if stored.startswith("$argon2"):
        from argon2 import PasswordHasher
        from argon2.exceptions import VerifyMismatchError

        try:
            return PasswordHasher().verify(stored, secret)
        except VerifyMismatchError:
            return False
    if stored.startswith("pbkdf2_sha256$"):
        return False
    return secrets.compare_digest(secret, stored)


def _mask_key(key: str) -> str:
    return key[:12] + "..." + key[-4:] if len(key) > 16 else key[:4] + "..."


def _validate_admin_password(password: str) -> str:
    normalized = (password or "").strip()
    if not normalized:
        raise ValueError("管理员密码不能为空。")
    if normalized.lower() in WEAK_PASSWORDS or len(normalized) < 8:
        raise ValueError("管理员密码太弱，至少需要 8 个字符，且不能使用常见弱密码。")
    return normalized


class UserRecord:
    """A single API user record."""

    def __init__(
        self,
        user_id: str,
        api_key_hash: str,
        api_key_masked: str,
        role: str = Role.VIEWER.value,
        note: str = "",
        created_at: float = 0,
        enabled: bool = True,
        updated_at: float = 0,
    ):
        self.user_id = user_id
        self.api_key_hash = api_key_hash
        self.api_key_masked = api_key_masked
        self.role = normalize_role(role, missing_role=Role.ADMIN).value
        self.note = note
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or self.created_at
        self.enabled = enabled
        self.plain_api_key: str | None = None

    def to_dict(self, include_secret: bool = False) -> dict:
        data = {
            "user_id": self.user_id,
            "api_key_hash": self.api_key_hash,
            "api_key_masked": self.api_key_masked,
            "role": self.role,
            "note": self.note,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "enabled": self.enabled,
        }
        if include_secret and self.plain_api_key:
            data["api_key"] = self.plain_api_key
        return data

    def to_public_dict(self) -> dict:
        """Return a UI-safe record without API key hashes or full keys."""
        return {
            "user_id": self.user_id,
            "api_key_masked": self.api_key_masked,
            "role": self.role,
            "note": self.note,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> UserRecord:
        legacy_key = data.get("api_key")
        api_key_hash = data.get("api_key_hash")
        api_key_masked = data.get("api_key_masked")
        if legacy_key and not api_key_hash:
            api_key_hash = hash_api_key(legacy_key)
            api_key_masked = _mask_key(legacy_key)
        if not api_key_hash:
            raise ValueError(f"User {data.get('user_id', '<unknown>')} has no API key hash")
        return cls(
            user_id=data["user_id"],
            api_key_hash=api_key_hash,
            api_key_masked=api_key_masked or "***",
            role=normalize_role(data.get("role"), missing_role=Role.ADMIN).value,
            note=data.get("note", ""),
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0),
            enabled=data.get("enabled", True),
        )


class AdminManager:
    """Manages API users and keys with JSON file persistence."""

    def __init__(
        self,
        data_dir: Path | None = None,
        *,
        users_file: Path | None = None,
        audit_log: Path | None = None,
    ):
        if users_file is None:
            if data_dir is None:
                data_dir = Path("./data/auth")
            self.data_dir = Path(data_dir)
            self._db_path = self.data_dir / "api_users.json"
        else:
            self._db_path = Path(users_file)
            self.data_dir = self._db_path.parent
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._audit_log_path = Path(audit_log) if audit_log else self.data_dir / "auth_audit.log"
        self._users: dict[str, UserRecord] = {}
        self._admin_password_hash = ""
        self.initial_admin_password: str | None = None
        self.load()

    @property
    def db_path(self) -> Path:
        return self._db_path

    def load(self):
        """Load users from JSON file."""
        if self._db_path.exists():
            with open(self._db_path, encoding="utf-8") as f:
                data = json.load(f)
            stored_password = data.get("admin_password_hash") or data.get("admin_password", "")
            if stored_password and not stored_password.startswith("$argon2"):
                self._admin_password_hash = _hash_secret(stored_password)
            else:
                self._admin_password_hash = stored_password
            self._users = {}
            for item in data.get("users", []):
                rec = UserRecord.from_dict(item)
                self._users[rec.user_id] = rec
            self.save()
        else:
            self._users = {}
            self._admin_password_hash = ""

    def save(self):
        """Persist users to JSON file."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "admin_password_hash": self._admin_password_hash,
            "users": [u.to_dict() for u in self._users.values()],
        }
        with open(self._db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @property
    def initialized(self) -> bool:
        return bool(self._admin_password_hash and self._users)

    def initialize(self, admin_password: str, display_name: str = "Admin") -> UserRecord:
        """Initialize the local admin account and return the first API key once."""
        if self.initialized:
            raise ValueError("LLM Studio 已经完成初始化。")
        password = _validate_admin_password(admin_password)
        self._admin_password_hash = _hash_secret(password)
        api_key = generate_api_key()
        admin = UserRecord(
            user_id="admin",
            api_key_hash=hash_api_key(api_key),
            api_key_masked=_mask_key(api_key),
            role=Role.ADMIN.value,
            note=display_name or "Admin",
        )
        admin.plain_api_key = api_key
        self._users["admin"] = admin
        self.save()
        self.write_audit("initialize_admin", "admin")
        print(f"[Admin] Initialized admin API key: {redact_secret(api_key)}")
        return admin

    def verify_admin_password(self, password: str) -> bool:
        """Verify admin dashboard login password."""
        return _verify_secret(password, self._admin_password_hash)

    def change_admin_password(self, old_password: str, new_password: str) -> bool:
        """Change the admin dashboard password."""
        if not self.verify_admin_password(old_password):
            return False
        self._admin_password_hash = _hash_secret(_validate_admin_password(new_password))
        self.save()
        self.write_audit("change_admin_password", "admin")
        return True

    def authenticate(self, user_id: str, api_key: str) -> UserRecord | None:
        """Authenticate by explicit user ID and API key."""
        user = self._users.get(user_id)
        if user and user.enabled and secrets.compare_digest(hash_api_key(api_key), user.api_key_hash):
            return user
        return None

    def authenticate_by_api_key(self, api_key: str) -> UserRecord | None:
        """Authenticate by API key only, used by Authorization: Bearer recovery."""
        if not api_key:
            return None
        key_hash = hash_api_key(api_key)
        for user in self._users.values():
            if user.enabled and secrets.compare_digest(key_hash, user.api_key_hash):
                return user
        return None

    def find_user_by_api_key(self, api_key: str) -> UserRecord | None:
        """Find a user by API key hash without applying enabled checks."""
        if not api_key:
            return None
        key_hash = hash_api_key(api_key)
        for user in self._users.values():
            if secrets.compare_digest(key_hash, user.api_key_hash):
                return user
        return None

    def create_user(self, user_id: str, role: str = Role.VIEWER.value, note: str = "") -> UserRecord:
        """Create a new API user with auto-generated key."""
        if user_id in self._users:
            raise ValueError(f"User '{user_id}' already exists")
        api_key = generate_api_key()
        rec = UserRecord(
            user_id=user_id,
            api_key_hash=hash_api_key(api_key),
            api_key_masked=_mask_key(api_key),
            role=normalize_role(role, missing_role=Role.VIEWER).value,
            note=note,
        )
        rec.plain_api_key = api_key
        self._users[user_id] = rec
        self.save()
        self.write_audit("create_user", user_id)
        return rec

    def list_users(self) -> list[dict]:
        """List all users without full API keys or hashes."""
        return [u.to_public_dict() for u in self._users.values()]

    def get_user(self, user_id: str) -> UserRecord | None:
        return self._users.get(user_id)

    def delete_user(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            self.save()
            self.write_audit("delete_user", user_id)
            return True
        return False

    def toggle_user(self, user_id: str) -> bool | None:
        """Enable/disable a user. Returns new enabled state or None."""
        user = self._users.get(user_id)
        if user:
            user.enabled = not user.enabled
            user.updated_at = time.time()
            self.save()
            self.write_audit("toggle_user", user_id)
            return user.enabled
        return None

    def regenerate_key(self, user_id: str) -> str | None:
        """Regenerate API key for a user. Returns the new key once or None."""
        user = self._users.get(user_id)
        if user:
            api_key = generate_api_key()
            user.api_key_hash = hash_api_key(api_key)
            user.api_key_masked = _mask_key(api_key)
            user.plain_api_key = api_key
            user.updated_at = time.time()
            self.save()
            self.write_audit("regenerate_key", user_id)
            return api_key
        return None

    def update_user(self, user_id: str, role: str | None = None, note: str | None = None) -> bool:
        user = self._users.get(user_id)
        if not user:
            return False
        if role is not None:
            user.role = normalize_role(role, missing_role=Role.VIEWER).value
        if note is not None:
            user.note = note
        user.updated_at = time.time()
        self.save()
        self.write_audit("update_user", user_id)
        return True

    def get_full_key(self, user_id: str) -> str | None:
        """Full keys are no longer recoverable after creation."""
        user = self._users.get(user_id)
        return user.plain_api_key if user else None

    def reset_admin_password(self, new_password: str) -> None:
        """Reset the local admin dashboard password."""
        self._admin_password_hash = _hash_secret(_validate_admin_password(new_password))
        self.save()
        self.write_audit("reset_admin_password", "admin")

    def create_admin_if_missing(self, password: str, note: str = "Admin") -> UserRecord | None:
        """Create admin only when it does not exist. Returns the new admin once."""
        if "admin" in self._users:
            return None
        self._admin_password_hash = _hash_secret(_validate_admin_password(password))
        api_key = generate_api_key()
        admin = UserRecord(
            user_id="admin",
            api_key_hash=hash_api_key(api_key),
            api_key_masked=_mask_key(api_key),
            role=Role.ADMIN.value,
            note=note,
        )
        admin.plain_api_key = api_key
        self._users["admin"] = admin
        self.save()
        self.write_audit("create_admin_if_missing", "admin")
        return admin

    def write_audit(self, action: str, user_id: str) -> None:
        """Append a safe audit entry without passwords or API keys."""
        self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"time": time.time(), "action": action, "user_id": user_id}
        with open(self._audit_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
