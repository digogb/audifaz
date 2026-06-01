"""Provisiona o concurso TJCE 2026 (F06) e vincula um usuário existente.

Idempotente e seguro:
  - Cria (ou reusa) o Concurso slug="tjce-2026" — NUNCA o SEFAZ.
  - Importa o plano markdown SOMENTE nesse concurso (import_plan apaga/recria
    apenas Phases/Weeks/Days/Topics do concurso_id passado).
  - Vincula um usuário já existente (default: busca "valdyr") via UserConcurso
    e define concurso_atual_id.
  - GUARDA DE SEGURANÇA: conta as Phases do SEFAZ antes e depois; se mudar,
    aborta com erro (rollback). O SEFAZ jamais é tocado.

Uso (dentro do container app):
    python scripts/provision_tjce.py /caminho/plano_estudos_tjce_f06.md [--user valdyr] [--dry-run]
"""

import argparse
import asyncio
import sys
from datetime import date

from sqlalchemy import select, func

from app.db import AsyncSessionLocal
from app.models import Concurso, Phase, User, UserConcurso
from app.services.plan_importer import import_plan
from app.migrate import (
    _seed_blocos_if_needed,
    _seed_redacao_temas_if_needed,
    _backfill_blocos,
)

SEFAZ_SLUG = "sefaz-ce-2026"
TJCE_SLUG = "tjce-2026"

TJCE_DEFAULTS = dict(
    slug=TJCE_SLUG,
    nome="TJCE 2026 — Analista Judiciário (TI Sistemas)",
    banca="FCC",
    orgao="TJCE",
    cargo="F06 — Analista Judiciário – Ciência da Computação – TI Sistemas",
    data_prova=date(2026, 8, 9),
    descricao=(
        "Concurso TJCE 2026, cargo F06 (Analista Judiciário – Apoio Especializado – "
        "Ciência da Computação – TI Sistemas). Banca FCC. Conteúdo conforme retificação "
        "do programa publicada no DJe nº 3786 (29/05/2026)."
    ),
    edital_url=None,
    theme_slug="lexlumina",
    brand="audifaz",
    requer_assinatura=False,
    ativo=True,
    publico=False,
)

PROMPT_EXTRA = (
    "Banca: FCC (Fundação Carlos Chagas). Cargo: F06 — Analista Judiciário, TI Sistemas, TJCE. "
    "Perfil do cargo após a retificação de 29/05/2026: Gestão de Produtos Digitais (Product "
    "Management/Ownership) com profundidade técnica. A FCC cobra definição literal e conceito "
    "aplicado a cenários, sem pegadinha psicológica; valoriza números exatos (ex.: 5 domínios do "
    "OWASP SAMM, 10 bases legais da LGPD, 3 Flight Levels, técnicas de priorização MoSCoW/RICE/WSJF). "
    "NÃO cobrar ITIL/COBIT/PMBOK/CMMI/MR-MPS como blocos centrais (saíram do edital). Focar em: "
    "gestão de produto, agilidade/Flight Levels, métricas de produto, DDD estratégico, OWASP SAMM, "
    "IA generativa/RAG/agentes e Resolução CNJ 615, engenharia de dados, RPA, Java/Spring, "
    "Lei 14.133/2021 e normativos do CNJ, LGPD."
)


async def get_or_create_concurso(db) -> tuple[Concurso, bool]:
    existing = (await db.execute(
        select(Concurso).where(Concurso.slug == TJCE_SLUG)
    )).scalar_one_or_none()
    if existing:
        # Atualiza metadados (mantém id e qualquer progresso vinculado)
        for k, v in TJCE_DEFAULTS.items():
            setattr(existing, k, v)
        existing.prompt_extra = PROMPT_EXTRA
        return existing, False
    c = Concurso(**TJCE_DEFAULTS, prompt_extra=PROMPT_EXTRA)
    db.add(c)
    await db.flush()
    return c, True


async def find_user(db, needle: str) -> User:
    pat = f"%{needle.lower()}%"
    rows = (await db.execute(
        select(User).where(
            func.lower(User.username).like(pat) | func.lower(User.email).like(pat)
        )
    )).scalars().all()
    if len(rows) == 0:
        print(f"ERRO: nenhum usuário casa com '{needle}'.", file=sys.stderr)
        allu = (await db.execute(select(User.id, User.username, User.email))).all()
        print("Usuários existentes:", file=sys.stderr)
        for u in allu:
            print(f"  id={u[0]} username={u[1]!r} email={u[2]!r}", file=sys.stderr)
        sys.exit(2)
    if len(rows) > 1:
        print(f"ERRO: '{needle}' é ambíguo, casou {len(rows)} usuários:", file=sys.stderr)
        for u in rows:
            print(f"  id={u.id} username={u.username!r} email={u.email!r}", file=sys.stderr)
        print("Rode novamente com --user mais específico (username ou email exato).", file=sys.stderr)
        sys.exit(2)
    return rows[0]


