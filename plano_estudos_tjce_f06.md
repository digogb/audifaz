# Plano de Estudos — TJCE 2026 · Cargo F06 (Analista Judiciário – Apoio Especializado – Ciência da Computação – TI Sistemas)

> **Replanejado em:** 31/05/2026, com base no **Edital de Abertura** e na **Retificação do Conteúdo Programático do cargo F06** publicada no DJe nº 3786 (29/05/2026).
> **Início dos estudos:** 01/06/2026 (segunda) · **Data da prova:** 09/08/2026 (domingo, período da MANHÃ) · **Janela:** 10 semanas (70 dias).
> **Banca:** Fundação Carlos Chagas (FCC) · **Cidades de prova:** Fortaleza, Juazeiro do Norte ou Sobral/CE.
> **Aluno:** Valdyr Junior — formado em TI, com lacunas pontuais. **Carga-alvo:** ~18h/semana (2h por dia útil + 4h por dia de fim de semana).

---

## 0. ⚠️ O que mudou com a retificação (leia primeiro)

A retificação de 29/05 **trocou o perfil técnico do cargo**. O F06 deixou de ser um cargo de *governança clássica de TI* e passou a ser um cargo de **Gestão de Produtos Digitais (Product Management / Product Ownership) com profundidade técnica**.

**Saiu do edital (não cai mais como antes):** ITIL v4, COBIT 2019, PMBOK 7, CMMI-DEV, MR-MPS, e a maioria das ISOs (25010, 27001/02/05, 31000) como blocos centrais.

**Entrou (núcleo da prova agora):**
- **Gestão de Produtos Digitais** (visão de produto, backlog, MoSCoW/RICE/WSJF, PO×PM, MVP/MMF, feature flags)
- **Análise de Negócio e Requisitos** (elicitação, BPMN 2.0, user stories, DoD/DoR)
- **Estratégia e Design de Produto** (Design Thinking, Discovery, UX/e-MAG, OKR, roadmaps)
- **Agilidade e Portfólio** (Scrum, Kanban, **Flight Levels**, PI Planning)
- **Métricas de produto** (Lead/Cycle Time, Throughput, CFD, NPS/CSAT, A/B, cohort)
- **Engenharia de Domínio** (DDD estratégico, Strangler Fig, API-led Connectivity, modelo TIME)
- **Software Assurance** (**OWASP SAMM**, threat modeling, IAM/RBAC, SBOM)
- **IA aplicada ao produto** (IA generativa no SDLC, engenharia de prompt, **RAG**, agentes, **Resolução CNJ 615**)
- **Engenharia de Dados** (Data Lake/DW/Lakehouse, modelagem dimensional, ETL/ELT)
- **RPA e Hyperautomation**
- **Java / Spring Boot**
- **Contratações de TIC** (Lei 14.133/2021, normativos CNJ, gestão contratual)

A boa notícia para um profissional formado em TI: muito disso é **conceito aplicado**, não decoreba puro de norma. A FCC vai descrever cenários e pedir o conceito certo. O ganho está em **dominar o vocabulário de produto/gestão** (que dev costuma não ter) e **fechar lacunas técnicas pontuais**.

---

## 1. Sumário executivo (TL;DR)

- **Prova:** 60 questões objetivas (**20 Conhecimentos Gerais + 40 Conhecimentos Específicos**) + Redação dissertativo-argumentativa. Duração 4h, manhã.
- **Pesos:** CG = peso 1, CE = peso 3, Redação = peso 1. A CE com peso 3 é onde a classificação se decide.
- **Filtro real:** a Redação só é corrigida para os **mais bem classificados na objetiva** (quadro do item 12.2 do edital) + todos os cotistas habilitados. Quem não entra nesse corte é eliminado mesmo com redação boa. **Logo, a objetiva (especialmente a CE) é o verdadeiro funil.**
- **Estratégia para o Valdyr:** com ~18h/semana, não dá para estudar tudo com a mesma profundidade. O plano **prioriza os blocos de produto/gestão (novos, alto peso e onde quase ninguém chega afiado)** e faz **revisão dirigida** do técnico que você já tem base. Português e RLM entram em doses semanais constantes — são 13–17 questões de CG somadas e não podem ser abandonadas.

---

## 2. Mapa da prova F06

### 2.1. Conhecimentos Gerais (20 questões — peso 1)

| Matéria | Questões estimadas | Prioridade |
|---|---|---|
| Língua Portuguesa | 8–10 | **ALTA** |
| Raciocínio Lógico-Matemático (com proporção e estatística) | 5–7 | **MÉDIA-ALTA** |
| Direitos das Pessoas com Deficiência (Res. CSJT 386/2024 art. 6º + leis citadas) | 2–3 | MÉDIA (decoreba) |
| Legislação: Lei 9.826/1974 (Estatuto CE), Previdência CE, Lei 16.397/2017 (Org. Judiciária CE) | 3–4 | **ALTA** (decoreba puro) |

### 2.2. Conhecimentos Específicos (40 questões — peso 3)

Distribuição estimada a partir dos 15 grandes temas da retificação:

