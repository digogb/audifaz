# Plano de Implementação — AudiFaz Multi-Usuário

## Contexto

Transformar o AudiFaz de single-user em multi-usuário compartilhado:
- Conteúdo do dia gerado automaticamente via cron (1x/dia, compartilhado)
- Progresso individual por usuário (tentativas, erros, simulados)
- Autenticação simples (username + senha, JWT)
- Navegação entre dias da semana
- Geração sem streaming (resposta completa de uma vez)
- Questões aparecendo corretamente

---

## Fase 1 — Autenticação [ ]

**Backend:**
- Adicionar dependências: `python-jose[cryptography]`, `passlib[bcrypt]`, `apscheduler`
- Novo model `User` (id, username, password_hash, created_at)
- Novo `backend/app/auth.py` — JWT (create_token, verify_password, hash_password, get_current_user dependency)
- Novo `backend/app/routers/auth.py` — `POST /api/auth/login`, `POST /api/auth/register`
- Adicionar auth a todos os routers existentes (Depends(get_current_user))
- Seed: criar usuário padrão na inicialização se `ADMIN_USERNAME`/`ADMIN_PASSWORD` env vars estiverem definidas
- Schemas: `LoginRequest`, `TokenOut`

**Frontend:**
- Novo `frontend/src/contexts/AuthContext.jsx` — token em localStorage, login/logout
- Novo `frontend/src/pages/Login.jsx` — formulário username + senha
- `App.jsx` — rotas protegidas, redireciona para /login se não autenticado
- `api.js` — interceptor axios para adicionar `Authorization: Bearer <token>`, redirect para /login em 401
- `Layout.jsx` — exibir username + botão logout no header

**Critério de aceite:** Login funciona, todas as rotas retornam 401 sem token.

---

## Fase 2 — Progresso Individual por Usuário [ ]

**Pré-requisito:** Fase 1 concluída.

**Backend (modelos e routers):**
- `models.py`:
  - `QuestionAttempt`: remover `unique=True` de `question_id`, adicionar `user_id` FK → `users.id`, adicionar `UniqueConstraint("question_id", "user_id")`
  - `ErrorEntry`: adicionar `user_id` FK → `users.id` (nullable)
  - `MockExam`: adicionar `user_id` FK → `users.id` (nullable)
  - Remover relacionamentos ORM `GeneratedQuestion.attempt` e `QuestionAttempt.question` (simplifica multi-user)
- `routers/materials.py` — `get_material`: carregar tentativas filtradas por `user_id`; `record_attempt`: salvar com `user_id`
- `routers/errors.py` — todos os endpoints filtram por `current_user.id`; `create_error` e criação automática usam `user_id`
- `routers/mocks.py` — filtrar por `current_user.id`
- `routers/progress.py` — mock series filtrado por `current_user.id`

**Critério de aceite:** Usuário A responde questão, Usuário B vê a mesma questão sem tentativa.

---

## Fase 3 — Geração sem Streaming + Cron Diário [ ]

**Pré-requisito:** Fase 2 concluída.

**Backend:**
- `claude_client.py`: adicionar `generate_material(topics, model)` — função não-streaming que acumula internamente o stream e retorna `(content_md, questions_data, usage_data)`
- `routers/materials.py`:
  - Endpoint `POST /{day_id}/material/generate`: remover `StreamingResponse`, retornar JSON (`StudyMaterialOut`) após geração completa
  - Manter lógica de deletar material existente antes de gerar novo
- `main.py`:
  - Adicionar `APScheduler` no lifespan
  - Job cron: todo dia às 05:00 Fortaleza → chama `generate_daily_material()` se não existir material para hoje
  - Ao startup: se hoje não tem material e já passou das 05:00, gerar imediatamente

**Frontend:**
- `Today.jsx`:
  - Remover `streamMaterial` / lógica SSE
  - Chamar `api.generateMaterial(dayId, model)` (POST normal, timeout 5min)
  - Loading spinner enquanto aguarda
  - Exibir conteúdo + questões de uma vez ao receber resposta
- `api.js`: substituir `streamMaterial` por `generateMaterial` (axios POST)

**Critério de aceite:** Clicar "Gerar Material" mostra spinner, depois exibe tudo. Às 05:00 o conteúdo já está pronto.

---

## Fase 4 — Navegação entre Dias [ ]

**Pré-requisito:** Fase 3 concluída.

**Backend:**
- `routers/days.py`: adicionar `GET /api/days/by-date/{date_str}` — retorna o `StudyDay` de qualquer data (passado ou futuro), 404 se não existe

**Frontend:**
- `api.js`: adicionar `getDayByDate(dateStr)`
- `Today.jsx`:
  - Usar `useSearchParams` para ler `?data=YYYY-MM-DD`
  - Se sem param → `getToday()`; se com param → `getDayByDate(date)`
  - Botões `←` Dia anterior / Dia seguinte `→` no header da página
  - Mini-calendário da semana: dias clicáveis (navegar para o dia clicado)
  - Atualizar URL ao navegar (não recarrega a página)
  - Indicador visual: "hoje" vs "data navegada"

**Critério de aceite:** Navegar para ontem mostra o conteúdo gerado; clicar nos dias do mini-calendário navega corretamente.

---

## Modelo de dados final

```
User (id, username, password_hash, created_at)

QuestionAttempt (id, question_id→Question, user_id→User,
                 alternativa_escolhida, acertou, respondido_em, observacao)
  UNIQUE(question_id, user_id)

ErrorEntry (id, ..., user_id→User)

MockExam (id, ..., user_id→User)
```

Compartilhado entre todos os usuários:
- StudyDay, Topic, StudyMaterial, GeneratedQuestion (plano + conteúdo do dia)

Individual por usuário:
- QuestionAttempt, ErrorEntry, MockExam, MockExamResult

---

## Stack / Decisões Técnicas

- JWT com `python-jose`, senhas com `passlib[bcrypt]`
- Token armazenado em `localStorage`, expiração 30 dias
- Cron com `APScheduler` (AsyncIOScheduler, sem Celery/Redis)
- Geração cron usa `claude-sonnet-4-6` (custo-benefício)
- Navegação por URL query param `?data=YYYY-MM-DD`
- Sem mudanças em topic completion e notas (permanecem compartilhados)

---

## docker-compose.yml

Adicionar env vars:
```yaml
environment:
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  - SECRET_KEY=${SECRET_KEY}
  - ADMIN_USERNAME=${ADMIN_USERNAME:-}
  - ADMIN_PASSWORD=${ADMIN_PASSWORD:-}
  - TZ=America/Fortaleza
```
