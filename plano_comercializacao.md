# Plano de Implementação — Comercialização AudiFaz (Multi-Concurso)

> **Contexto:** o AudiFaz já roda em produção (OCI ARM, Caddy, FastAPI+SQLite, audio-worker, cron 5h). Auth, progresso individual, simulados, caderneta de erros, áudios e podcast já existem. Falta transformar o sistema **single-concurso (SEFAZ-CE chumbado em `plano.md`)** em **multi-concurso comercializável (SEFAZ-CE + TJCE + N futuros)**.
>
> **Premissa-chave:** não reescrever. Estender o que já existe. Migração in-place na mesma VM. O concurso pessoal continua funcionando o tempo todo.

---

## 0. Visão arquitetural do estado-alvo

```
User ──(n:n)── Concurso ──┬── Phase ── Week ── StudyDay ── Topic ── Bloco
                          ├── BancaExample (questões de referência por banca)
                          ├── ChecklistAdmin (inscrição, pagamento, cartão)
                          └── Recurso (livros, cursos, links)

User ── Subscription (Stripe ou Pix) ── ativa acesso a 1+ Concursos
     ── UserTopicProgress / UserDayProgress / QuestionAttempt / ErrorEntry / MockExam / Redacao
        (todos já existem hoje, só precisam ser scoped por concurso)
```

A unidade comercial é **assinatura por concurso** (não por usuário global). Um usuário pode assinar SEFAZ-CE e TJCE simultaneamente.

---

## Fase 1 — Concurso como entidade de primeira classe `[2 dias]`

**Objetivo:** todo conteúdo (Phase, Week, StudyDay, Topic) passa a ser scoped por `Concurso`. O SEFAZ-CE atual vira o primeiro registro, sem perda de dados.

**Backend:**
- `models.py`:
  - Novo `Concurso(id, slug, nome, banca, orgao, cargo, data_prova, ativo, descricao, edital_url, criado_em)`
  - Adicionar `concurso_id` FK em `Phase` (cascata: Week/StudyDay/Topic herdam pelo parent)
  - Nova tabela `user_concurso` (n:n) com `(user_id, concurso_id, ativo, criado_em)` — registra quais concursos o usuário tem acesso
  - Coluna `users.concurso_atual_id` (FK nullable) — concurso selecionado no header
- `migrate.py`: adicionar bloco que cria `Concurso(slug="sefaz-ce-2026")`, atribui todas as Phases existentes a ele, vincula admin user ao concurso. Idempotente.
- Novo `routers/concursos.py`:
  - `GET /api/concursos` — lista os concursos do usuário
  - `GET /api/concursos/disponiveis` — catálogo público (sem auth) p/ landing
  - `PUT /api/me/concurso-atual/{id}` — troca contexto
- **Mudança em todos os routers existentes:** filtrar queries por `user.concurso_atual_id` (helper `get_current_concurso(user, db)` em `auth.py`)

**Frontend:**
- `Layout.jsx`: dropdown de concurso no header (puxa `/api/concursos`, troca via `PUT /me/concurso-atual`)
- `api.js`: interceptor injeta header `X-Concurso-Id` (defesa em profundidade, backend ainda usa o do user)
- Todas as páginas continuam funcionando — elas só veem o que pertence ao concurso atual

**Critério de aceite:** logar como admin, ver dropdown com "SEFAZ-CE 2026", trocar para um concurso vazio mostra plano vazio (sem quebrar). Dados pessoais (attempts, erros, simulados) continuam intactos.

**Riscos:** queries existentes que não filtram por concurso vão vazar entre tenants. Mitigação: revisar todos os routers num só PR; teste manual com 2 concursos seedados.

---

## Fase 2 — Parser genérico de plano markdown `[2-3 dias]`

**Objetivo:** generalizar `seed.py:_parse_plano()` para importar qualquer plano de estudo `.md` (já que `plano.md` e `plano_estudos_tjce_f06.md` seguem padrão similar).

**Backend:**
- `seed.py` → `services/plan_importer.py`:
  - Função `import_plan(concurso_id, markdown_text)` — parseia, valida, cria Phase/Week/StudyDay/Topic
  - Suportar variações sintáticas: cronograma em tabela markdown vs lista; checkboxes (`- [ ]`) como tópicos; datas em formato dd/mm ou dd/mm/aaaa
  - Detecção de blocos prioritários (regex em seções "ALTA / MÉDIA / BAIXA")
- Novo endpoint admin: `POST /api/admin/concursos/{id}/importar-plano` (multipart `.md`)
- Manter `seed.py` chamando `import_plan()` para o concurso default no startup (compatibilidade)