| Bloco (tema do edital) | Questões esperadas | Dificuldade p/ Valdyr |
|---|---|---|
| 1. Gestão de Produtos Digitais (PM/PO) | 4–6 | **ALTA** (vocabulário novo) |
| 2. Análise de Negócio e Requisitos (BPMN, user stories) | 3–4 | MÉDIA |
| 3. Estratégia, Ideação e Design (Design Thinking, UX, OKR) | 3–4 | **ALTA** (novo) |
| 4. Agilidade e Portfólio (Scrum, Kanban, Flight Levels) | 3–4 | MÉDIA |
| 5. Métricas de Produto | 2–3 | **ALTA** (novo) |
| 6. Riscos, Qualidade e Conformidade (LGPD, FinOps) | 2–3 | MÉDIA |
| 7. Engenharia de Domínio e Modernização (DDD, Strangler, API-led) | 3–4 | MÉDIA |
| 8. Software Assurance (OWASP SAMM, threat modeling, IAM, SBOM) | 3–4 | **ALTA** (SAMM é novo) |
| 9. IA aplicada ao produto (generativa, RAG, agentes, CNJ 615) | 3–4 | **ALTA** (novo) |
| 10. Engenharia de Dados e Plataformas Analíticas | 2–3 | MÉDIA |
| 11. Automação e RPA / Hyperautomation | 1–2 | MÉDIA |
| 12. Engenharia de Software Moderna (microsserviços, K8s, DevSecOps) | 2–3 | BAIXA-MÉDIA |
| 13. Desenvolvimento com Java (Spring Boot, JPA, mensageria) | 2–3 | BAIXA-MÉDIA |
| 14. Planejamento/Contratação/Fiscalização de TIC (Lei 14.133, CNJ) | 2–3 | **ALTA** (decoreba) |
| 15. Inglês técnico | 1–2 | BAIXA |

### 2.3. Redação (peso 1)

- **Tipo:** dissertativo-argumentativo autoral, **tema de interesse geral** (não atrelado à TI).
- **Critérios (item 12 do edital):**
  - **TEMA (7,0):** recorte temático (2,0) + interpretação crítica dos textos de apoio (2,0) + progressão textual (3,0).
  - **NORMA-PADRÃO (3,0):** propriedade vocabular (0,8) + coesão textual (1,6) + morfossintaxe (0,6).
- **Zera** se fugir ao tema/modalidade, escrever em outra língua, ter menos de 8 linhas, ou se identificar.
- **Atenção FCC:** não marque recuo de parágrafo com sinal (ponto/traço) — use o recuo natural da margem.

---

## 3. Como a FCC pensa (e o que isso muda no estudo)

1. **Conceito literal e aplicado:** a alternativa correta costuma ser a definição do conceito ou um cenário que mapeia para ele. Decore as **definições e os números** (5 domínios do SAMM, 3 Flight Levels, técnicas de priorização, etc.).
2. **Sem pegadinha psicológica (≠ Cebraspe):** eliminação por exclusão funciona bem. Alternativa que mistura conceitos de áreas diferentes geralmente está errada.
3. **Enunciados longos com cenário:** "uma equipe quer substituir um sistema legado gradualmente sem big-bang" → **Strangler Fig**. Treine reconhecer o conceito a partir da situação.
4. **Português pesado:** questões longas com pegadinhas em concordância, regência, crase, pronomes. Não subestime.
5. **RLM com cálculo:** lógica proposicional + porcentagem/regra de três + estatística (média, mediana, desvio padrão). Treine cálculo mental.
6. **Em TI, a FCC adora:** nomes e propósitos (qual técnica de priorização, qual métrica de fluxo, qual domínio do SAMM), LGPD literal (bases legais, agentes), Lei 14.133 (fases, modalidades), e diferenciar conceitos próximos (Outcome × Output, DoD × DoR, AS-IS × TO-BE).

**Insight para o seu perfil:** a tentação de quem é de TI é estudar Java/microsserviços/Docker (conforto). Resista. O ganho marginal por hora é muito maior em **Product Management, OWASP SAMM, IA aplicada e contratações** — temas que você provavelmente nunca formalizou e que somam ~18–22 questões de peso 3.

---

## 4. Diagnóstico para o perfil do Valdyr (formado em TI, com lacunas)

### Provável base já consolidada (revisar rápido, não estudar do zero)
- Programação e POO; conceitos de REST/APIs; Git
- Microsserviços, Docker e noções de Kubernetes
- Banco de dados relacional e SQL; modelagem ER
- Conceitos gerais de DevOps/CI-CD

### Lacunas prováveis (onde mora o ganho por hora)
- **Todo o vocabulário de produto/gestão:** visão de produto, backlog, MoSCoW/RICE/WSJF, MVP/MMF, OKR, roadmaps, métricas de produto, Flight Levels, PI Planning
- **Design Thinking / Discovery / UX (e-MAG)**
- **OWASP SAMM** (estrutura e 5 domínios) e **threat modeling** formal
- **IA aplicada:** RAG, agentes, engenharia de prompt, ética/governança (CNJ 615)
- **DDD estratégico** (Core/Supporting/Generic, bounded context, context mapping) e **API-led Connectivity**
- **Contratações de TIC:** Lei 14.133/2021, normativos do CNJ, papéis de gestão contratual
- **LGPD literal** (bases legais, agentes, Privacy by Design/Default)
- **Legislação CE** (Estatuto 9.826/1974, Org. Judiciária 16.397/2017, Previdência CE) — decoreba puro
- **Português normativo** (regência, crase, concordância) e **estatística no RLM**

### Alocação de esforço sugerida (% das ~180h totais)

