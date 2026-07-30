from llm_studio.admin import AdminManager
from tools import reset_auth


def test_reset_auth_regenerate_key_creates_backup_and_changes_hash(tmp_path):
    users_file = tmp_path / "api_users.json"
    manager = AdminManager(users_file=users_file)
    admin = manager.initialize("StrongAdminPassword123")
    old_key = admin.plain_api_key
    old_hash = manager.get_user("admin").api_key_hash

    new_key = reset_auth.regenerate_key(users_file, "admin")
    reloaded = AdminManager(users_file=users_file)

    assert new_key != old_key
    assert reloaded.get_user("admin").api_key_hash != old_hash
    assert reloaded.authenticate("admin", old_key) is None
    assert reloaded.authenticate("admin", new_key) is not None
    assert list(tmp_path.glob("api_users.json.bak-*"))


def test_reset_auth_resets_admin_password_and_keeps_key_hash(tmp_path):
    users_file = tmp_path / "api_users.json"
    manager = AdminManager(users_file=users_file)
    manager.initialize("StrongAdminPassword123")
    old_hash = manager.get_user("admin").api_key_hash

    reset_auth.reset_admin_password(users_file, "NewStrongPassword123")
    reloaded = AdminManager(users_file=users_file)

    assert reloaded.verify_admin_password("NewStrongPassword123") is True
    assert reloaded.get_user("admin").api_key_hash == old_hash
    assert list(tmp_path.glob("api_users.json.bak-*"))


def test_reset_auth_reset_admin_resets_password_and_key(tmp_path):
    users_file = tmp_path / "api_users.json"
    manager = AdminManager(users_file=users_file)
    old_admin = manager.initialize("StrongAdminPassword123")
    old_key = old_admin.plain_api_key

    new_key = reset_auth.reset_admin(users_file, "NewStrongPassword123")
    reloaded = AdminManager(users_file=users_file)

    assert reloaded.verify_admin_password("NewStrongPassword123") is True
    assert reloaded.authenticate("admin", old_key) is None
    assert reloaded.authenticate("admin", new_key) is not None


def test_reset_auth_create_admin_if_missing(tmp_path):
    users_file = tmp_path / "api_users.json"

    new_key = reset_auth.create_admin_if_missing(users_file, "StrongAdminPassword123")
    manager = AdminManager(users_file=users_file)

    assert new_key is not None
    assert manager.get_user("admin").role == "admin"
    assert manager.authenticate("admin", new_key) is not None


def test_reset_auth_list_users_does_not_show_hash(tmp_path, capsys):
    users_file = tmp_path / "api_users.json"
    manager = AdminManager(users_file=users_file)
    manager.initialize("StrongAdminPassword123")

    reset_auth.print_user_list(AdminManager(users_file=users_file))
    output = capsys.readouterr().out

    assert "admin" in output
    assert "api_key_hash" not in output
    assert "$argon2" not in output
