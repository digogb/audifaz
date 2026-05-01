"""Idempotent SQLite migrations for adding multi-user columns."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def _column_exists(db: AsyncSession, table: str, column: str) -> bool:
    result = await db.execute(text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result.all())


async def _table_exists(db: AsyncSession, table: str) -> bool:
    result = await db.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": table},
    )
    return result.scalar_one_or_none() is not None


async def _ensure_default_user(db: AsyncSession) -> int | None:
    """Return the id of any existing user (or None if no users)."""
    result = await db.execute(text("SELECT id FROM users ORDER BY id LIMIT 1"))
    row = result.first()
    return row[0] if row else None


async def migrate(db: AsyncSession):
    if not await _table_exists(db, "users"):
        return  # fresh DB, nothing to migrate

    default_user_id = await _ensure_default_user(db)

    # error_entries.user_id
    if await _table_exists(db, "error_entries") and not await _column_exists(db, "error_entries", "user_id"):
        await db.execute(text("ALTER TABLE error_entries ADD COLUMN user_id INTEGER REFERENCES users(id)"))
        if default_user_id:
            await db.execute(text("UPDATE error_entries SET user_id = :uid"), {"uid": default_user_id})

    # mock_exams.user_id
    if await _table_exists(db, "mock_exams") and not await _column_exists(db, "mock_exams", "user_id"):
        await db.execute(text("ALTER TABLE mock_exams ADD COLUMN user_id INTEGER REFERENCES users(id)"))
        if default_user_id:
            await db.execute(text("UPDATE mock_exams SET user_id = :uid"), {"uid": default_user_id})

    # question_attempts: needs to drop UNIQUE on question_id and add user_id + UNIQUE(question_id, user_id)
    if await _table_exists(db, "question_attempts") and not await _column_exists(db, "question_attempts", "user_id"):
        await db.execute(text("""
            CREATE TABLE question_attempts_new (
                id INTEGER PRIMARY KEY,
                question_id INTEGER NOT NULL REFERENCES generated_questions(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                alternativa_escolhida VARCHAR(1) NOT NULL,
                acertou BOOLEAN NOT NULL,
                respondido_em DATETIME NOT NULL,
                observacao VARCHAR(500),
                UNIQUE(question_id, user_id)
            )
        """))
        if default_user_id:
            await db.execute(text("""
                INSERT INTO question_attempts_new
                    (id, question_id, user_id, alternativa_escolhida, acertou, respondido_em, observacao)
                SELECT id, question_id, :uid, alternativa_escolhida, acertou, respondido_em, observacao
                FROM question_attempts
            """), {"uid": default_user_id})
        await db.execute(text("DROP TABLE question_attempts"))
        await db.execute(text("ALTER TABLE question_attempts_new RENAME TO question_attempts"))

    await db.commit()