| Bloco | % do tempo |
|---|---|
| Produto, Estratégia, Agilidade e Métricas (temas 1–5) | 24% |
| Software Assurance + LGPD + Riscos (temas 6 e 8) | 12% |
| Engenharia de Domínio + Software Moderno + Java (temas 7, 12, 13) | 13% |
| IA aplicada ao produto (tema 9) | 8% |
| Engenharia de Dados + RPA (temas 10, 11) | 7% |
| Contratações de TIC + CNJ (tema 14) | 7% |
| Português | 11% |
| RLM (lógica + estatística) | 7% |
| Legislação CE + Direitos PCD | 6% |
| Redação | 4% |
| Inglês técnico + folga/revisão | 1% |

---

## 5. Cronograma macro (10 semanas)

| Fase | Semanas | Datas | Foco |
|---|---|---|---|
| **F1 — Diagnóstico e Fundamentos de Produto** | 1–2 | 01/06 – 14/06 | Nivelamento, Gestão de Produtos Digitais, Análise de Negócio e Requisitos |
| **F2 — Estratégia, Agilidade e Métricas** | 3–4 | 15/06 – 28/06 | Design Thinking/Discovery/UX/OKR, Scrum/Kanban/Flight Levels, métricas, LGPD |
| **F3 — Engenharia, Domínio e Segurança** | 5–6 | 29/06 – 12/07 | DDD, modernização, microsserviços/DevSecOps, OWASP SAMM, IAM, SBOM |
| **F4 — IA, Dados, RPA, Java e Contratações** | 7–8 | 13/07 – 26/07 | IA aplicada/RAG/agentes, engenharia de dados, RPA, Java/Spring, Lei 14.133 |
| **F5 — Revisão e Simulados** | 9–10 | 27/07 – 09/08 | Simulados cronometrados, revisão espaçada, números exatos, legislação CE, ajuste fino |

---

## 6. Cronograma detalhado por dia

> Cada dia útil ≈ 2h (1 frente principal); cada dia de fim de semana ≈ 4h (2 frentes). Onde houver feriado regional (Corpus Christi 04/06; São João 24/06), trate como dia mais leve ou compense no fim de semana.

### Semana 1 (01/06 – 07/06) — Diagnóstico + Gestão de Produtos Digitais

- [ ] **Dia 1 (01/06, seg):** Simulado diagnóstico — 20 questões de CG + 40 de CE de provas FCC anteriores de Analista TI, sem estudar antes. Medir o ponto de partida e montar a planilha de tracking (um % por bloco da seção 11).
- [ ] **Dia 2 (02/06, ter):** Visão de Produto — propósito, objetivos estratégicos e alinhamento com a missão institucional; capacidades de negócio; proposição de valor; Canvas de Proposição de Valor; análise competitiva.
- [ ] **Dia 3 (03/06, qua):** Português — Ortografia, acentuação e emprego do sinal indicativo de crase. Resolver 20 questões FCC.
- [ ] **Dia 4 (04/06, qui):** Ciclo de vida do produto (introdução, crescimento, maturidade, descontinuidade/decommissioning de legados) e papéis/responsabilidades de Product Owner × Product Manager no Scrum e em fluxos Kanban.
- [ ] **Dia 5 (05/06, sex):** Gestão de Backlog — criação, refinamento, estimativa e priorização; técnicas **MoSCoW, RICE, WSJF** e Matriz Valor × Esforço.
- [ ] **Dia 6 (06/06, sáb):** Release Planning, definição de **MVP** e **MMF** no contexto público; estratégias de feature flags, phased rollouts e dark launches.
- [ ] **Dia 6 (06/06, sáb):** Gestão de stakeholders (mapeamento de influência, comunicação, expectativas) e fundamentos de arquitetura corporativa com base no **TOGAF** (ADM, 4 domínios, building blocks — visão conceitual).
- [ ] **Dia 7 (07/06, dom):** Redação 1 — tema de interesse geral; escrever 20–30 linhas e autocorrigir pela rubrica FCC (TEMA 7,0 / NORMA 3,0). Identificar nível inicial.
- [ ] **Dia 7 (07/06, dom):** Revisão da semana — refazer questões erradas do diagnóstico nos tópicos de produto já estudados; consolidar fichas de MoSCoW/RICE/WSJF e MVP/MMF.

### Semana 2 (08/06 – 14/06) — Análise de Negócio e Requisitos

- [ ] **Dia 1 (08/06, seg):** Técnicas de elicitação de requisitos — entrevistas, questionários, observação, workshops de requisitos e análise de documentos.
- [ ] **Dia 2 (09/06, ter):** RLM — estrutura lógica de relações arbitrárias; raciocínio verbal, sequencial e orientação espacial/temporal. Resolver questões FCC.
- [ ] **Dia 3 (10/06, qua):** BPMN 2.0 — modelagem da situação atual (**AS-IS**) e futura (**TO-BE**); eventos, atividades, gateways, pools/lanes; fluxo de sequência × fluxo de mensagem.
- [ ] **Dia 4 (11/06, qui):** Especificação de requisitos — funcionais, não-funcionais e regras de negócio; categorias (FURPS+); rastreabilidade.
- [ ] **Dia 5 (12/06, sex):** Documentação ágil — User Stories, Critérios de Aceitação, **Definition of Done (DoD)** e **Definition of Ready (DoR)**.
- [ ] **Dia 6 (13/06, sáb):** Gap Analysis (análise de lacunas) e análise de viabilidade técnica e de negócio.
- [ ] **Dia 6 (13/06, sáb):** Português — morfossintaxe, classes de palavras, processos de formação de palavras, sinonímia e antonímia. Resolver questões FCC.
- [ ] **Dia 7 (14/06, dom):** Legislação CE — Lei Estadual 9.826/1974 (Estatuto dos Funcionários Públicos do Ceará): 1ª leitura — provimento, posse, direitos, deveres e regime disciplinar.
- [ ] **Dia 7 (14/06, dom):** Redação 2 — tema social/atual, com autocorreção pela rubrica FCC.

