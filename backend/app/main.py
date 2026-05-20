import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from .db import engine, AsyncSessionLocal
from .models import Base, User, StudyDay, StudyMaterial, Week, Phase, Concurso
from .seed import seed_if_needed
from .migrate import migrate
from .auth import hash_password
from .routers import days, topics, materials, errors, mocks, progress, audios, podcast, concursos, blocos, redacoes, billing
from .routers import auth as auth_router
from .routers.materials import generate_for_day

logger = logging.getLogger(__name__)
TZ = ZoneInfo("America/Fortaleza")


async def _seed_admin():
    username = os.environ.get("ADMIN_USERNAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "").strip()
    if not username or not password:
        return
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        if not result.scalar_one_or_none():
            db.add(User(username=username, password_hash=hash_password(password)))
            await db.commit()


async def _generate_today_if_needed():
    today = datetime.now(TZ).date()
    async with AsyncSessionLocal() as db:
        # Encontra um StudyDay de hoje por concurso ativo que ainda não tem material
        stmt = (
            select(StudyDay.id, Concurso.slug)
            .join(Week, StudyDay.week_id == Week.id)
            .join(Phase, Week.phase_id == Phase.id)
            .join(Concurso, Phase.concurso_id == Concurso.id)
            .outerjoin(StudyMaterial, StudyMaterial.study_day_id == StudyDay.id)
            .where(StudyDay.data == today, Concurso.ativo == True, StudyMaterial.id.is_(None))
        )
        pending = (await db.execute(stmt)).all()

    if not pending:
        return

    for day_id, concurso_slug in pending:
        logger.info(f"Cron: gerando material {concurso_slug} {today} (day_id={day_id})")
        try:
            await generate_for_day(day_id)
            logger.info(f"Cron: material {concurso_slug} {today} gerado com sucesso")
        except Exception as e:
            logger.error(f"Cron: erro material {concurso_slug} {today} (day_id={day_id}): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await migrate(db)
    async with AsyncSessionLocal() as db:
        await seed_if_needed(db)
    await _seed_admin()

    # Start cron scheduler
    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(_generate_today_if_needed, "cron", hour=5, minute=0)
    scheduler.start()

    # Generate today's material at startup if past 05:00 and not yet generated.
    # Skip via env var (útil em dev/testes onde a chamada Claude trava startup).
    if os.environ.get("SKIP_STARTUP_GEN", "").lower() not in ("1", "true", "yes"):
        now = datetime.now(TZ)
        if now.hour >= 5:
            await _generate_today_if_needed()

    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="AudiFaz", lifespan=lifespan)

app.include_router(auth_router.router)
app.include_router(concursos.router)
app.include_router(blocos.router)
app.include_router(redacoes.router)
app.include_router(billing.router)
app.include_router(days.router)
app.include_router(topics.router)
app.include_router(materials.router)
app.include_router(errors.router)
app.include_router(mocks.router)
app.include_router(progress.router)
app.include_router(audios.router)
app.include_router(podcast.router)

# Serve React build in production
static_dir = Path("/app/static")
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index = static_dir / "index.html"
        return FileResponse(index)