**Frontend:**
- Página `Config.jsx`: seção "Importar plano" (upload `.md` + preview do parse antes de confirmar)

**Critério de aceite:** importar `plano_estudos_tjce_f06.md` → criar Concurso(slug="tjce-2026"), 5 fases, 12 semanas, ~82 study days, todos os tópicos amarrados.

**Riscos:** o TJCE plan tem estrutura diferente do SEFAZ (fase com semanas embutidas vs semanas top-level). Mitigação: aceitar 2-3 formatos via heurísticas; permitir ajuste manual no admin se parse incompleto.

**O que NÃO fazer:** tentar parser universal de qualquer markdown. Padronizar 2 formatos é suficiente, daqui pra frente novos planos seguem o template.

---

## Fase 3 — Geração de conteúdo scoped por banca/concurso `[1-2 dias]`

**Objetivo:** o material gerado leva em conta banca e perfil do concurso. FCC ≠ Cebraspe; TJCE ≠ SEFAZ.

**Backend:**
- `Concurso.prompt_extra` (text): instrução específica injetada no prompt do Claude ("Banca FCC: cobra letra de lei. Top 100 corrige redação. Cargo F06...")
- `BancaExample(id, banca, fonte, questao_md, resposta, comentario)` — questões reais por banca (ex-`fcc_examples.json`)
  - Seed: migrar `fcc_examples.json` atual → tabela
  - Endpoint `POST /api/admin/banca-examples` para upload
- `routers/materials.py:generate_for_day()`: pega `BancaExample` da banca do concurso (3-5 amostras) + `prompt_extra` e injeta no system prompt
- `audio-worker/claude_client.py`: mesma mudança — transcript do podcast usa contexto da banca/cargo

**Critério de aceite:** gerar material num StudyDay do TJCE produz questões no estilo FCC com termos do edital TJCE; o do SEFAZ continua igual.

**Riscos:** cache do Claude (você usa prompt caching) precisa que os `BancaExample` fiquem no prefixo estável. Garantir que o prompt-extra do concurso seja parte do bloco cacheado.

---

## Fase 4 — Bloco/matéria com peso e métricas `[2-3 dias]`

**Objetivo:** rastrear desempenho por **bloco temático** (ex: "Governança", "Segurança", "Português"), como a seção 11 do plano TJCE.

**Backend:**
- `Bloco(id, concurso_id, nome, peso_estimado, prioridade[alta|media|baixa], alocacao_pct, meta_acerto_pct, ordem)`
- `Topic.bloco_id` (nullable inicialmente para retro-compat; backfill via heurística nome → bloco)
- `GeneratedQuestion.bloco_id` (já tem `disciplina` em string — migrar para FK)
- `MockExamResult.bloco_id` (substitui `disciplina` string)
- Novo `routers/metricas.py`:
  - `GET /api/metricas/bloco?concurso_id=X` — agregação `acertos/total` por bloco, por semana
  - `GET /api/metricas/heatmap` — matriz bloco × semana (para o gráfico estilo seção 11)

**Frontend:**
- Nova página `/metricas` (ou seção em `Progress.jsx`): tabela bloco × semana + meta + status (verde/amarelo/vermelho)
- Card de "próximo gargalo" — bloco com maior peso e menor %acerto

**Critério de aceite:** o tracking da seção 11 do plano TJCE aparece preenchido automaticamente conforme o usuário responde questões e faz simulados.

**Por que importa para venda:** essa é a tela que vende. "Você está 35% abaixo da meta em Segurança da Informação — bloco de peso 3." É o que diferencia de qualquer outro app de estudos.

---

## Fase 5 — Módulo de Redação `[3-4 dias]`

**Objetivo:** nova feature alto-valor. Aluno escreve, Claude avalia via rubrica FCC, retorna nota e feedback estruturado.

**Backend:**
- `Redacao(id, user_id, concurso_id, numero, tema, enunciado_md, texto_aluno, nota_tema, nota_norma, nota_total, feedback_json, criado_em, corrigida_em)`
- `RedacaoTema(id, concurso_id, tema, enunciado_md, textos_apoio_md, ordem)` — banco de temas curados (você cria os primeiros à mão)
- `routers/redacoes.py`:
  - `GET /api/redacao/temas` — temas disponíveis para o concurso
  - `POST /api/redacao` — aluno submete (dispara correção async via background task ou worker)
  - `GET /api/redacao/{id}` — texto + feedback
- Prompt Claude para correção segue rubrica FCC (você já tem em `plano_estudos_tjce_f06.md` seção 9: TEMA 7,0 / NORMA 3,0)

