# RUNBOOK — operação da VM

## Backup automatizado

- **Frequência:** todo dia às 03h00 (America/Fortaleza), via APScheduler no próprio container `app`.
- **Local:** `/data/backups/audifaz-YYYY-MM-DD.db` (volume `./data`, persistente).
- **Retenção:** 30 dias rolling (configurável via env `BACKUP_RETENTION_DAYS`).
- **Método:** API oficial do SQLite (`sqlite3 .backup`) — consistente, não bloqueia escritas.

Verificar último backup:
```bash
ls -lhrt data/backups/
```

## Restore

1. **Parar app + worker** para liberar o DB:
   ```bash
   docker compose stop app audio-worker
   ```
2. **Copiar o backup desejado** sobre o DB ativo (ajuste a data):
   ```bash
   docker run --rm -v ./data:/data alpine sh -c \
     "cp /data/backups/audifaz-2026-05-19.db /data/audifaz.db && \
      chown 0:0 /data/audifaz.db && \
      chmod 644 /data/audifaz.db"
   ```
3. **Subir novamente:**
   ```bash
   docker compose up -d
   ```
4. **Validar:**
   ```bash
   docker compose logs app | tail -20
   curl http://localhost:8000/api/brand
   ```

## Backup manual (antes de migrations destrutivas)

```bash
docker compose exec app python -c "from app.main import _backup_sqlite_sync; _backup_sqlite_sync()"
```

Ou, sem app rodando:
```bash
docker run --rm -v ./data:/data alpine sh -c \
  "apk add -q sqlite && cd /data && \
   sqlite3 audifaz.db \".backup backups/manual-$(date +%Y%m%d-%H%M%S).db\""
```

## Backup da VM inteira

Backup do volume Docker (`./data`) faz sentido para tirar snapshot completo, mas para restore granular o `.db` já é suficiente.

Pra snapshot OCI: usar Block Volume Backup (manual ou policy diária).

## Rotinas de operação

| Tarefa | Frequência | Onde |
|---|---|---|
| Backup SQLite | diário 03h | container `app` |
| Geração de material do dia | diário 05h | container `app` |
| Limpar áudios `.tmp_*` | a cada restart | `audio-worker` |
| Verificar tamanho de `./data` | mensal | `du -sh data/` |

## Logs

```bash
docker compose logs -f app                    # tudo
docker compose logs --tail=200 app            # recente
docker compose logs app | grep "backup ok"    # backups
docker compose logs app | grep "mp/webhook"   # Mercado Pago
```

## Reset de senha de usuário (suporte)

```bash
docker compose exec app python -c "
from app.db import AsyncSessionLocal
from app.models import User
from app.auth import hash_password
from sqlalchemy import select
import asyncio
async def main():
    async with AsyncSessionLocal() as db:
        u = (await db.execute(select(User).where(User.email == 'foo@bar.com'))).scalar_one()
        u.password_hash = hash_password('nova-senha-temp-123')
        await db.commit()
asyncio.run(main())
"
```

Avisar o usuário e instruir troca via UI.
