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

    # study_materials.validation_flags
    if await _table_exists(db, "study_materials") and not await _column_exists(db, "study_materials", "validation_flags"):
        await db.execute(text("ALTER TABLE study_materials ADD COLUMN validation_flags JSON"))

    # study_materials.status + error_msg
    if await _table_exists(db, "study_materials") and not await _column_exists(db, "study_materials", "status"):
        await db.execute(text("ALTER TABLE study_materials ADD COLUMN status VARCHAR(20) DEFAULT 'done'"))
    if await _table_exists(db, "study_materials") and not await _column_exists(db, "study_materials", "error_msg"):
        await db.execute(text("ALTER TABLE study_materials ADD COLUMN error_msg VARCHAR(500)"))

    # user_topic_progress
    if not await _table_exists(db, "user_topic_progress"):
        await db.execute(text("""
            CREATE TABLE user_topic_progress (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                topic_id INTEGER NOT NULL REFERENCES topics(id),
                concluido BOOLEAN NOT NULL DEFAULT 0,
                observacao VARCHAR(500),
                UNIQUE(user_id, topic_id)
            )
        """))
        # Migrar dados existentes: para cada topic concluído, criar um registro para o primeiro user
        if default_user_id:
            await db.execute(text("""
                INSERT OR IGNORE INTO user_topic_progress (user_id, topic_id, concluido, observacao)
                SELECT :uid, id, concluido, observacao FROM topics WHERE concluido = 1
            """), {"uid": default_user_id})

    # user_day_progress
    if not await _table_exists(db, "user_day_progress"):
        await db.execute(text("""
            CREATE TABLE user_day_progress (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                study_day_id INTEGER NOT NULL REFERENCES study_days(id),
                status VARCHAR(20) NOT NULL DEFAULT 'pendente',
                notas VARCHAR(2000),
                UNIQUE(user_id, study_day_id)
            )
        """))
        # Migrar dados existentes: dias com status != pendente para o primeiro user
        if default_user_id:
            await db.execute(text("""
                INSERT OR IGNORE INTO user_day_progress (user_id, study_day_id, status, notas)
                SELECT :uid, id, status, notas FROM study_days
                WHERE status != 'pendente' OR notas IS NOT NULL
            """), {"uid": default_user_id})

    await db.commit()