async def sefaz_phase_count(db) -> int:
    sefaz = (await db.execute(
        select(Concurso).where(Concurso.slug == SEFAZ_SLUG)
    )).scalar_one_or_none()
    if not sefaz:
        return -1  # SEFAZ não existe neste banco (ok)
    return (await db.execute(
        select(func.count(Phase.id)).where(Phase.concurso_id == sefaz.id)
    )).scalar_one()


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plano_md", help="caminho do plano_estudos_tjce_f06.md")
    ap.add_argument("--user", default="valdyr", help="username/email (substring) do aluno")
    ap.add_argument("--dry-run", action="store_true", help="parseia e valida sem persistir")
    ap.add_argument("--exclusive", action="store_true", default=True,
                    help="desativa os vínculos do usuário com outros concursos (default: True)")
    ap.add_argument("--no-exclusive", dest="exclusive", action="store_false",
                    help="mantém o usuário com acesso a todos os concursos atuais")
    args = ap.parse_args()

    content = open(args.plano_md, encoding="utf-8").read()

    async with AsyncSessionLocal() as db:
        sefaz_before = await sefaz_phase_count(db)
        print(f"[guard] SEFAZ phases antes: {sefaz_before}")

        concurso, created = await get_or_create_concurso(db)
        print(f"[tjce] concurso id={concurso.id} slug={concurso.slug} "
              f"({'criado' if created else 'reusado/atualizado'})")

        user = await find_user(db, args.user)
        print(f"[user] alvo: id={user.id} username={user.username!r} email={user.email!r}")

        if args.dry_run:
            from app.services.plan_importer import parse_plan
            plan = parse_plan(content, 2026)
            print(f"[dry-run] fases={len(plan.phases)} semanas={len(plan.weeks)} "
                  f"dias={plan.total_days} topicos={plan.total_topics}")
            await db.rollback()
            print("[dry-run] rollback feito, nada persistido.")
            return

        counts = await import_plan(db, concurso.id, content)
        print(f"[import] {counts}")

        # Blocos temáticos + temas de redação + classificação dos tópicos (idempotente).
        # Necessário porque o migrate() do startup roda antes do TJCE existir, e o
        # import_plan recria os tópicos (zerando bloco_id) a cada execução.
        await _seed_blocos_if_needed(db)
        await _seed_redacao_temas_if_needed(db)
        await _backfill_blocos(db)
        await db.commit()
        print("[seed] blocos/temas/backfill aplicados ao TJCE.")

        # Vincula usuário (idempotente) e define concurso atual
        link = (await db.execute(
            select(UserConcurso).where(
                UserConcurso.user_id == user.id,
                UserConcurso.concurso_id == concurso.id,
            )
        )).scalar_one_or_none()
        if not link:
            db.add(UserConcurso(user_id=user.id, concurso_id=concurso.id, ativo=True))
            print("[link] UserConcurso criado.")
        else:
            link.ativo = True
            print("[link] UserConcurso já existia (reativado).")

        if args.exclusive:
            # Desativa vínculos do usuário com OUTROS concursos (ex.: SEFAZ),
            # para que ele veja só o TJCE no seletor. Não remove dados/histórico.
            others = (await db.execute(
                select(UserConcurso).where(
                    UserConcurso.user_id == user.id,
                    UserConcurso.concurso_id != concurso.id,
                    UserConcurso.ativo == True,
                )
            )).scalars().all()
            for o in others:
                o.ativo = False
            if others:
                print(f"[link] {len(others)} vínculo(s) com outros concursos desativados (exclusivo TJCE).")

        user.concurso_atual_id = concurso.id
        await db.commit()
        print(f"[link] concurso_atual_id do usuário definido para {concurso.id}.")

        # GUARDA: SEFAZ inalterado
        sefaz_after = await sefaz_phase_count(db)
        print(f"[guard] SEFAZ phases depois: {sefaz_after}")
        if sefaz_before != sefaz_after:
            print("ERRO CRÍTICO: contagem de Phases do SEFAZ mudou! Investigar imediatamente.",
                  file=sys.stderr)
            sys.exit(3)
        print("[ok] SEFAZ intacto. TJCE provisionado e vinculado ao usuário.")


if __name__ == "__main__":
    asyncio.run(main())
