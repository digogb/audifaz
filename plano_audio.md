# Plano de Implementação — Áudios Estilo NotebookLM

## Contexto

Gerar 1 áudio podcast (estilo NotebookLM, 2 locutores em PT-BR discutindo) por dia de estudo, a partir do `conteudo_md` do `StudyMaterial`. Áudio é compartilhado entre todos os usuários (igual ao material) e disparado automaticamente após o material ser gerado pelo cron.

**Decisão de arquitetura:** rodar o [`lfnovo/open-notebook`](https://github.com/lfnovo/open-notebook) (clone open-source do NotebookLM com API REST completa) self-hosted, usando **Gemini 2.5 Flash TTS** (preview, free tier da Google AI Studio API) como motor de áudio. É literalmente o mesmo TTS que o NotebookLM usa por baixo, mas via API oficial — sem Playwright, sem login Google manual, sem cookies expirando.

**Custo recorrente:** zero — Gemini 2.5 Flash TTS é gratuito no free tier da AI Studio (1500 RPD, 1 podcast/dia usa 1).

---

## Como o usuário ouve

**Decisão:** **feed RSS de podcast** + botão de download mp3. Sem player web.

Fluxo: usuário assina o feed 1x no Pocket Casts / Apple Podcasts / Overcast / Castro → todo dia 06h o episódio novo cai no app sozinho, com download offline, controles em lockscreen, CarPlay/Android Auto, etc.

Auth do feed: cada `User` ganha um `podcast_token` (hex aleatório). URL: `/api/podcast/{token}/feed.xml`. Revogar = regenerar token na tela `/config`.

---

## Modelo de Dados

**`User`** — adicionar campo:
```python
podcast_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
```

**Novo `MaterialAudio`:**
```python
class MaterialAudio(Base):
    __tablename__ = "material_audios"
    id: Mapped[int] = mapped_column(primary_key=True)
    study_material_id: Mapped[int] = mapped_column(ForeignKey("study_materials.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="pendente")  # pendente|gerando|done|erro
    arquivo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duracao_seg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tamanho_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notebooklm_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # guarda episode_id do open-notebook
    instrucoes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    gerado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    concluido_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_msg: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tentativas: Mapped[int] = mapped_column(Integer, default=0)
    material: Mapped["StudyMaterial"] = relationship()
```

> Mantemos o nome `notebooklm_id` por compatibilidade com o que já está em produção — agora guarda o `episode_id` retornado pelo open-notebook.

**Schema Pydantic:** `MaterialAudioOut` + `PodcastTokenOut` (já implementados em `backend/app/schemas.py`).

---

## Arquitetura — Comunicação backend ↔ audio-worker ↔ open-notebook

```
[backend] gera material → cria MaterialAudio(status='pendente')
                                   ↓
[audio-worker] poll a cada 30s no SQLite → pega pendente → status='gerando'
                                   ↓
              chama open-notebook via HTTP:
                POST /sources/json          → cria source com conteudo_md
                POST /podcasts/generate     → dispara job (episode_profile="audifaz")
                GET  /podcasts/jobs/{id}    → poll status do job
                GET  /podcasts/episodes/{id}/audio  → baixa mp3
                DELETE /podcasts/episodes/{id}      → limpa episódio
                                   ↓
              salva em /data/audios/{audio_id}.mp3
                                   ↓
              status='done', arquivo_path=..., tamanho_bytes=..., duracao_seg=...
                                   ↓
[backend] serve via GET /api/podcast/{token}/audio/{audio_id}.mp3
[backend] expõe feed via GET /api/podcast/{token}/feed.xml
```

`audio-worker` e `backend` compartilham o mesmo SQLite + volume `audios/`. `open-notebook` é um serviço HTTP isolado que só fala com o `audio-worker` na rede do Compose. `surrealdb` é dependência interna do open-notebook (não usado por mais ninguém).

---

## Fase 1 — Services no Compose + Setup manual 1x [ ]

### Adicionar no `docker-compose.yml`:

```yaml
surrealdb:
  image: surrealdb/surrealdb:v2
  command:
    - start
    - --log=info
    - --user=root
    - --pass=${SURREAL_PASSWORD:-rootroot}
    - rocksdb:/data/surreal.db
  volumes:
    - ./data/surreal:/data
  restart: unless-stopped

open-notebook:
  image: lfnovo/open_notebook:v1-latest
  depends_on:
    - surrealdb
  environment:
    - OPEN_NOTEBOOK_ENCRYPTION_KEY=${OPEN_NOTEBOOK_ENCRYPTION_KEY}
    - SURREAL_URL=ws://surrealdb:8000/rpc
    - SURREAL_USER=root
    - SURREAL_PASSWORD=${SURREAL_PASSWORD:-rootroot}
    - SURREAL_NAMESPACE=open_notebook
    - SURREAL_DATABASE=production
  ports:
    - "8502:8502"  # UI (acesso só local pra setup)
    # 5055 fica interno na rede do compose
  volumes:
    - ./data/open-notebook:/app/data
  restart: unless-stopped

audio-worker:
  build:
    context: ./audio-worker
  depends_on:
    - app
    - open-notebook
  volumes:
    - ./data:/data
  environment:
    - DATABASE_URL=sqlite+aiosqlite:////data/audifaz.db
    - AUDIOS_DIR=/data/audios
    - OPENNOTEBOOK_URL=http://open-notebook:5055
    - OPENNOTEBOOK_NOTEBOOK_ID=${OPENNOTEBOOK_NOTEBOOK_ID}
    - OPENNOTEBOOK_EPISODE_PROFILE=audifaz
    - POLL_INTERVAL=30
    - MAX_RETRIES=3
    - TZ=America/Fortaleza
  restart: unless-stopped
```

### `.env` novo:
```
OPEN_NOTEBOOK_ENCRYPTION_KEY=<gerar 32 bytes b64: openssl rand -base64 32>
SURREAL_PASSWORD=<gerar senha forte>
OPENNOTEBOOK_NOTEBOOK_ID=<preencher depois do setup manual>
GEMINI_API_KEY=<criar em aistudio.google.com>
PUBLIC_BASE_URL=https://audifaz.seudominio.com
```

### Setup manual (1x, na UI do open-notebook em http://localhost:8502):

1. Subir o stack: `docker compose up -d surrealdb open-notebook`
2. Aguardar ~30s e abrir `http://localhost:8502`
3. **Settings → API Keys → Add Credential** → provider=Google → colar `GEMINI_API_KEY`
4. **Speaker Profiles → New** "ana-lucas-ptbr":
   - Speaker 1: `Ana` · provider=`google` · model=`gemini-2.5-flash-preview-tts` · voice=`Kore`
   - Speaker 2: `Lucas` · provider=`google` · model=`gemini-2.5-flash-preview-tts` · voice=`Puck`
5. **Episode Profiles → New** "audifaz":
   - `language: pt-BR`
   - `speaker_config: ana-lucas-ptbr`
   - `outline_llm: claude-sonnet-4-6`
   - `transcript_llm: claude-sonnet-4-6`
   - `num_segments: 8` (worker vai sobrescrever dinamicamente)
   - `default_briefing`:
     ```
     Não resuma. O conteúdo da fonte JÁ É um resumo — sua tarefa é expandi-lo
     em diálogo didático entre Ana e Lucas, percorrendo TODOS os tópicos na
     ordem em que aparecem, sem omitir nenhum subitem. Cada conceito da fonte
     deve virar pelo menos uma troca de fala.

     O conteúdo do dia pode ser de qualquer área coberta pelo concurso de
     Auditor Fiscal de TI da SEFAZ-CE 2026 (banca FCC):
     - TI: frameworks (COBIT, ITIL, ISO 27001/27002/27005), engenharia de
       software (GoF, microsserviços, DevOps, DevSecOps), dados (NoSQL,
       ETL/ELT, Kafka, Data Lake/Warehouse/Mesh), cloud (AWS/Azure/GCP,
       Kubernetes), segurança (criptografia, PKI, OAuth/OIDC, OWASP),
       infraestrutura (redes, virtualização, storage), IA/ML/MLOps
     - Direito Tributário (CTN, LC 87/123/116, Reforma Tributária IBS/CBS),
       Constitucional, Administrativo (Lei 14.133, 8.429, 12.527), Civil,
       Penal, Financeiro (LRF, Lei 4.320), LGPD
     - Contabilidade Geral e Pública (MCASP, NBC TSP, NBC TA), Auditoria
     - Economia (micro/macro), Matemática Financeira, Estatística,
       Análise Combinatória, Raciocínio Lógico
     - Língua Portuguesa, Redação Oficial
     - Legislação Estadual CE (ICMS, ITCD, IPVA, FECOP)

     Adapte o tom ao tópico: técnico quando for TI, normativo quando for
     direito/contabilidade, prático quando for matemática/português.

     Destaque pegadinhas típicas da banca FCC quando identificar uma na fonte:
     - Troca de versões de framework (COBIT 5 vs 2019, ITIL v3 vs v4)
     - Datas/números de leis trocados, alíquotas, prazos, exceções
     - Palavras absolutas ("sempre", "nunca") versus relativas ("pode", "deve")
     - Conceitos parecidos confundidos (OAuth vs OIDC, RPO vs RTO,
       DW vs Data Lake, ICMS vs ISS, etc)
     - Listas com pegadinha (modalidades de extinção do crédito tributário,
       controles ISO 27002, princípios LIMPE, etc)

     Português brasileiro conversacional. Sem introdução longa, sem
     despedida longa — vá direto ao conteúdo. Sem limite de duração:
     cobrir todos os tópicos é mais importante que ser conciso.
     ```
6. **Notebooks → New** "AudiFaz" → copiar o `id` retornado (formato `notebook:xxx`) → colocar em `.env` como `OPENNOTEBOOK_NOTEBOOK_ID`
7. `docker compose up -d audio-worker`

Documentar no `audio-worker/SETUP.md`.

---

## Fase 2 — audio-worker como cliente HTTP do open-notebook [ ]

**Estrutura:**
```
audio-worker/
├── Dockerfile               # python:3.12-slim puro
├── requirements.txt         # httpx, sqlalchemy[asyncio], aiosqlite
├── db.py                    # modelos espelhados (MaterialAudio, StudyMaterial)
├── open_notebook_client.py  # cliente HTTP
├── worker.py                # loop de polling
└── SETUP.md
```

### `audio-worker/Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "worker.py"]
```

Sem Playwright, sem Chromium, sem ffmpeg. Imagem fica ~150MB (vs ~1.5GB antes).

### `audio-worker/requirements.txt`:
```
httpx>=0.27
sqlalchemy[asyncio]>=2.0
aiosqlite>=0.20
```

### `audio-worker/open_notebook_client.py`:

Wrapper async sobre a API. Fluxo de `generate_podcast(content_md, num_segments)`:

1. `POST /sources/json` — cria source com `notebook_id`, `content`, `async_processing=True`
2. Poll do source até status `ready` (timeout 120s)
3. `POST /podcasts/generate` — `{notebook_id, source_ids, episode_profile, num_segments}` → `job_id`
4. `GET /podcasts/jobs/{job_id}` — poll a cada 5s até `status=completed` (timeout 1200s = 20min)
5. Do payload do job extrair `episode_id`
6. `GET /podcasts/episodes/{episode_id}/audio` — stream mp3 pra arquivo no `AUDIOS_DIR`
7. Computar `tamanho_bytes` (stat) e `duracao_seg` (header `Content-Duration` se existir, senão `None`)
8. (Opcional) `DELETE /podcasts/episodes/{episode_id}` — limpa episódio do open-notebook pra não acumular
9. Retornar `(path, duracao_seg, tamanho_bytes, episode_id)`

Erros do open-notebook (5xx, 4xx) viram `RuntimeError` que o worker captura e marca como `erro`/retry.

### `audio-worker/worker.py`:

Loop atual já está OK. Mudanças:
- Trocar `from notebooklm_runner import generate_podcast` por `from open_notebook_client import generate_podcast`
- Calcular `num_segments` dinâmico antes de chamar:
  ```python
  num_segments = max(8, len(content_md) // 1500)
  ```
- Passar `num_segments` para `generate_podcast`

**Critério de aceite:** worker pega pendente do banco → chama open-notebook → mp3 cai em `/data/audios/{audio_id}.mp3` → status='done'.

---

## Fase 3 — Backend e Frontend (já implementados) [✓]

### Backend (sem alteração):
- `models.py`: `User.podcast_token` + `MaterialAudio` ✓
- `migrate.py`: migrations idempotentes ✓
- `schemas.py`: `MaterialAudioOut` + `PodcastTokenOut` ✓
- `routers/audios.py`: GET status, POST generate (admin), POST regenerate-token, GET podcast/me ✓
- `routers/podcast.py`: RSS feed 2.0 + iTunes namespace, streaming mp3 com Range ✓
- `routers/materials.py`: `_enqueue_audio` chamado em `_run_generation_bg` e `generate_for_day` ✓
- `main.py`: routers registrados ✓

### Frontend (sem alteração):
- `App.jsx` + `Layout.jsx`: rota `/config` + menu ✓
- `api.js`: `getAudio`, `generateAudio`, `getPodcastFeed`, `regeneratePodcastToken` ✓
- `pages/Today.jsx`: `<AudioStatus />` embutido ✓
- `components/AudioStatus.jsx`: estados pendente/gerando/done/erro, polling 15s, botão download + regenerar ✓
- `pages/Config.jsx`: card de podcast com URL copiável e regenerar token ✓

---

## Fase 4 — Polimento [ ]

- **Reset de `tentativas` no admin retry** (`routers/audios.py:trigger_audio`) — quando admin reseta áudio em `erro`, zerar `tentativas` também (hoje fica em `>= MAX_RETRIES` e worker ignora)
- **Auto-gerar `podcast_token` no primeiro `get_audio`** — hoje download fica `null` até user abrir `/config` e gerar token manualmente
- Listar todos os áudios em `/config` (admin) com botão "regenerar" por item
- Adicionar `<itunes:image>` (capa fixa do podcast) no RSS — apps mostram thumbnail
- Adicionar `<itunes:summary>` por episódio com primeiros 200 chars do `conteudo_md`
- Validar feed em https://podba.se/validate
- Cron semanal apagando mp3s com mais de 90 dias (opcional)

---

## Pontos de atenção / riscos operacionais

| Risco | Mitigação |
|---|---|
| Open Notebook quebra após update | Pinamos `lfnovo/open_notebook:v1-latest` (ou tag estável). Stack isolada — falha do podcast não derruba app principal. |
| Gemini muda preview do TTS | Modelo é `gemini-2.5-flash-preview-tts` — quando sair de preview, atualizar nome no Speaker Profile via UI. Sem mudança de código. |
| Free tier do Gemini estourar | 1500 RPD, 1 podcast usa 1 request → folga absurda. Se virar problema, fallback pra Google Cloud TTS (~$0 free tier) ou Coqui local. |
| Job de podcast trava no open-notebook | Worker tem timeout de 20min no poll. Vira `erro`, conta em `tentativas`, retry automático até `MAX_RETRIES=3`. |
| Source não fica `ready` no open-notebook | Timeout de 120s no `add_source`. Vira `RuntimeError` no worker → `erro`. |
| Conflito SQLite multi-writer (backend + worker) | SQLite com `journal_mode=WAL` (confirmar). Worker escreve pouco e nunca na mesma row que o backend. |
| Acúmulo de episódios no open-notebook | Worker chama `DELETE /podcasts/episodes/{id}` após download. mp3 nosso fica no nosso volume. |
| Limite de chars do TTS por chunk | Open-notebook chunkea internamente. Sem código nosso pra isso. |

---

## Stack / Decisões Técnicas (final)

- **Motor de áudio:** [`lfnovo/open-notebook`](https://github.com/lfnovo/open-notebook) self-hosted, API REST em `:5055`
- **TTS:** Gemini 2.5 Flash TTS preview (Google AI Studio API, free tier, multi-speaker conversational nativo PT-BR)
- **LLM (outline + transcript):** Claude Sonnet 4.6 (mesma chave já usada pra gerar material) — definido no Episode Profile via UI do open-notebook
- **Comunicação backend ↔ worker:** DB polling no SQLite (sem Redis) — worker checa a cada 30s
- **Comunicação worker ↔ open-notebook:** HTTP via `httpx.AsyncClient` na rede interna do Compose
- **Áudio compartilhado** — 1 mp3 por `StudyMaterial`, sem `user_id`
- **Auto-trigger** — criado junto com material; worker processa em background
- **Storage:** volume `./data/audios` montado em backend (leitura) e worker (escrita)
- **Distribuição:** feed RSS 2.0 + iTunes namespace servido pelo backend, autenticado por `podcast_token` por usuário na URL. Sem player web.
- **Streaming:** `FileResponse` do FastAPI com `Accept-Ranges: bytes` (apps de podcast usam Range pra download em chunks)
- **2 locutores PT-BR:** Ana (`Kore`) + Lucas (`Puck`) — vozes nativas do Gemini TTS
- **Duração:** sem limite — proporcional ao tamanho do material via `num_segments = max(8, chars // 1500)` + briefing rígido "não resuma"
- **Limite de tentativas:** 3 (campo `tentativas`); após isso, status `erro` permanente até admin resetar