### Semana 3 (15/06 – 21/06) — Estratégia, Design e Agilidade

- [ ] **Dia 1 (15/06, seg):** Design Thinking — empatia, definição, ideação (mapa mental, brainwriting, **SCAMPER**, **Jobs To Be Done**, future backwards, escrita de **PRD**), prototipação e teste.
- [ ] **Dia 2 (16/06, ter):** Português — pontuação, concordância nominal e concordância verbal. Resolver questões FCC.
- [ ] **Dia 3 (17/06, qua):** Product Discovery — técnicas de exploração de problemas e validação de soluções; relação discovery × delivery.
- [ ] **Dia 4 (18/06, qui):** UX/UI — usabilidade, acessibilidade (**e-MAG** e WCAG), arquitetura de informação, prototipação de baixa e alta fidelidade.
- [ ] **Dia 5 (19/06, sex):** Planejamento estratégico de TI com **OKRs** (objetivos e resultados-chave) e Roadmaps de produto (baseados em resultados × em funcionalidades).
- [ ] **Dia 6 (20/06, sáb):** Scrum (papéis, eventos, artefatos e compromissos) e Método Kanban (princípios, práticas, limite de WIP, métricas de fluxo).
- [ ] **Dia 6 (20/06, sáb):** RLM — proposições, conectivos, tabelas-verdade e equivalências lógicas (De Morgan, condicional). Resolver questões FCC.
- [ ] **Dia 7 (21/06, dom):** Agilidade em escala — **Flight Levels** (níveis 1, 2 e 3), **PI Planning** (planejamento trimestral), sincronização entre times e gestão de dependências com sistemas legados.
- [ ] **Dia 7 (21/06, dom):** Redação 3 — tema institucional (ex.: transformação digital do Estado), com autocorreção.

### Semana 4 (22/06 – 28/06) — Métricas, Riscos e Conformidade

- [ ] **Dia 1 (22/06, seg):** Métricas de processo (eficiência) — Lead Time, Cycle Time, Throughput e **CFD** (Cumulative Flow Diagram).
- [ ] **Dia 2 (23/06, ter):** Métricas de produto (eficácia) — adoção, engajamento e satisfação (**NPS, CSAT** no serviço público), testes A/B, análise de cohort, análise preditiva; **Outcomes × Outputs**.
- [ ] **Dia 3 (24/06, qua):** Português — regência nominal e verbal, crase aplicada, coordenação e subordinação, conectivos. (São João: dia mais leve.) Resolver questões FCC.
- [ ] **Dia 4 (25/06, qui):** Gestão de riscos de produto (valor, viabilidade, usabilidade e riscos jurídicos/regulatórios) e **FinOps** básico (gestão de custos em nuvem, eficiência no ciclo de vida).
- [ ] **Dia 5 (26/06, sex):** LGPD aplicada ao desenvolvimento — **Privacy by Design** e **Privacy by Default**; governança e qualidade do dado para a tomada de decisão.
- [ ] **Dia 6 (27/06, sáb):** LGPD letra de lei (Lei 13.709/2018) — fundamentos e princípios, **10 bases legais** (art. 7º) + dados sensíveis (art. 11), agentes (controlador, operador, encarregado/DPO), direitos do titular, ANPD, tratamento pelo Poder Público e sanções.
- [ ] **Dia 6 (27/06, sáb):** Português — revisão consolidada (refazer erros das semanas 1–4).
- [ ] **Dia 7 (28/06, dom):** Legislação CE — Lei 16.397/2017 (Lei de Organização Judiciária do Ceará): estrutura e órgãos do TJCE, competências.
- [ ] **Dia 7 (28/06, dom):** Redação 4 — tema de atualidades, com autocorreção.

### Semana 5 (29/06 – 05/07) — Engenharia de Domínio e Software Moderno

- [ ] **Dia 1 (29/06, seg):** DDD Estratégico — domínios e subdomínios (**Core, Supporting, Generic**), **Bounded Contexts**, Linguagem Ubíqua e **Context Mapping** (estratégias de integração).
- [ ] **Dia 2 (30/06, ter):** Modernização de legados — decomposição de monólitos, padrão **Strangler Fig** (estrangulamento), coexistência novo/antigo; gestão de dívida técnica (refatoração × novas funcionalidades); **modelo TIME** de portfólio de aplicações.
- [ ] **Dia 3 (01/07, qua):** **API-led Connectivity** — APIs como produto de negócio; APIs de Sistema, de Processo e de Experiência; governança de APIs; interoperabilidade com a **PDPJ-Br** (Plataforma Digital do Poder Judiciário).
- [ ] **Dia 4 (02/07, qui):** Arquitetura distribuída e microsserviços — granularidade, contratos, Service Discovery, API Gateway, **Circuit Breaker**; comunicação síncrona (REST) × assíncrona (eventos/mensageria).
- [ ] **Dia 5 (03/07, sex):** Conteinerização e orquestração — Docker e Kubernetes (pods, deployments, services, ingress, configmaps/secrets); práticas DevOps e **DevSecOps** (CI/CD, SAST/DAST/SCA).
- [ ] **Dia 6 (04/07, sáb):** Observabilidade — logs, métricas e rastreamento distribuído (três pilares); testes automatizados e qualidade de software.
- [ ] **Dia 6 (04/07, sáb):** RLM — lógica de argumentação, silogismos e raciocínio sequencial (séries numéricas e de figuras). Resolver questões FCC.
- [ ] **Dia 7 (05/07, dom):** Simulado parcial cronometrado dos blocos de Produto/Gestão/Engenharia já estudados (≈40 questões) + correção e registro na caderneta de erros.
- [ ] **Dia 7 (05/07, dom):** Redação 5 — com autocorreção.