**Frontend:**
- Nova página `/redacao`: lista de temas, editor textarea, contador de linhas (20-30), botão "submeter para correção"
- Visualização: nota + feedback por critério + sugestões inline

**Critério de aceite:** submeter redação retorna em <30s feedback estruturado e nota com mesma rubrica da FCC.

**Por que importa para venda:** correção de redação é caro (R$30-60 a peça em cursinhos). Oferecer correção ilimitada é o **gancho premium**. Custo real Claude: ~R$0,15 por correção.

---

## Fase 6 — Signup público + Billing `[5-7 dias]`

**Objetivo:** abrir o cadastro e cobrar.

**Decisão de pricing (sugestão a discutir):**
- **R$39/mês por concurso** (assinatura recorrente Stripe) OU
- **R$197 pagamento único até a data da prova** (Pix manual ou Stripe one-time)
- Trial: 7 dias grátis com acesso completo

**Backend:**
- `Subscription(id, user_id, concurso_id, tipo[mensal|unica], status[ativa|trial|cancelada|inadimplente], stripe_subscription_id, stripe_customer_id, inicio, fim, criado_em)`
- `PaymentEvent(id, subscription_id, tipo, payload_json, criado_em)` — log de webhooks
- `routers/auth.py`:
  - `POST /api/auth/signup` (email + senha + concurso de interesse) — cria User + Subscription em `trial`
  - Confirmação por email opcional (use Resend free tier ou SES)
- `routers/billing.py`:
  - `POST /api/billing/checkout/{concurso_id}` — cria Stripe Checkout Session, retorna URL
  - `POST /api/billing/webhook` — endpoint público com verificação de assinatura Stripe
  - `GET /api/billing/portal` — Stripe Customer Portal (cancelar/atualizar cartão)
- **Middleware paywall:** `require_active_subscription(concurso_id)` em routers de conteúdo (gerar material, baixar áudio, redação). Routers de leitura (ver plano, dashboard) liberados em trial.

**Frontend:**
- Landing page `/` pública (separada do app):
  - Hero, vídeo de 60s, prints do dashboard de métricas, depoimento (você mesmo, SEFAZ-CE)
  - Lista de concursos disponíveis (puxa `/api/concursos/disponiveis`)
  - CTA: "Comece grátis por 7 dias"
- Páginas: `/signup`, `/checkout/{concurso_id}`, `/billing` (gerenciar assinatura)
- Banner "Faltam X dias do trial" no Layout

**Critério de aceite:** pessoa nova entra na landing → escolhe TJCE → cadastra → trial ativo → após 7 dias é bloqueado nos endpoints de geração até pagar.

**Alternativa MVP (se Stripe demora):** Pix manual. Endpoint `POST /api/billing/pix-request` gera QR code via gateway tipo Mercado Pago/Pagar.me. Admin ativa manualmente após receber.

**Riscos:** Stripe BR exige CNPJ e KYC, pode levar 1-2 semanas para liberar. Plano B: começar com Mercado Pago (mais ágil para BR) ou Pix manual + Stripe depois.

---

## Fase 7 — Hardening multi-tenant + LGPD `[2-3 dias]`

**Objetivo:** ficar legalmente OK e estável para usuários reais.

- **Auditoria de queries:** grep por queries sem `user_id` ou `concurso_id` filter. Adicionar testes com 2 users + 2 concursos.
- **LGPD básico:**
  - Política de privacidade + termos de uso (gerar via template Iubenda free tier ou redigir)
  - `DELETE /api/me` — apaga dados do usuário (soft delete + anonimização)
  - `GET /api/me/export` — exporta JSON com tudo do usuário
  - Checkbox de aceite no signup
- **Quotas anti-abuso:**
  - Audio gen: max 1 audio/dia/usuário (TTS free tier 1M chars; 1 áudio ~5k chars → cabem ~200 áudios/mês free)
  - Redação: max 3/dia
  - Geração de material: cacheada (1 vez por dia, compartilhada entre todos do mesmo concurso — você já faz isso)
- **Backup:**
  - Cron diário: `sqlite3 .backup` → upload para Backblaze B2 ou Cloudflare R2 (custo: <$1/mês)
  - Retenção: 30 dias
- **Observabilidade mínima:**
  - Sentry free tier (5k events/mês) para erros
  - Endpoint `/api/health` já tem? Adicionar `/api/metrics` (gen/dia, users ativos)

**Critério de aceite:** rodar com 3 usuários de teste em 2 concursos diferentes por uma semana sem vazamento de dados nem incidente.

---

## Fase 8 — Lançamento TJCE `[2-3 dias]`

