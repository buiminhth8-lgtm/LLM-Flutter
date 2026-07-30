"""Local-only authentication recovery utility for LLM Studio."""

from __future__ import annotations

import argparse
import shutil
from collections.abc import Sequence
from datetime import datetime
from getpass import getpass
from pathlib import Path

from llm_studio.admin import AdminManager
from llm_studio.config import Config


def resolve_users_file(path: str | None = None, config_path: str | None = None) -> Path:
    """Resolve the local api_users.json path."""
    if path:
        return Path(path).expanduser().resolve()
    config = Config(config_path) if config_path else Config()
    auth_cfg = config.get("auth", {})
    configured = auth_cfg.get("users_file")
    if configured:
        resolved = Path(configured).resolve()
        legacy = (config.models_dir.parent / "api_users.json").resolve()
        if not resolved.exists() and legacy.exists():
            return legacy
        return resolved
    legacy = (config.models_dir.parent / "api_users.json").resolve()
    if legacy.exists():
        return legacy
    return (config.models_dir.parent / "auth" / "api_users.json").resolve()


def backup_users_file(users_file: Path) -> Path | None:
    """Back up api_users.json before local mutations."""
    if not users_file.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = users_file.with_name(f"{users_file.name}.bak-{timestamp}")
    shutil.copy2(users_file, backup)
    return backup


def load_manager(users_file: Path) -> AdminManager:
    return AdminManager(users_file=users_file, audit_log=users_file.parent / "auth_audit.log")


def print_user_list(manager: AdminManager) -> None:
    users = manager.list_users()
    if not users:
        print("No users found.")
        return
    for user in users:
        enabled = "enabled" if user.get("enabled", True) else "disabled"
        print(
            f"{user['user_id']}\trole={user['role']}\t{enabled}\t"
            f"api_key={user.get('api_key_masked', '***')}"
        )


def regenerate_key(users_file: Path, user_id: str) -> str:
    backup = backup_users_file(users_file)
    if backup:
        print(f"Backup created: {backup}")
    manager = load_manager(users_file)
    api_key = manager.regenerate_key(user_id)
    if not api_key:
        raise SystemExit(f"User not found: {user_id}")
    print(f"Regenerated API Key for {user_id}:")
    print(api_key)
    print("Please save this key now. It will not be shown again.")
    return api_key


def reset_admin_password(users_file: Path, password: str | None = None) -> None:
    backup = backup_users_file(users_file)
    if backup:
        print(f"Backup created: {backup}")
    manager = load_manager(users_file)
    new_password = password or getpass("New admin password: ")
    confirm = password or getpass("Confirm admin password: ")
    if new_password != confirm:
        raise SystemExit("Passwords do not match.")
    manager.reset_admin_password(new_password)
    print("Admin password reset successfully.")


def reset_admin(users_file: Path, password: str | None = None) -> str:
    backup = backup_users_file(users_file)
    if backup:
        print(f"Backup created: {backup}")
    manager = load_manager(users_file)
    new_password = password or getpass("New admin password: ")
    confirm = password or getpass("Confirm admin password: ")
    if new_password != confirm:
        raise SystemExit("Passwords do not match.")
    if manager.get_user("admin") is None:
        created = manager.create_admin_if_missing(new_password)
        if created is None or created.plain_api_key is None:
            raise SystemExit("Admin user already exists but could not be reset.")
        print("Admin user created.")
        api_key = created.plain_api_key
    else:
        manager.reset_admin_password(new_password)
        api_key = manager.regenerate_key("admin")
        if not api_key:
            raise SystemExit("Admin user not found.")
    print("Admin password reset successfully.")
    print("New admin API Key:")
    print(api_key)
    print("Please save this key now. It will not be shown again.")
    return api_key


def create_admin_if_missing(users_file: Path, password: str | None = None) -> str | None:
    backup = backup_users_file(users_file)
    if backup:
        print(f"Backup created: {backup}")
    manager = load_manager(users_file)
    if manager.get_user("admin") is not None:
        print("Admin user already exists.")
        return None
    new_password = password or getpass("New admin password: ")
    confirm = password or getpass("Confirm admin password: ")
    if new_password != confirm:
        raise SystemExit("Passwords do not match.")
    admin = manager.create_admin_if_missing(new_password)
    if admin is None or admin.plain_api_key is None:
        raise SystemExit("Admin user could not be created.")
    print("Admin user created.")
    print("New admin API Key:")
    print(admin.plain_api_key)
    print("Please save this key now. It will not be shown again.")
    return admin.plain_api_key


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python tools/reset_auth.py",
        description="Local-only LLM Studio authentication recovery tool.",
    )
    parser.add_argument("--users-file", default=None, help="Path to api_users.json.")
    parser.add_argument("--config", default=None, help="Path to config.yaml.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list-users", action="store_true")
    group.add_argument("--regenerate-key", metavar="USER_ID")
    group.add_argument("--reset-admin-password", action="store_true")
    group.add_argument("--reset-admin", action="store_true")
    group.add_argument("--create-admin-if-missing", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    users_file = resolve_users_file(args.users_file, args.config)
    users_file.parent.mkdir(parents=True, exist_ok=True)

    if args.list_users:
        print_user_list(load_manager(users_file))
    elif args.regenerate_key:
        regenerate_key(users_file, args.regenerate_key)
    elif args.reset_admin_password:
        reset_admin_password(users_file)
    elif args.reset_admin:
        reset_admin(users_file)
    elif args.create_admin_if_missing:
        create_admin_if_missing(users_file)


if __name__ == "__main__":
    main()