### Semana 6 (06/07 – 12/07) — Software Assurance (Segurança de Software e Governança)

- [ ] **Dia 1 (06/07, seg):** **OWASP SAMM** — estrutura, princípios e os 5 domínios de negócio (**Governance, Design, Implementation, Verification, Operations**) e níveis de maturidade.
- [ ] **Dia 2 (07/07, ter):** Segurança no ciclo de desenvolvimento (SDLC) — **Security by Design**; práticas de segurança por fase, da concepção à operação.
- [ ] **Dia 3 (08/07, qua):** Português — vozes do verbo, correlação de tempos e modos verbais, flexão verbal/nominal; reescrita e equivalência de estruturas (estilo FCC).
- [ ] **Dia 4 (09/07, qui):** **Threat Modeling** — identificação de ativos, superfícies de ataque e vetores de ameaça (STRIDE); gestão de vulnerabilidades de lógica de negócio e fluxos de aprovação judicial.
- [ ] **Dia 5 (10/07, sex):** **IAM** — gestão de identidade e acesso; princípio do menor privilégio; **RBAC** × ABAC; autenticação (MFA, SSO, OAuth 2.0, OIDC).
- [ ] **Dia 6 (11/07, sáb):** Segurança da cadeia de suprimentos de software — componentes de terceiros e **SBOM** (Software Bill of Materials); conformidade e auditoria (rastreabilidade de logs, não-repúdio).
- [ ] **Dia 6 (11/07, sáb):** LGPD no desenvolvimento — Relatório de Impacto à Proteção de Dados (**RIPD/DPIA**) em novas funcionalidades.
- [ ] **Dia 7 (12/07, dom):** Direitos das Pessoas com Deficiência — Res. CSJT 386/2024 (art. 6º), Lei 13.146/2015 (Estatuto da PcD); acessibilidade (Lei 10.098/2000, Decreto 5.296/2004), prioridade de atendimento (Lei 10.048/2000).
- [ ] **Dia 7 (12/07, dom):** Redação 6 — com autocorreção.

### Semana 7 (13/07 – 19/07) — IA aplicada ao produto + Engenharia de Dados

- [ ] **Dia 1 (13/07, seg):** Fundamentos de IA e Machine Learning — conceitos e tipos de aprendizado; aplicações em sistemas; **PLN** (Processamento de Linguagem Natural) no contexto jurídico.
- [ ] **Dia 2 (14/07, ter):** IA Generativa no SDLC — uso de LLMs para escrita de requisitos, histórias de usuário, critérios de aceitação e documentação (PRDs); **Engenharia de Prompt** (princípios e técnicas).
- [ ] **Dia 3 (15/07, qua):** RLM — proporcionalidade e porcentagem (regra de três simples, acréscimos e descontos) e **Estatística** (média, moda, mediana; desvio médio, amplitude, variância, desvio padrão; leitura de gráficos e tabelas).
- [ ] **Dia 4 (16/07, qui):** **RAG** (Retrieval-Augmented Generation) — fundamentos e aplicações; **agentes e workflows agênticos** (orquestração de tarefas); arquiteturas de IA (APIs de modelos, integração, pipelines de dados).
- [ ] **Dia 5 (17/07, sex):** UX for AI (incerteza, explicabilidade, human-in-the-loop); avaliação e monitoramento de IA (alucinação, latência, qualidade); ética, governança e riscos de IA — vieses, transparência algorítmica e **Resolução CNJ 615**.
- [ ] **Dia 6 (18/07, sáb):** Engenharia de Dados — Data Lake, Data Warehouse e **Lakehouse**; modelagem relacional e dimensional (**Star Schema** e **Snowflake**); **ETL × ELT**.
- [ ] **Dia 6 (18/07, sáb):** Inglês técnico — leitura de documentação/abstract; vocabulário técnico recorrente em provas FCC.
- [ ] **Dia 7 (19/07, dom):** Qualidade, governança e catalogação de dados (linhagem, metadados); processamento distribuído; integração de dados (APIs, mensageria, dados estruturados/não estruturados); base para BI e IA.
- [ ] **Dia 7 (19/07, dom):** Redação 7 — com autocorreção.

### Semana 8 (20/07 – 26/07) — RPA, Java/Spring e Contratações de TIC

