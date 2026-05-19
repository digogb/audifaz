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
from .models import Base, User, StudyDay, StudyMaterial
from .seed import seed_if_needed
from .migrate import migrate
from .auth import hash_password
from .routers import days, topics, materials, errors, mocks, progress, audios, podcast
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
        day_result = await db.execute(select(StudyDay).where(StudyDay.data == today))
        day = day_result.scalar_one_or_none()
        if not day:
            return
        mat_result = await db.execute(select(StudyMaterial).where(StudyMaterial.study_day_id == day.id))
        if mat_result.scalar_one_or_none():
            return
        day_id = day.id

    logger.info(f"Cron: gerando material para {today} (day_id={day_id})")
    try:
        await generate_for_day(day_id)
        logger.info(f"Cron: material de {today} gerado com sucesso")
    except Exception as e:
        logger.error(f"Cron: erro ao gerar material de {today}: {e}")


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

    # Generate today's material at startup if past 05:00 and not yet generated
    now = datetime.now(TZ)
    if now.hour >= 5:
        await _generate_today_if_needed()

    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="AudiFaz", lifespan=lifespan)

app.include_router(auth_router.router)
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
