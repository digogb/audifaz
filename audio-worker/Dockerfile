FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV AUDIOS_DIR=/data/audios \
    DATABASE_URL=sqlite+aiosqlite:////data/audifaz.db \
    POLL_INTERVAL=30 \
    MAX_RETRIES=3 \
    CLAUDE_MODEL=claude-sonnet-4-6

CMD ["python", "worker.py"]