- [ ] **Dia 1 (20/07, seg):** Automação de processos e **RPA** — BPM × RPA; identificação e priorização de processos automatizáveis; robôs (fluxos, tratamento de exceções, reprocessamento); **Hyperautomation** (RPA + IA + OCR).
- [ ] **Dia 2 (21/07, ter):** Java e POO — linguagem, orientação a objetos, tratamento de exceções e boas práticas de codificação.
- [ ] **Dia 3 (22/07, qua):** **Spring Boot / Spring MVC** — REST, JPA e Hibernate, transações e controle de concorrência; padrões API Gateway, Service Discovery e Circuit Breaker.
- [ ] **Dia 4 (23/07, qui):** Mensageria — filas e tópicos; comunicação síncrona (REST) × assíncrona; conceitos de **Kafka** e **RabbitMQ** (exchanges, AMQP).
- [ ] **Dia 5 (24/07, sex):** **Lei 14.133/2021** aplicada à TI — princípios, fases da contratação (planejamento, seleção, gestão contratual), modalidades e critérios de julgamento, dispensa e inexigibilidade; **ETP** (Estudo Técnico Preliminar) e **Termo de Referência**.
- [ ] **Dia 6 (25/07, sáb):** Contratação e fiscalização de TIC — normativos do **CNJ** (governança de TIC, **PDTIC**); papéis (gestor, fiscal técnico e administrativo); medição e aceite; **SLA/ANS**; penalidades, reequilíbrio econômico-financeiro e encerramento contratual.
- [ ] **Dia 6 (25/07, sáb):** RLM — revisão geral (lógica + estatística), refazendo erros das semanas anteriores.
- [ ] **Dia 7 (26/07, dom):** Simulado completo cronometrado (60 questões + redação, 4h, de manhã) — condicionar corpo e ritmo ao formato real.
- [ ] **Dia 7 (26/07, dom):** Correção do simulado + Redação 8 (a redação do próprio simulado) + atualização da caderneta de erros.

### Semana 9 (27/07 – 02/08) — Revisão dirigida + Simulados

- [ ] **Dia 1 (27/07, seg):** Revisão — Gestão de Produtos (visão, ciclo de vida, backlog/MoSCoW/RICE/WSJF, PO×PM, MVP/MMF) via flashcards.
- [ ] **Dia 2 (28/07, ter):** Revisão — Agilidade (Scrum/Kanban/Flight Levels/PI Planning) e Métricas (Lead/Cycle/Throughput/CFD, NPS/CSAT, A/B, cohort, Outcomes×Outputs).
- [ ] **Dia 3 (29/07, qua):** Revisão — Software Assurance (OWASP SAMM, threat modeling, IAM/RBAC, SBOM) e LGPD (bases legais, agentes, Privacy by Design/Default).
- [ ] **Dia 4 (30/07, qui):** Revisão — Engenharia/Modernização (DDD, Strangler Fig, API-led, microsserviços, Docker/K8s, observabilidade) e Java/Spring.
- [ ] **Dia 5 (31/07, sex):** Revisão — IA aplicada (generativa, RAG, agentes, ética/CNJ 615), Engenharia de Dados (DW/Lakehouse, dimensional, ETL/ELT) e RPA.
- [ ] **Dia 6 (01/08, sáb):** Simulado completo cronometrado (manhã, mesmo horário da prova) + correção detalhada.
- [ ] **Dia 6 (01/08, sáb):** Legislação CE — revisão consolidada (Lei 9.826/1974 + Lei 16.397/2017 + Previdência CE).
- [ ] **Dia 7 (02/08, dom):** Revisão — Contratações de TIC (Lei 14.133, CNJ/PDTIC, gestão contratual) e Direitos das Pessoas com Deficiência.
- [ ] **Dia 7 (02/08, dom):** Redação 9 — com autocorreção pela rubrica FCC.

### Semana 10 (03/08 – 09/08) — Ajuste fino + Prova

- [ ] **Dia 1 (03/08, seg):** Revisão dos **números exatos** que a FCC cobra — 5 domínios do OWASP SAMM, 10 bases legais da LGPD, 3 Flight Levels, técnicas de priorização (MoSCoW/RICE/WSJF), métricas de fluxo, fases da Lei 14.133, fases do ADM TOGAF.
- [ ] **Dia 2 (04/08, ter):** Revisão — Português (crase, regência, concordância, pontuação) e RLM (lógica + estatística), resolvendo questões FCC de fechamento.
- [ ] **Dia 3 (05/08, qua):** Revisão — caderneta de erros dos simulados; refazer as questões erradas explicando a justificativa de cada uma.
- [ ] **Dia 4 (06/08, qui):** Revisão — mapas mentais dos blocos de maior peso (Produto/Gestão, Software Assurance, IA, Contratações); leitura dos resumos próprios. Sem conteúdo novo.
- [ ] **Dia 5 (07/08, sex):** Descanso ativo — leitura leve dos resumos. Separar documentos: RG original, comprovante de inscrição impresso, 2 canetas pretas de material transparente. Dormir cedo.
- [ ] **Dia 6 (08/08, sáb):** Conferir local e trajeto da prova (Fortaleza/Juazeiro/Sobral conforme o Cartão Informativo). Revisão final apenas dos números. Descanso e sono cedo.
- [ ] **Dia 7 (09/08, dom):** **PROVA** — Analista Judiciário F06, período da manhã. Chegar 1h antes. Estratégia: 1ª passada (90 min) no que sabe rápido; 2ª passada (90 min) nos pesos pesados (produto, normativos, segurança, IA); redação por último (45 min); revisar a folha de respostas (15 min).

