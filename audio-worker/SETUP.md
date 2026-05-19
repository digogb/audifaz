# audio-worker — setup

Container que gera podcasts didáticos PT-BR (estilo NotebookLM) a partir do `conteudo_md`
de cada `StudyMaterial`. Pipeline:

1. **Claude** (mesma chave do backend) gera transcript Ana/Lucas estruturado
2. **Google Cloud TTS Chirp 3 HD** sintetiza cada turno em mp3
3. **ffmpeg** concatena tudo em `/data/audios/{audio_id}.mp3`

Sem Open Notebook, sem SurrealDB, sem login Google.

## Pré-requisitos

- Conta Google (qualquer Gmail serve)
- Docker Compose já configurado
- `ANTHROPIC_API_KEY` já no `.env` (mesma do backend)

## Setup (1 vez, ~5min)

### 1. Habilitar Google Cloud TTS

No projeto GCP que você usa (ou crie um novo em https://console.cloud.google.com/projectcreate):

1. **Habilitar billing** se ainda não estiver: https://console.cloud.google.com/billing
   (dentro do free tier de 1M chars/mês não há cobrança — configure um alerta de
   budget em R$ 0,10 pra ser avisado se ultrapassar)
2. **Habilitar a API**: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com
   → selecione o projeto → "Enable"
3. **Criar API key**: https://console.cloud.google.com/apis/credentials
   → "Create credentials" → "API key" → copiar a chave (`AIza...`)
4. **Restringir a chave** (segurança): no editor da key, em "API restrictions"
   marque "Restrict key" → selecione apenas "Cloud Text-to-Speech API" → Save

### 2. Preencher `.env`

```
ANTHROPIC_API_KEY=sk-ant-...
GCP_TTS_API_KEY=AIzaSy...
PUBLIC_BASE_URL=https://audifaz.seudominio.com

# opcionais (defaults usam Kore + Charon — vozes Chirp 3 HD em PT-BR)
# CLAUDE_MODEL=claude-sonnet-4-6
# VOICE_ANA=pt-BR-Chirp3-HD-Kore
# VOICE_LUCAS=pt-BR-Chirp3-HD-Charon
```

### 3. Subir o worker

```bash
docker compose up -d audio-worker
docker compose logs -f audio-worker
```

O worker polla `material_audios` no SQLite a cada 30s. Quando vê `status='pendente'`:

1. Pede pro Claude gerar um transcript estruturado (~12-40 turnos conforme tamanho do material)
2. Sintetiza cada turno via GCP TTS Chirp HD (Ana=Kore, Lucas=Charon)
3. Concatena com ffmpeg em `./data/audios/{audio_id}.mp3`
4. Atualiza `status='done'` com `duracao_seg` e `tamanho_bytes`

## Trocar vozes

GCP TTS tem 30 vozes Chirp 3 HD em PT-BR. Listar disponíveis:

```bash
curl -s "https://texttospeech.googleapis.com/v1/voices?languageCode=pt-BR&key=$GCP_TTS_API_KEY" | jq '.voices[] | select(.name | startswith("pt-BR-Chirp3")) | "\(.name) \(.ssmlGender)"'
```

Bem ranqueadas (subjetivo):
- `pt-BR-Chirp3-HD-Kore` (F, didática) ← default Ana
- `pt-BR-Chirp3-HD-Charon` (M, informativo) ← default Lucas
- `pt-BR-Chirp3-HD-Puck` (M, animado)
- `pt-BR-Chirp3-HD-Aoede` (F, suave)
- `pt-BR-Chirp3-HD-Fenrir` (M, firme)

Atualize `VOICE_ANA` e `VOICE_LUCAS` no `.env` e reinicie o worker. Sem rebuild.

## Custo

Para 1 podcast/dia (~30/mês):

- **Claude Sonnet 4.6** (transcript): ~$0,04/podcast = ~$1,20/mês
- **GCP TTS Chirp 3 HD**: ~3.000 chars/podcast × 30 = 90k chars/mês
  → **dentro do free tier de 1M chars/mês** = $0,00

Se passar do free tier (acima de ~330 podcasts/mês): $30 por milhão de chars.

## Smoke test (preview vocal)

Pra testar a qualidade vocal sem rodar o worker inteiro:

```bash
GCP_TTS_API_KEY=... python audio-worker/scripts/test_gcp_studio_tts.py
# resultado em /tmp/gcp_studio_preview/preview.mp3
```

## Quando der pau

| Sintoma | Causa provável | Fix |
|---|---|---|
| `TranscriptError: ANTHROPIC_API_KEY não configurado` | env var faltando | Preencher `.env` |
| `TTSError: HTTP 400 ... INVALID_ARGUMENT` | Voice name inválida | Listar voices (comando acima) e atualizar `VOICE_*` |
| `TTSError: HTTP 403 ... PERMISSION_DENIED` | Cloud TTS API desabilitada ou key restrita demais | Passos 1.2 e 1.4 acima |
| `TTSError: HTTP 429` | Quota exaurida | Worker faz retry automático com backoff. Se persistir, ver Cloud Console → Quotas |
| `ffmpeg falhou` | mp3 part corrompido (TTS retornou inválido) | Ver log anterior do turn que falhou; provavelmente quota/voice issue |
| Worker pegou pendente mas nunca termina | Claude travou (raro) | SDK tem timeout default; vira erro após ~10min e retry |
| Status virou `erro` após 3 tentativas | Falha persistente | Admin pode resetar via `POST /api/audios/{id}/trigger` |

## Limpar áudios antigos

```bash
find ./data/audios -name '*.mp3' -mtime +90 -delete
```