- **Domínio:** decidir `audifaz.com.br` (genérico) vs `audifaz.com.br/tjce` vs subdomínio por concurso. **Recomendação:** domínio único + dropdown de concurso. Mais simples, mesmo SEO.
- **Conteúdo de marketing:**
  - 5-8 posts orgânicos em grupos de concurso TI no Telegram/Discord
  - 1 post no LinkedIn explicando o app
  - Vídeo de 2 minutos com walkthrough (Loom)
- **Validação:** captar 5-10 usuários reais antes de pagar tráfego. Se 2+ assinarem no trial, sinal verde.
- **Suporte:** caixa única `suporte@audifaz.com.br` (Gmail forward grátis). SLA informal 24h.

---

## Cronograma sugerido (sequencial, ~5 semanas focado)

| Semana | Fases | Resultado |
|---|---|---|
| 1 | Fase 1 + Fase 2 | TJCE importado e navegável em paralelo ao SEFAZ |
| 2 | Fase 3 + Fase 4 | Conteúdo do TJCE com estilo FCC + dashboard de bloco |
| 3 | Fase 5 | Redação funcionando, você corrige suas próprias para validar |
| 4 | Fase 6 (parte 1) | Signup público + Pix manual; convidar 3-5 amigos beta |
| 5 | Fase 6 (parte 2) + Fase 7 + Fase 8 | Stripe, LGPD, landing, lançamento |

Realista (com job e estudo paralelo): **8-10 semanas**.

---

## Custos operacionais estimados (10 assinantes ativos)

| Item | Custo/mês |
|---|---|
| OCI ARM (já paga) | R$ 0 |
| GCP Chirp TTS (até 1M chars free) | R$ 0 (acima: ~R$0,08/áudio) |
| Claude API (~30 gerações/mês × 10 users) | R$ 60-90 |
| Stripe (3.99% + R$0,39/transação) | R$ 25 |
| Domínio + email | R$ 5 |
| Backup B2 | R$ 3 |
| **Total** | **~R$ 95/mês** |

**Breakeven:** 3 assinantes a R$39/mês cobrem o custo.

---

## Riscos e mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| SQLite gargalo com 50+ users | BAIXA até 30 users | WAL mode já está; migração para Postgres é trivial (SQLAlchemy abstrai); só fazer quando latência subir |
| Custo Claude explode | MÉDIA | Cache de prompt (já tem); 1 geração/dia/concurso (não por usuário); usar Haiku 4.5 para gerações menos críticas |
| Stripe não libera CNPJ | MÉDIA | Plano B: Mercado Pago ou Pagar.me; Plano C: Pix manual + ativação por admin |
| Pirataria de PDFs (alguém compartilha login) | BAIXA-MÉDIA | Limite de 2 dispositivos por conta (JWT com device_id); watermark invisível nos áudios |
| Edital muda durante o ciclo | BAIXA | Replano é manual; oferecer como diferencial ("plano atualizado conforme edital") |
| Suporte vira gargalo | MÉDIA | FAQ no app + documentação em vídeo; comunidade no Discord para tirar dúvidas entre alunos |

---

## O que NÃO fazer no MVP

- ❌ Migrar para Postgres antes de precisar (SQLite aguenta dezenas de users)
- ❌ Implementar admin panel completo. Use o próprio Config.jsx + endpoints admin
- ❌ Múltiplos planos por concurso ("plano intensivo" vs "plano relax"). Um plano por concurso basta
- ❌ App mobile nativo. PWA + podcast feed (já tem!) já entrega offline e mobile
- ❌ Gamificação (XP, badges, streaks). Não é o público
- ❌ Comunidade/fórum interno. Discord externo se algum dia precisar
- ❌ Cupons de desconto antes de validar pricing
- ❌ Migração de schema "perfeita" — manter campos legados nullable, deprecar depois

---

## Decisões pendentes (precisa do seu input antes de começar)

1. **Modelo de cobrança:** assinatura mensal recorrente vs pagamento único até a prova vs ambos?
2. **Preço:** R$39/mês? R$197 single? Outra faixa?
3. **Provedor de pagamento:** Stripe (mais limpo) vs Mercado Pago (mais rápido pra BR) vs Pix manual no MVP?
4. **Identidade visual única ou por concurso:** "AudiFaz TJCE" / "AudiFaz SEFAZ" como sub-brands, ou só "AudiFaz" com dropdown?
5. **Continua usando pessoalmente?** Se sim, seu user fica isento da paywall (flag `is_internal=True` no model).

---

*Doc gerado em 19/05/2026. Próximo passo recomendado: começar pela Fase 1 num branch `feat/concurso-multi-tenant`.*