---

## 7. Conteúdo F06 por prioridade

### 7.1. Prioridade ALTA (maior ROI por hora) — domine primeiro
- **Gestão de Produtos Digitais:** visão de produto, ciclo de vida, backlog e priorização (MoSCoW, RICE, WSJF, Valor×Esforço), PO×PM, Release/MVP/MMF, feature flags/phased rollouts/dark launches, stakeholders.
- **Estratégia e Design:** Design Thinking (SCAMPER, JTBD, PRD), Product Discovery, UX/UI e e-MAG, OKRs, roadmaps.
- **Agilidade e Portfólio:** Scrum, Kanban (WIP), Flight Levels (1/2/3), PI Planning.
- **Métricas de produto:** Lead/Cycle Time, Throughput, CFD, NPS/CSAT, A/B, cohort, Outcomes×Outputs.
- **OWASP SAMM** (5 domínios), threat modeling, IAM/RBAC, SBOM.
- **IA aplicada:** IA generativa no SDLC, engenharia de prompt, RAG, agentes, ética/governança (CNJ 615).
- **LGPD** (Lei 13.709/2018) — letra de lei + Privacy by Design/Default + RIPD.
- **Contratações de TIC:** Lei 14.133/2021 (fases, modalidades, ETP/TR), normativos CNJ, gestão contratual.
- **Legislação CE:** Lei 9.826/1974, Lei 16.397/2017, Previdência CE.
- **Português** e **RLM com estatística**.

### 7.2. Prioridade MÉDIA — refresh dirigido
- Análise de Negócio e Requisitos (BPMN 2.0, user stories, DoD/DoR, gap analysis).
- Engenharia de Domínio (DDD estratégico, context mapping) e Modernização (Strangler Fig, API-led, dívida técnica, modelo TIME).
- Engenharia de Dados (Data Lake/DW/Lakehouse, dimensional, ETL/ELT, governança).
- RPA / Hyperautomation.
- Riscos de produto e FinOps.

### 7.3. Prioridade BAIXA — revisão rápida (você já tem base)
- Java e POO (sintaxe, exceções) — só relembrar o vocabulário em PT.
- Microsserviços, REST/eventos, Docker e Kubernetes — conceitual.
- DevOps/CI-CD e observabilidade — conceitual.
- Inglês técnico — leitura.

---

## 8. Recursos recomendados

### Plataformas e questões
- **TEC Concursos / Qconcursos:** filtrar por banca **FCC** + Analista de TI. Meta: resolver o máximo de questões de **Gestão de Projetos/Produtos, Engenharia de Software, Segurança e LGPD**.
- **Estratégia / Direção / Gran Cursos:** pacote específico para **TJCE 2026 – Analista TI** quando sair (já contemplando a retificação).

### Materiais por tema novo
- **Product Management:** "Inspired" e "Empowered" (Marty Cagan); material de Product Discovery; Canvas de Proposição de Valor (Osterwalder).
- **Agilidade em escala:** Flight Levels (Klaus Leopold); Scrum Guide 2020 (oficial, PT-BR); Kanban (David Anderson).
- **OWASP SAMM:** documento oficial do projeto OWASP SAMM v2 (gratuito).
- **IA aplicada / CNJ:** Resolução CNJ nº 615 (texto oficial) e recomendações do CNJ sobre IA no Judiciário.
- **Lei 14.133/2021:** texto da lei + resumos de contratações de TIC (e normativos do CNJ sobre governança/PDTIC).
- **LGPD:** Lei 13.709/2018 (leitura direta) + resumo de bases legais e agentes.
- **Português FCC:** Prof. Fernando Pestana / Décio Terror. **RLM:** Prof. Renato Borges / Sérgio Carvalho.

### Provas anteriores prioritárias (FCC, Analista de TI)
- TRT 13ª (PB) 2022 · TRT 18ª (GO) 2023 · TJ-AP 2019 · TRE-CE 2022 · TRE-PB 2023 · DPE-AM 2022 · DPE-RS 2022.
- Observação: como o conteúdo virou Product/IA, complemente com questões de **Gestão Ágil/Produtos** de bancas que já cobram o tema (mesmo fora da FCC), para reconhecimento de conceito.

---

## 9. Estratégia para a redação

**O quê:** dissertativo-argumentativo autoral, tema de interesse geral, ~20–30 linhas.

**Critérios (item 12 do edital):** TEMA 7,0 (recorte 2,0 + interpretação crítica dos textos de apoio 2,0 + progressão textual 3,0) · NORMA-PADRÃO 3,0 (propriedade vocabular 0,8 + coesão 1,6 + morfossintaxe 0,6).

### Estrutura recomendada
- **Introdução (3–4 linhas):** contextualização breve + tese clara + anúncio de 2 argumentos.
- **Desenvolvimento 1 e 2 (8–10 linhas cada):** tópico frasal + dados/exemplos institucionais + diálogo crítico com os textos de apoio.
- **Conclusão (4–5 linhas):** síntese + proposta de intervenção (agente + ação + meio + finalidade) **articulada aos argumentos**.

### Temas prováveis (2025–2026)
Regulação de IA generativa no serviço público · combate à desinformação · saúde mental no trabalho · inclusão e cotas no serviço público · cibersegurança e privacidade (LGPD) · transformação digital do Estado e exclusão digital · acesso à Justiça e processo eletrônico · sustentabilidade.

