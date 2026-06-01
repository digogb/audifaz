"""Idempotent SQLite migrations for adding multi-user columns."""
import json
import os
from pathlib import Path
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
            # Inclui theme_slug/brand/requer_assinatura explicitamente: numa tabela
            # criada via create_all (deploy novo), esses NOT NULL não têm DEFAULT no
            # nível do banco (o default é só do ORM), então o INSERT cru precisa supri-los.
            await db.execute(text("""
                INSERT INTO concursos (slug, nome, banca, orgao, cargo, data_prova,
                                       descricao, theme_slug, brand, requer_assinatura,
                                       ativo, publico, criado_em)
                VALUES ('sefaz-ce-2026',
                        'SEFAZ-CE 2026 — Auditor Fiscal TI',
                        'FCC', 'SEFAZ-CE', 'B02 Auditor-Fiscal TI',
                        '2026-08-01',
                        'Concurso para Auditor Fiscal de TI da Secretaria da Fazenda do Ceará',
                        'audifaz', 'audifaz', 0,
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

        # concursos.theme_slug
        if not await _column_exists(db, "concursos", "theme_slug"):
            await db.execute(text("ALTER TABLE concursos ADD COLUMN theme_slug VARCHAR(40) NOT NULL DEFAULT 'audifaz'"))
            await db.execute(text("UPDATE concursos SET theme_slug = 'audifaz' WHERE slug = 'sefaz-ce-2026'"))
            await db.execute(text("UPDATE concursos SET theme_slug = 'lexlumina' WHERE slug = 'tjce-2026'"))

        # concursos.brand + requer_assinatura + preco_cents (Fase 6)
        if not await _column_exists(db, "concursos", "brand"):
            await db.execute(text("ALTER TABLE concursos ADD COLUMN brand VARCHAR(40) NOT NULL DEFAULT 'audifaz'"))
            await db.execute(text("CREATE INDEX IF NOT EXISTS ix_concursos_brand ON concursos(brand)"))
            await db.execute(text("UPDATE concursos SET brand = 'audifaz' WHERE slug = 'sefaz-ce-2026'"))
            await db.execute(text("UPDATE concursos SET brand = 'anajud'  WHERE slug = 'tjce-2026'"))
        if not await _column_exists(db, "concursos", "requer_assinatura"):
            await db.execute(text("ALTER TABLE concursos ADD COLUMN requer_assinatura BOOLEAN NOT NULL DEFAULT 0"))
            await db.execute(text("UPDATE concursos SET requer_assinatura = 1 WHERE slug = 'tjce-2026'"))
        if not await _column_exists(db, "concursos", "preco_cents"):
            await db.execute(text("ALTER TABLE concursos ADD COLUMN preco_cents INTEGER"))
            await db.execute(text("UPDATE concursos SET preco_cents = 19800 WHERE slug = 'tjce-2026'"))

        # study_materials: cross-provider validation pipeline (Fase 7b)
        if await _table_exists(db, "study_materials") and not await _column_exists(db, "study_materials", "tentativas_geracao"):
            await db.execute(text("ALTER TABLE study_materials ADD COLUMN tentativas_geracao INTEGER NOT NULL DEFAULT 1"))
            await db.execute(text("ALTER TABLE study_materials ADD COLUMN validador_provider VARCHAR(20)"))
            await db.execute(text("ALTER TABLE study_materials ADD COLUMN validador_modelo VARCHAR(50)"))
            await db.execute(text("ALTER TABLE study_materials ADD COLUMN validacao_status VARCHAR(20) NOT NULL DEFAULT 'pendente'"))
            await db.execute(text("ALTER TABLE study_materials ADD COLUMN regenerado_em DATETIME"))
            # Backfill: materiais existentes — se tem validation_flags=[] vira 'ok', se tem flags vira 'warning'
            await db.execute(text("UPDATE study_materials SET validacao_status = 'ok' WHERE validation_flags = '[]' OR validation_flags IS NULL"))
            await db.execute(text("UPDATE study_materials SET validacao_status = 'warning' WHERE validation_flags IS NOT NULL AND validation_flags != '[]'"))

        # users.email + termos (Fase 7)
        if not await _column_exists(db, "users", "email"):
            await db.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(200)"))
            await db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email)"))
        if not await _column_exists(db, "users", "termos_aceitos_versao"):
            await db.execute(text("ALTER TABLE users ADD COLUMN termos_aceitos_versao VARCHAR(20)"))
            await db.execute(text("ALTER TABLE users ADD COLUMN termos_aceitos_em DATETIME"))

        # mock_exams.concurso_id
        if await _table_exists(db, "mock_exams") and not await _column_exists(db, "mock_exams", "concurso_id"):
            await db.execute(text("ALTER TABLE mock_exams ADD COLUMN concurso_id INTEGER REFERENCES concursos(id)"))
            await db.execute(
                text("UPDATE mock_exams SET concurso_id = :cid WHERE concurso_id IS NULL"),
                {"cid": default_concurso_id},
            )
            await db.execute(text("CREATE INDEX IF NOT EXISTS ix_mock_exams_concurso_id ON mock_exams(concurso_id)"))

    # Seed inicial de banca_examples a partir do JSON antigo (uma vez só)
    if await _table_exists(db, "banca_examples"):
        count = (await db.execute(text("SELECT COUNT(*) FROM banca_examples"))).scalar()
        if count == 0:
            await _seed_banca_examples_from_json(db)

    # blocos.* (idempotente)
    if await _table_exists(db, "blocos"):
        await _seed_blocos_if_needed(db)

    # topics.bloco_id
    if await _table_exists(db, "topics") and not await _column_exists(db, "topics", "bloco_id"):
        await db.execute(text("ALTER TABLE topics ADD COLUMN bloco_id INTEGER REFERENCES blocos(id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_topics_bloco_id ON topics(bloco_id)"))

    # generated_questions.bloco_id
    if await _table_exists(db, "generated_questions") and not await _column_exists(db, "generated_questions", "bloco_id"):
        await db.execute(text("ALTER TABLE generated_questions ADD COLUMN bloco_id INTEGER REFERENCES blocos(id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_generated_questions_bloco_id ON generated_questions(bloco_id)"))

    # mock_exam_results.bloco_id
    if await _table_exists(db, "mock_exam_results") and not await _column_exists(db, "mock_exam_results", "bloco_id"):
        await db.execute(text("ALTER TABLE mock_exam_results ADD COLUMN bloco_id INTEGER REFERENCES blocos(id)"))
        await db.execute(text("CREATE INDEX IF NOT EXISTS ix_mock_exam_results_bloco_id ON mock_exam_results(bloco_id)"))

    # Backfill: classificar topics/questions/results existentes pelos blocos via keywords
    if await _table_exists(db, "blocos"):
        await _backfill_blocos(db)

    # Temas de redação default
    if await _table_exists(db, "redacao_temas"):
        await _seed_redacao_temas_if_needed(db)

    await db.commit()


_DEFAULT_TEMAS = {
    "sefaz-ce-2026": [
        (
            "Cibersegurança, privacidade e LGPD na transformação digital do Estado",
            "Redija um texto dissertativo-argumentativo sobre **Cibersegurança, privacidade e LGPD na transformação digital do Estado brasileiro**, posicionando-se sobre os desafios institucionais para conciliar inovação com proteção de dados pessoais.",
            "**Texto I.** A Lei Geral de Proteção de Dados (Lei 13.709/2018) estabeleceu, no Brasil, um marco regulatório para o tratamento de dados pessoais, incluindo o setor público. A ANPD tornou-se autoridade competente para fiscalização.\n\n**Texto II.** Incidentes de vazamento de dados envolvendo órgãos públicos cresceram nos últimos anos. O CNJ instituiu a Estratégia Nacional de Segurança Cibernética do Judiciário (Res. CNJ 396/2021) para padronizar políticas mínimas.\n\n**Texto III.** \"Transparência ativa e proteção de dados são valores complementares, não excludentes. O desafio é encontrar o ponto de equilíbrio que respeite o art. 5º, X e XXXIII, da Constituição.\" (extrato de artigo acadêmico)",
        ),
    ],
    "tjce-2026": [
        (
            "Regulação da Inteligência Artificial generativa no serviço público",
            "Redija um texto dissertativo-argumentativo, com extensão de 20 a 30 linhas, sobre **A regulação da inteligência artificial generativa no serviço público brasileiro**, analisando criticamente as implicações éticas, jurídicas e operacionais.",
            "**Texto I.** O CNJ instituiu, em 2023, a Resolução 332/2020 (com alterações posteriores), que estabelece diretrizes para o uso de inteligência artificial no Poder Judiciário, prevendo princípios como transparência, explicabilidade e supervisão humana.\n\n**Texto II.** \"Os sistemas generativos baseados em LLMs apresentam riscos específicos: alucinações factuais, viés algorítmico decorrente dos dados de treinamento e dificuldade de auditoria. Para o serviço público, essas características exigem governança específica.\" (Relatório técnico)\n\n**Texto III.** O PL 2338/2023, em tramitação no Senado, propõe um marco legal para sistemas de IA no Brasil, classificando-os por risco e estabelecendo deveres do agente de IA proporcionais.",
        ),
        (
            "Acesso à Justiça e processo eletrônico: inclusão digital como direito fundamental",
            "Redija um texto dissertativo-argumentativo sobre **O processo eletrônico e a inclusão digital como condição para o acesso à Justiça**, posicionando-se sobre os limites e as condições para que a digitalização não amplie desigualdades.",
            "**Texto I.** O art. 5º, LXXIV, da Constituição assegura ao Estado o dever de prestar assistência jurídica integral e gratuita aos que comprovarem insuficiência de recursos. A Lei 11.419/2006 instituiu o processo eletrônico no Judiciário brasileiro.\n\n**Texto II.** Pesquisa do CGI.br aponta que cerca de 13% dos domicílios brasileiros não tinham acesso à internet em 2023, com forte concentração nas regiões Norte e Nordeste e na população idosa e de menor renda.\n\n**Texto III.** A PDPJ-Br (Res. CNJ 335/2020) busca padronizar sistemas processuais entre tribunais. Iniciativas de balcões físicos do Judiciário e parcerias com defensorias visam mitigar o efeito excludente da digitalização.",
        ),
        (
            "Saúde mental no trabalho e teletrabalho no serviço público",
            "Redija um texto dissertativo-argumentativo sobre **Saúde mental no trabalho, teletrabalho e o dever institucional do empregador público**, analisando as transformações do mundo do trabalho pós-pandemia e seus reflexos no Judiciário e na Administração Pública.",
            "**Texto I.** A Norma Regulamentadora 1 (NR-1), atualizada em 2024, passou a exigir a inclusão de riscos psicossociais no Programa de Gerenciamento de Riscos das empresas, com aplicação subsidiária ao serviço público.\n\n**Texto II.** Dados da Previdência Social indicam que afastamentos por transtornos mentais e comportamentais cresceram 38% entre 2019 e 2023 no Brasil, com destaque para ansiedade, burnout e depressão.\n\n**Texto III.** O Judiciário ampliou regimes de teletrabalho integral e híbrido após a pandemia. Estudos apontam ganhos de produtividade convivendo com risco de jornada estendida e isolamento.",
        ),
    ],
}


async def _seed_redacao_temas_if_needed(db: AsyncSession):
    """Insere temas default por concurso, somente se ainda não houver tema para o concurso."""
    rows = (await db.execute(text("SELECT id, slug FROM concursos"))).all()
    for cid, cslug in rows:
        count = (await db.execute(
            text("SELECT COUNT(*) FROM redacao_temas WHERE concurso_id = :cid"),
            {"cid": cid},
        )).scalar()
        if count and count > 0:
            continue
        defaults = _DEFAULT_TEMAS.get(cslug)
        if not defaults:
            continue
        for ordem, (titulo, enunciado, apoio) in enumerate(defaults):
            await db.execute(
                text("""
                    INSERT INTO redacao_temas
                        (concurso_id, titulo, enunciado_md, textos_apoio_md, ativo, ordem, criado_em)
                    VALUES (:cid, :titulo, :enu, :apoio, 1, :ordem, datetime('now'))
                """),
                {"cid": cid, "titulo": titulo, "enu": enunciado, "apoio": apoio, "ordem": ordem},
            )


# Blocos default por concurso. Slugs estáveis; nomes/pesos editáveis depois via admin.
# Extraídos da seção 7 do plano TJCE e do plano SEFAZ.
_DEFAULT_BLOCOS = {
    "sefaz-ce-2026": [
        # TI técnico
        ("ti-governanca", "Governança e Processos (ITIL/COBIT/PMBOK)", 3.0, "alta", 15.0, 80.0, "itil,cobit,pmbok,governanca,governança,cmmi,togaf"),
        ("ti-engenharia", "Engenharia de Software (UML/BPMN/Ágeis/Testes)", 2.5, "media", 8.0, 75.0, "uml,bpmn,scrum,kanban,xp,tdd,bdd,refatoração,solid,gof,padrões,testes,requisitos"),
        ("ti-seguranca", "Segurança da Informação (ISO 27k/OWASP/LGPD)", 3.0, "alta", 12.0, 80.0, "iso 27,owasp,zero trust,siem,criptografia,pki,oauth,oidc,lgpd,sgsi,nist,seg info"),
        ("ti-dados", "Banco de Dados e DW (SQL/PostgreSQL/Oracle/NoSQL)", 2.0, "media", 8.0, 75.0, "sql,banco,postgres,oracle,nosql,mongodb,redis,cassandra,etl,dw,olap,data lake,kafka,window"),
        ("ti-arquitetura", "Arquitetura, DevOps e Cloud", 2.0, "media", 7.0, 80.0, "microsserviços,microservices,ddd,hexagonal,kubernetes,docker,ci/cd,cloud,aws,azure,gcp,iac,terraform"),
        ("ti-prog-web", "Programação e Web (Java/Python/JS/REST)", 1.5, "baixa", 4.0, 85.0, "java,python,javascript,react,angular,vue,node,rest,api,html,css,git"),
        ("ti-so-redes", "Sistemas Operacionais e Redes", 1.5, "media", 4.0, 70.0, "linux,unix,windows,redes,tcp,udp,osi,dns,dhcp,vpn,firewall,roteamento"),
        # Direito/legislação
        ("dir-tributario", "Direito Tributário (CTN, Reforma)", 3.0, "alta", 10.0, 75.0, "tributário,tributario,ctn,icms,issqn,iss,iptu,ipva,reforma tributária,ibs,cbs"),
        ("dir-constitucional", "Direito Constitucional", 2.0, "media", 6.0, 70.0, "constitucional,cf 88,art. 5,limpe,fundamentos,direitos sociais"),
        ("dir-administrativo", "Direito Administrativo (8.112, 14.133, 8.429)", 2.0, "media", 6.0, 70.0, "administrativo,8.112,licitação,licitacao,14.133,improbidade,8.429,12.527,lai"),
        ("contabilidade", "Contabilidade Geral e Pública", 2.0, "media", 6.0, 70.0, "contabil,contábil,balanço,mcasp,nbc,patrimônio,demonstrações"),
        ("auditoria", "Auditoria", 1.5, "baixa", 3.0, 70.0, "auditoria,nbc ta,iso 19011,independência,parecer"),
        # CG
        ("portugues", "Língua Portuguesa", 1.0, "alta", 8.0, 80.0, "portugues,português,gramatica,sintaxe,crase,regência,redação"),
        ("rlm", "Raciocínio Lógico-Matemático", 1.0, "media", 5.0, 70.0, "rlm,raciocinio,lógica,proposição,estatística,probabilidade,matemática"),
        ("outros", "Outros / Não classificado", 0.5, "baixa", 0.0, 60.0, ""),
    ],
    "tjce-2026": [
        # CE (peso 3) — estrutura alinhada à retificação do edital F06 (29/05/2026)
        ("produto-gestao", "Gestão de Produtos, Estratégia e Design (temas 1–3)", 3.0, "alta", 16.0, 80.0, "visão de produto,gestão de produto,backlog,moscow,rice,wsjf,mvp,mmf,roadmap,okr,product discovery,design thinking,scamper,jobs to be done,jtbd,stakeholder,product owner,product manager,canvas,prd,feature flag,dark launch,ciclo de vida,usabilidade,acessibilidade,e-mag,prototipação"),
        ("agilidade-metricas", "Agilidade, Fluxo e Métricas de Produto (temas 4–5)", 3.0, "alta", 8.0, 80.0, "scrum,kanban,flight levels,pi planning,limite de wip,lead time,cycle time,throughput,cfd,cumulative flow,nps,csat,cohort,teste a/b,outcome,output,métricas de processo,métricas de produto"),
        ("riscos-qualidade", "Riscos, Qualidade, Conformidade e LGPD (tema 6)", 2.5, "alta", 7.0, 80.0, "gestão de riscos,privacy by design,privacy by default,finops,lgpd,13.709,base legal,anpd,encarregado,titular,conformidade,qualidade de software"),
        ("dominio-eng", "Eng. de Domínio, SW Moderno e Java (temas 7,12,13)", 2.5, "media", 13.0, 78.0, "ddd,bounded context,linguagem ubíqua,context mapping,strangler,dívida técnica,modelo time,api-led,microsserviços,microservices,docker,kubernetes,devsecops,observabilidade,java,spring,hibernate,jpa,kafka,rabbitmq,mensageria,circuit breaker,service discovery,api gateway,interoperabilidade,pdpj"),
        ("software-assurance", "Software Assurance / Segurança (tema 8)", 3.0, "alta", 9.0, 78.0, "owasp samm,samm,threat modeling,modelagem de ameaças,security by design,sdlc seguro,iam,rbac,abac,menor privilégio,sbom,cadeia de suprimentos,supply chain,não-repúdio,ripd,dpia,mfa,sso,oauth,oidc"),
        ("ia-aplicada", "IA aplicada ao produto (tema 9)", 3.0, "alta", 8.0, 78.0, "inteligência artificial,machine learning,aprendizado de máquina,pln,processamento de linguagem,ia generativa,llm,engenharia de prompt,rag,retrieval-augmented,agentes,agênticos,alucinação,cnj 615,explicabilidade,human-in-the-loop,ética"),
        ("dados-rpa", "Engenharia de Dados e RPA (temas 10–11)", 2.0, "media", 7.0, 75.0, "data lake,data warehouse,lakehouse,modelagem dimensional,star schema,snowflake,etl,elt,linhagem,metadados,catalogação,governança de dados,processamento distribuído,rpa,hyperautomation,ocr,bpm"),
        ("contratacoes-tic", "Contratação e Fiscalização de TIC (tema 14)", 3.0, "alta", 7.0, 82.0, "14.133,contratação,licitação,licitacao,etp,termo de referência,pdtic,gestão contratual,fiscal técnico,sla,ans,dispensa,inexigibilidade,reequilíbrio,cnj,governança de tic"),
        # Legislação CE
        ("leg-ce", "Legislação CE + Direitos PCD", 1.0, "alta", 6.0, 80.0, "9.826,16.397,estatuto,organização judiciária,previdência,pcd,deficiência,csjt 386,13.146,acessibilidade,10.098,5.296"),
        # CG
        ("portugues", "Língua Portuguesa", 1.0, "alta", 11.0, 78.0, "portugues,português,crase,regência,concordância,morfossintaxe,pontuação,ortografia,acentuação,pronomes,figuras de linguagem,coordenação,subordinação"),
        ("rlm", "Raciocínio Lógico-Matemático", 1.0, "media", 7.0, 72.0, "rlm,raciocínio,raciocinio,lógica,proposição,conectivos,tabela-verdade,silogismo,estatística,porcentagem,regra de três,desvio padrão,média,mediana,moda,variância"),
        ("ingles", "Inglês técnico", 1.0, "baixa", 1.0, 70.0, "inglês técnico,english"),
        ("redacao", "Redação dissertativa", 1.0, "media", 4.0, 75.0, "redação,redacao,dissertativo,argumentação,coesão"),
        ("outros", "Outros / Não classificado", 0.5, "baixa", 0.0, 60.0, ""),
    ],
}


async def _seed_blocos_if_needed(db: AsyncSession):
    """Cria blocos default por concurso, se ainda não houver nenhum para o concurso."""
    rows = await db.execute(text("SELECT id, slug FROM concursos"))
    for cid, cslug in rows.all():
        count = (await db.execute(
            text("SELECT COUNT(*) FROM blocos WHERE concurso_id = :cid"),
            {"cid": cid},
        )).scalar()
        if count and count > 0:
            continue
        defaults = _DEFAULT_BLOCOS.get(cslug)
        if not defaults:
            continue
        for ordem, (slug, nome, peso, prio, alloc, meta, kws) in enumerate(defaults):
            await db.execute(
                text("""
                    INSERT OR IGNORE INTO blocos
                        (concurso_id, slug, nome, peso, prioridade, alocacao_pct,
                         meta_acerto_pct, ordem, keywords)
                    VALUES (:cid, :slug, :nome, :peso, :prio, :alloc, :meta, :ordem, :kws)
                """),
                {"cid": cid, "slug": slug, "nome": nome, "peso": peso,
                 "prio": prio, "alloc": alloc, "meta": meta, "ordem": ordem,
                 "kws": kws},
            )


def _match_bloco(text_lower: str, blocos: list[tuple]) -> int | None:
    """Recebe (id, slug, keywords) por bloco; retorna primeiro bloco cuja keyword aparece."""
    for bid, slug, keywords in blocos:
        if not keywords:
            continue
        for kw in keywords.split(","):
            kw = kw.strip().lower()
            if kw and kw in text_lower:
                return bid
    # Fallback: bloco "outros" se existir
    for bid, slug, _ in blocos:
        if slug == "outros":
            return bid
    return None


async def _backfill_blocos(db: AsyncSession):
    """Classifica topics/questions/results não-classificados via heurística de keywords."""
    concursos = (await db.execute(text("SELECT id, slug FROM concursos"))).all()
    for cid, cslug in concursos:
        blocos = (await db.execute(
            text("SELECT id, slug, keywords FROM blocos WHERE concurso_id = :cid ORDER BY ordem"),
            {"cid": cid},
        )).all()
        if not blocos:
            continue

        # Topics ainda sem bloco
        topics = (await db.execute(text("""
            SELECT t.id, t.descricao FROM topics t
            JOIN study_days d ON d.id = t.study_day_id
            JOIN weeks w ON w.id = d.week_id
            JOIN phases p ON p.id = w.phase_id
            WHERE p.concurso_id = :cid AND t.bloco_id IS NULL
        """), {"cid": cid})).all()
        for tid, desc in topics:
            bid = _match_bloco((desc or "").lower(), blocos)
            if bid:
                await db.execute(text("UPDATE topics SET bloco_id = :b WHERE id = :t"),
                                 {"b": bid, "t": tid})

        # Generated questions ainda sem bloco
        questions = (await db.execute(text("""
            SELECT q.id, q.enunciado, q.disciplina FROM generated_questions q
            JOIN study_materials m ON m.id = q.study_material_id
            JOIN study_days d ON d.id = m.study_day_id
            JOIN weeks w ON w.id = d.week_id
            JOIN phases p ON p.id = w.phase_id
            WHERE p.concurso_id = :cid AND q.bloco_id IS NULL
        """), {"cid": cid})).all()
        for qid, enu, disc in questions:
            text_blob = f"{disc or ''} {enu or ''}".lower()
            bid = _match_bloco(text_blob, blocos)
            if bid:
                await db.execute(text("UPDATE generated_questions SET bloco_id = :b WHERE id = :q"),
                                 {"b": bid, "q": qid})

        # MockExamResults sem bloco
        results = (await db.execute(text("""
            SELECT r.id, r.disciplina FROM mock_exam_results r
            JOIN mock_exams m ON m.id = r.mock_exam_id
            WHERE m.concurso_id = :cid AND r.bloco_id IS NULL
        """), {"cid": cid})).all()
        for rid, disc in results:
            bid = _match_bloco((disc or "").lower(), blocos)
            if bid:
                await db.execute(text("UPDATE mock_exam_results SET bloco_id = :b WHERE id = :r"),
                                 {"b": bid, "r": rid})


async def _seed_banca_examples_from_json(db: AsyncSession):
    """Carrega backend/app/fcc_examples.json para a tabela banca_examples."""
    json_path = Path(__file__).parent / "fcc_examples.json"
    if not json_path.exists():
        return
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return
    for q in data.get("questoes", []):
        if not q.get("enunciado") or not q.get("gabarito"):
            continue
        await db.execute(
            text("""
                INSERT INTO banca_examples
                    (banca, fonte, ano, disciplina, enunciado, alternativas, gabarito, comentario, ativo, criado_em)
                VALUES ('FCC', :fonte, :ano, :disciplina, :enunciado, :alternativas, :gabarito, NULL, 1, datetime('now'))
            """),
            {
                "fonte": q.get("prova", "FCC"),
                "ano": q.get("ano"),
                "disciplina": q.get("disciplina", ""),
                "enunciado": q.get("enunciado", ""),
                "alternativas": json.dumps(q.get("alternativas", {}), ensure_ascii=False),
                "gabarito": q.get("gabarito", "A"),
            },
        )
