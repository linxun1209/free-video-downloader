import sqlite3
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import database


def _create_legacy_users_table(db_file: Path) -> None:
    conn = sqlite3.connect(db_file)
    try:
        conn.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_vip INTEGER DEFAULT 0,
                vip_expire_at TEXT,
                daily_summary_count INTEGER DEFAULT 0,
                last_summary_date TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_init_db_migrates_profile_columns_and_update_trims_and_persists(tmp_path, monkeypatch):
    db_file = tmp_path / "legacy.db"
    _create_legacy_users_table(db_file)
    monkeypatch.setattr(database, "DB_PATH", str(db_file))

    database.init_db()

    conn = sqlite3.connect(db_file)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    finally:
        conn.close()

    assert {"nickname", "phone", "bio"}.issubset(columns)

    user = database.create_user("alice@example.com", "hashed-password")
    updated = database.update_user_profile(
        user["id"],
        "  Alice  ",
        "  +1 555 0101  ",
        "  Loves long-form summaries.  ",
    )

    assert updated is not None
    assert updated["nickname"] == "Alice"
    assert updated["phone"] == "+1 555 0101"
    assert updated["bio"] == "Loves long-form summaries."

    persisted = database.get_user_by_id(user["id"])
    assert persisted is not None
    assert persisted["nickname"] == "Alice"
    assert persisted["phone"] == "+1 555 0101"
    assert persisted["bio"] == "Loves long-form summaries."