### Armadilhas FCC
Recuo de parágrafo com sinal especial; tangenciar o tema (zera); paráfrase sem crítica; proposta de intervenção solta; linguagem coloquial; menos de 8 linhas (zera).

**Cadência:** 1 redação por semana a partir da Semana 1, sempre autocorrigida pela rubrica acima (e, se possível, com correção externa).

---

## 10. Dia da prova (09/08/2026 — manhã)

- **Leve:** documento original com foto, comprovante de inscrição impresso, 2 canetas pretas de material transparente, água em garrafa transparente.
- **Não leve:** celular/smartwatch/calculadora/fone (ficam em local indicado). Chegue **1h antes** — acesso fecha pontualmente.
- **Durante (4h):** 0–5 min conferência; 5–95 min 1ª passada (o que sabe rápido: Java/BD/microsserviços/REST + conceitos diretos de produto); 95–185 min 2ª passada (pesos pesados: produto/gestão, OWASP SAMM, IA, LGPD, Lei 14.133, legislação CE); 185–230 min redação; 230–240 min revisão da folha.
- **Chute técnico FCC:** desconfie de "sempre/nunca/todos/nenhum"; prefira a alternativa mais próxima da definição literal do conceito; alternativa que mistura conceitos de áreas diferentes costuma estar errada.

---

## 11. Métricas e tracking semanal

Meta de % de acerto por bloco; preencha após cada simulado.

| Bloco | S1 (baseline) | S5 | S7 | S9 | S10 | Meta |
|---|---|---|---|---|---|---|
| Língua Portuguesa | __% | __% | __% | __% | __% | 75% |
| RLM + Estatística | __% | __% | __% | __% | __% | 70% |
| Legislação CE + PCD | __% | __% | __% | __% | __% | 80% |
| Gestão de Produtos (temas 1–3) | __% | __% | __% | __% | __% | 80% |
| Agilidade + Métricas (temas 4–5) | __% | __% | __% | __% | __% | 80% |
| Riscos/Qualidade + LGPD (tema 6) | __% | __% | __% | __% | __% | 80% |
| Domínio + SW Moderno + Java (7,12,13) | __% | __% | __% | __% | __% | 80% |
| Software Assurance (tema 8) | __% | __% | __% | __% | __% | 75% |
| IA aplicada (tema 9) | __% | __% | __% | __% | __% | 75% |
| Dados + RPA (temas 10–11) | __% | __% | __% | __% | __% | 75% |
| Contratações de TIC (tema 14) | __% | __% | __% | __% | __% | 80% |
| Inglês técnico | __% | __% | __% | __% | __% | 70% |
| Redação (nota /10) | _,_ | _,_ | _,_ | _,_ | _,_ | 7,5+ |

---

## 12. Riscos do plano e mitigação

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Subestimar os temas de produto por achar que "é só conceito" | ALTA | Tempo bloqueado para produto/gestão nas semanas 1–4, antes do conforto técnico |
| 18h/semana não cobrirem tudo | MÉDIA-ALTA | Priorização rígida (seção 7.1 primeiro); cortar revisão do que já domina |
| Português/RLM negligenciados | MÉDIA | Doses semanais fixas em dias úteis desde a Semana 1 |
| Ficar fora do corte da objetiva (redação não corrigida) | ALTA se descuidar | Foco brutal na CE (peso 3); redação semanal, mas a objetiva é o funil |
| Material desatualizado (cita ITIL/COBIT) | MÉDIA | Usar o conteúdo deste plano (pós-retificação) como referência; ignorar blocos que saíram |
| Edital/norma superveniente | BAIXA | Acompanhar o DJe-CE e o site da FCC semanalmente |

---

## 13. Checklist administrativo

- [ ] **Inscrição feita** (período 18/05 – 22/06/2026)
- [ ] **Pagamento da DAE** dentro do prazo
- [ ] **Foto enviada** no upload da inscrição
- [ ] **Cidade de prova** selecionada (Fortaleza / Juazeiro do Norte / Sobral)
- [ ] **Cargo:** F06 — Analista Judiciário – Ciência da Computação – TI Sistemas
- [ ] **Conferência de inscrição** no site da FCC
- [ ] **Cartão Informativo** (acompanhar e-mail e site nos dias que antecedem a prova)
- [ ] **Acompanhar o Diário da Justiça eletrônico do CE** para convocações e retificações

---

## 14. Mentalidade

O cargo F06 mudou de cara: virou **gestão de produto digital com base técnica**. Isso é uma vantagem para quem se prepara com método, porque **a maioria dos candidatos de TI vai estudar o que já gosta (código, infra) e chegar fraco em produto, IA aplicada e contratações** — justamente onde estão ~20 questões de peso 3.

Com ~18h/semana, a regra é: **cumprir o cronograma de produto/gestão e normativos primeiro**, revisar o técnico depois. A disciplina de fazer o que dá menos prazer (decorar bases da LGPD, mapear os 5 domínios do SAMM, entender Flight Levels) é o que separa quem entra no corte de quem fica de fora.

Boa preparação, Valdyr.

---

*Plano replanejado em 31/05/2026 a partir do Edital de Abertura do TJCE 2026 e da Retificação do conteúdo programático do cargo F06 (DJe nº 3786, 29/05/2026). Cronograma: 01/06 → 09/08/2026.*
