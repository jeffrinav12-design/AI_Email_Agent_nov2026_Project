from auth.authentication import UserAuthManager
from database.database import EmailHistoryDB


def test_user_can_register_and_login(tmp_path):
    db_path = str(tmp_path / "test.db")
    auth = UserAuthManager(db_path=db_path)

    auth.register_user("alice", "correct horse")
    user = auth.login_user("alice", "correct horse")

    assert user["username"] == "alice"
    assert user["id"] > 0


def test_gmail_accounts_and_history_are_scoped_to_user(tmp_path):
    db_path = str(tmp_path / "test.db")
    auth = UserAuthManager(db_path=db_path)
    history = EmailHistoryDB(db_path=db_path)

    auth.register_user("alice", "password")
    auth.register_user("bob", "password")
    alice = auth.login_user("alice", "password")
    bob = auth.login_user("bob", "password")

    auth.set_gmail_account(alice["id"], "alice@gmail.com", "tokens/alice.json")
    history.save_email(str(alice["id"]), "recipient@example.com", "Hello", "Body", "Professional", "draft_saved", "draft-1")
    history.save_email(str(bob["id"]), "other@example.com", "Other", "Body", "Friendly", "draft_saved", "draft-2")

    assert auth.get_user_gmail_accounts(alice["id"])[0]["gmail_account"] == "alice@gmail.com"
    assert len(history.get_history(user_id=str(alice["id"]))) == 1
    assert history.get_history(user_id=str(alice["id"]))[0]["recipient"] == "recipient@example.com"


def test_login_rejects_wrong_password(tmp_path):
    auth = UserAuthManager(db_path=str(tmp_path / "test.db"))
    auth.register_user("alice", "correct")

    try:
        auth.login_user("alice", "wrong")
    except ValueError as exc:
        assert str(exc) == "Invalid username or password."
    else:
        raise AssertionError("Expected invalid credentials to be rejected")