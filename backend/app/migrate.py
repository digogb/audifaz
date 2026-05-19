"""Idempotent SQLite migrations for adding multi-user columns."""
import os
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

    # users.podcast_token
    if await _table_exists(db, "users") and not await _column_exists(db, "users", "podcast_token"):
        await db.execute(text("ALTER TABLE users ADD COLUMN podcast_token VARCHAR(64)"))
        await db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_podcast_token ON users(podcast_token)"))

    # material_audios
    if not await _table_exists(db, "material_audios"):
        await db.execute(text("""
            CREATE TABLE material_audios (
                id INTEGER PRIMARY KEY,
                study_material_id INTEGER NOT NULL UNIQUE REFERENCES study_materials(id),
                status VARCHAR(20) NOT NULL DEFAULT 'pendente',
                arquivo_path VARCHAR(500),
                duracao_seg INTEGER,
                tamanho_bytes INTEGER,
                notebooklm_id VARCHAR(200),
                instrucoes VARCHAR(1000),
                gerado_em DATETIME NOT NULL,
                concluido_em DATETIME,
                error_msg VARCHAR(500),
                tentativas INTEGER NOT NULL DEFAULT 0
            )
        """))
        await db.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_material_audios_study_material_id "
            "ON material_audios(study_material_id)"
        ))

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

    # --- Multi-concurso ---
    # Insere concurso default SEFAZ-CE se ainda não existir (table criada por create_all)
    if await _table_exists(db, "concursos"):
        row = await db.execute(text("SELECT id FROM concursos WHERE slug = 'sefaz-ce-2026'"))
        default_concurso_id = row.scalar_one_or_none()
        if not default_concurso_id:
            await db.execute(text("""
                INSERT INTO concursos (slug, nome, banca, orgao, cargo, data_prova,
                                       descricao, ativo, publico, criado_em)
                VALUES ('sefaz-ce-2026',
                        'SEFAZ-CE 2026 — Auditor Fiscal TI',
                        'FCC', 'SEFAZ-CE', 'B02 Auditor-Fiscal TI',
                        '2026-08-01',
                        'Concurso para Auditor Fiscal de TI da Secretaria da Fazenda do Ceará',
                        1, 1, datetime('now'))
            """))
            row = await db.execute(text("SELECT id FROM concursos WHERE slug = 'sefaz-ce-2026'"))
            default_concurso_id = row.scalar_one()

        # phases.concurso_id
        if await _table_exists(db, "phases") and not await _column_exists(db, "phases", "concurso_id"):
            await db.execute(text("ALTER TABLE phases ADD COLUMN concurso_id INTEGER REFERENCES concursos(id)"))
            await db.execute(
                text("UPDATE phases SET concurso_id = :cid WHERE concurso_id IS NULL"),
                {"cid": default_concurso_id},
            )
            await db.execute(text("CREATE INDEX IF NOT EXISTS ix_phases_concurso_id ON phases(concurso_id)"))

        # users.concurso_atual_id
        if not await _column_exists(db, "users", "concurso_atual_id"):
            await db.execute(text("ALTER TABLE users ADD COLUMN concurso_atual_id INTEGER REFERENCES concursos(id)"))
            await db.execute(
                text("UPDATE users SET concurso_atual_id = :cid WHERE concurso_atual_id IS NULL"),
                {"cid": default_concurso_id},
            )

        # users.is_internal
        if not await _column_exists(db, "users", "is_internal"):
            await db.execute(text("ALTER TABLE users ADD COLUMN is_internal BOOLEAN NOT NULL DEFAULT 0"))
            admin_username = os.environ.get("ADMIN_USERNAME", "").strip()
            if admin_username:
                await db.execute(
                    text("UPDATE users SET is_internal = 1 WHERE username = :u"),
                    {"u": admin_username},
                )

        # Vincula todos os users existentes ao concurso default
        if await _table_exists(db, "user_concursos"):
            await db.execute(
                text("""
                    INSERT OR IGNORE INTO user_concursos (user_id, concurso_id, ativo, criado_em)
                    SELECT id, :cid, 1, datetime('now') FROM users
                """),
                {"cid": default_concurso_id},
            )

        # study_days: drop UNIQUE constraint on `data` (single-tenant legacy).
        # Com multi-concurso, datas se repetem entre concursos.
        idx_list = await db.execute(text("PRAGMA index_list(study_days)"))
        has_unique_on_data = False
        for row in idx_list.all():
            idx_name, is_unique = row[1], row[2]
            if not is_unique:
                continue
            cols = await db.execute(text(f"PRAGMA index_info({idx_name})"))
            if any(c[2] == "data" for c in cols.all()):
                has_unique_on_data = True
                break
        if has_unique_on_data:
            await db.execute(text("""
                CREATE TABLE study_days_new (
                    id INTEGER PRIMARY KEY,
                    week_id INTEGER NOT NULL REFERENCES weeks(id),
                    data DATE NOT NULL,
                    tipo VARCHAR(20) NOT NULL DEFAULT 'util',
                    status VARCHAR(20) NOT NULL DEFAULT 'pendente',
                    notas VARCHAR(2000)
                )
            """))
            await db.execute(text("""
                INSERT INTO study_days_new (id, week_id, data, tipo, status, notas)
                SELECT id, week_id, data, tipo, status, notas FROM study_days
            """))
            await db.execute(text("DROP TABLE study_days"))
            await db.execute(text("ALTER TABLE study_days_new RENAME TO study_days"))
            await db.execute(text("CREATE INDEX ix_study_days_data ON study_days(data)"))

        # error_entries.concurso_id
        if await _table_exists(db, "error_entries") and not await _column_exists(db, "error_entries", "concurso_id"):
            await db.execute(text("ALTER TABLE error_entries ADD COLUMN concurso_id INTEGER REFERENCES concursos(id)"))
            await db.execute(
                text("UPDATE error_entries SET concurso_id = :cid WHERE concurso_id IS NULL"),
                {"cid": default_concurso_id},
            )
            await db.execute(text("CREATE INDEX IF NOT EXISTS ix_error_entries_concurso_id ON error_entries(concurso_id)"))

        # mock_exams.concurso_id
        if await _table_exists(db, "mock_exams") and not await _column_exists(db, "mock_exams", "concurso_id"):
            await db.execute(text("ALTER TABLE mock_exams ADD COLUMN concurso_id INTEGER REFERENCES concursos(id)"))
            await db.execute(
                text("UPDATE mock_exams SET concurso_id = :cid WHERE concurso_id IS NULL"),
                {"cid": default_concurso_id},
            )
            await db.execute(text("CREATE INDEX IF NOT EXISTS ix_mock_exams_concurso_id ON mock_exams(concurso_id)"))

    await db.commit()
