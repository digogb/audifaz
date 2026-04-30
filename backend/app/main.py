from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from .db import engine, AsyncSessionLocal
from .models import Base
from .seed import seed_if_needed
from .routers import days, topics, materials, errors, mocks, progress


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await seed_if_needed(db)
    yield


app = FastAPI(title="audifaz", lifespan=lifespan)

app.include_router(days.router)
app.include_router(topics.router)
app.include_router(materials.router)
app.include_router(errors.router)
app.include_router(mocks.router)
app.include_router(progress.router)

# Serve React build in production
static_dir = Path("/app/static")
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index = static_dir / "index.html"
        return FileResponse(index)
