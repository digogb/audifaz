"""Parser e importador de planos de estudo em markdown.

Suporta dois formatos:

  - SEFAZ: cabeçalhos `### FASE N — "nome"`, `### SEMANA N | dd/mm - dd/mm | tema`,
    dias como `- **dd/mm**: descrição`, fim de semana `#### Fim de semana d1-d2/mm`
    seguido por `- **Sáb...**:` e `- **Dom...**:`.

  - TJCE: tabela de fases `| **F<N> — <nome>** | n–m | dd/mm – dd/mm | foco |`,
    semanas `### Semana N (dd/mm – dd/mm) — Tema`, e tarefas em checkbox
    `- [ ] **Dia N (dd/mm, ter):** descrição` ou `- [ ] **Dia N-M:** descrição`,
    além de tarefas sem dia explícito que viram tópicos do primeiro dia da semana.
"""

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class ParsedPhase:
    numero: int
    nome: str
    week_range: tuple[int, int] = (0, 0)  # inclusive; (0,0) = desconhecido


@dataclass
class ParsedDay:
    data: date
    tipo: str = "util"  # util|sabado|domingo|feriado|prova
    topics: list[str] = field(default_factory=list)


@dataclass
class ParsedWeek:
    numero: int
    data_inicio: date
    data_fim: date
    tema: str
    phase_numero: Optional[int] = None
    days: list[ParsedDay] = field(default_factory=list)


@dataclass
class ParsedPlan:
    phases: list[ParsedPhase] = field(default_factory=list)
    weeks: list[ParsedWeek] = field(default_factory=list)

    @property
    def total_days(self) -> int:
        return sum(len(w.days) for w in self.weeks)

    @property
    def total_topics(self) -> int:
        return sum(len(d.topics) for w in self.weeks for d in w.days)


# ---- detecção e despacho ----

def detect_format(content: str) -> str:
    if re.search(r'^### FASE \d+ [—\-] "', content, re.MULTILINE):
        return "sefaz"
    if re.search(r'^### Semana \d+ \(\d+/\d+', content, re.MULTILINE):
        return "tjce"
    return "unknown"


def parse_plan(content: str, default_year: int = 2026) -> ParsedPlan:
    fmt = detect_format(content)
    if fmt == "sefaz":
        return _parse_sefaz(content, default_year)
    if fmt == "tjce":
        return _parse_tjce(content, default_year)
    raise ValueError("Formato de plano não reconhecido (esperado SEFAZ ou TJCE)")


# ---- helpers ----

def _day_type(d: date) -> str:
    wd = d.weekday()
    if wd == 5:
        return "sabado"
    if wd == 6:
        return "domingo"
    return "util"


# ---- parser SEFAZ ----

def _parse_sefaz(content: str, year: int) -> ParsedPlan:
    phase_re = re.compile(r'### FASE (\d+) [—\-] "([^"]+)"')
    week_re = re.compile(r"### SEMANA (\d+) \| (\d{1,2})/(\d{2}) [–\-] (\d{1,2})/(\d{2}) \| (.+)")
    day_re = re.compile(r"- \*\*(\d{1,2})/(\d{2})([^*]*)\*\*[: ]+(.+)")
    weekend_re = re.compile(r"#### Fim de semana (\d{1,2})-(\d{1,2})/(\d{2})")
    sab_re = re.compile(r"- \*\*Sáb[^*]*\*\*[: ]+(.+)")
    dom_re = re.compile(r"- \*\*Dom[^*]*\*\*[: ]+(.+)")

    phases: list[ParsedPhase] = []
    weeks: list[ParsedWeek] = []
    current_phase: Optional[ParsedPhase] = None
    current_week: Optional[ParsedWeek] = None
    weekend_dates: Optional[tuple[date, date]] = None

    for line in content.split("\n"):
        m = phase_re.search(line)
        if m:
            current_phase = ParsedPhase(numero=int(m.group(1)), nome=m.group(2))
            phases.append(current_phase)
            continue

        m = week_re.search(line)
        if m:
            wn = int(m.group(1))
            s_day, s_month = int(m.group(2)), int(m.group(3))
            e_day, e_month = int(m.group(4)), int(m.group(5))
            tema = m.group(6).strip()
            current_week = ParsedWeek(
                numero=wn,
                data_inicio=date(year, s_month, s_day),
                data_fim=date(year, e_month, e_day),
                tema=tema,
                phase_numero=current_phase.numero if current_phase else None,
            )
            weeks.append(current_week)
            weekend_dates = None
            continue

        m = weekend_re.search(line)
        if m:
            d1, d2, month = int(m.group(1)), int(m.group(2)), int(m.group(3))
            weekend_dates = (date(year, month, d1), date(year, month, d2))
            continue

        m = sab_re.search(line)
        if m and weekend_dates and current_week:
            current_week.days.append(ParsedDay(
                data=weekend_dates[0], tipo="sabado", topics=[m.group(1).strip()],
            ))
            continue

        m = dom_re.search(line)
        if m and weekend_dates and current_week:
            current_week.days.append(ParsedDay(
                data=weekend_dates[1], tipo="domingo", topics=[m.group(1).strip()],
            ))
            continue

        m = day_re.search(line)
        if m and current_week:
            day_num = int(m.group(1))
            month_num = int(m.group(2))
            day_info = m.group(3)
            description = m.group(4).strip()

            if "FERIADO" in day_info:
                tipo = "feriado"
            elif "Sáb" in day_info:
                tipo = "sabado"
            elif "Dom" in day_info:
                tipo = "domingo"
            else:
                tipo = "util"
            if "PROVA" in description:
                tipo = "prova"

            try:
                d = date(year, month_num, day_num)
                current_week.days.append(ParsedDay(data=d, tipo=tipo, topics=[description]))
            except ValueError:
                pass

    # Dedup por data dentro de cada semana, manter última ocorrência
    for w in weeks:
        seen: dict[date, ParsedDay] = {}
        for d in w.days:
            seen[d.data] = d
        w.days = sorted(seen.values(), key=lambda x: x.data)

    return ParsedPlan(phases=phases, weeks=weeks)


# ---- parser TJCE ----

_TJCE_PHASE_RE = re.compile(
    r'\|\s*\*\*F(\d+)\s*[—\-]\s*([^*|]+?)\*\*\s*\|\s*(\d+)(?:\s*[–\-]\s*(\d+))?\s*\|',
    re.MULTILINE,
)
_TJCE_WEEK_RE = re.compile(
    r'^### Semana (\d+) \((\d+)/(\d+)\s*[–\-]\s*(\d+)/(\d+)\)\s*[—\-]\s*(.+?)\s*$',
    re.MULTILINE,
)
# checkboxes: `- [ ] **prefix:** ...` (espaço dentro de [ ] é opcional)
_TJCE_CB_RE = re.compile(r'^- \[[ x]?\]\s+\*\*([^*]+?)\*\*\s*:?\s*(.*)$', re.MULTILINE)
_TJCE_DATE_IN_PREFIX_RE = re.compile(r'\((\d{1,2})/(\d{1,2})')
_TJCE_DIA_RE = re.compile(r'^Dia\s+(\d+)(?:\s*[\-–]\s*(\d+))?', re.IGNORECASE)


def _parse_tjce(content: str, year: int) -> ParsedPlan:
    # Fases pela tabela em alguma seção (idealmente "## 5. Cronograma macro")
    phases: list[ParsedPhase] = []
    seen_numbers: set[int] = set()
    for m in _TJCE_PHASE_RE.finditer(content):
        n = int(m.group(1))
        if n in seen_numbers:
            continue
        nome = m.group(2).strip()
        start = int(m.group(3))
        end = int(m.group(4)) if m.group(4) else start
        phases.append(ParsedPhase(numero=n, nome=nome, week_range=(start, end)))
        seen_numbers.add(n)

    # Semanas + tarefas
    weeks: list[ParsedWeek] = []
    week_matches = list(_TJCE_WEEK_RE.finditer(content))
    for i, m in enumerate(week_matches):
        wn = int(m.group(1))
        s_day = int(m.group(2))
        s_month = int(m.group(3))
        e_day = int(m.group(4))
        e_month = int(m.group(5))
        tema = m.group(6).strip()

        section_start = m.end()
        section_end = week_matches[i + 1].start() if i + 1 < len(week_matches) else len(content)
        section_text = content[section_start:section_end]

        # Cortar em separador horizontal ou próxima seção `##`
        stop = re.search(r'^\s*(?:---|##\s)', section_text, re.MULTILINE)
        if stop:
            section_text = section_text[:stop.start()]

        try:
            week_start = date(year, s_month, s_day)
            week_end = date(year, e_month, e_day)
        except ValueError:
            continue

        # Inicializa todos os dias do calendário da semana
        days_map: dict[date, ParsedDay] = {}
        cur = week_start
        while cur <= week_end:
            days_map[cur] = ParsedDay(data=cur, tipo=_day_type(cur))
            cur += timedelta(days=1)

        # Processa cada checkbox como tópico, mapeando para o dia certo
        for cb in _TJCE_CB_RE.finditer(section_text):
            prefix = cb.group(1).strip().rstrip(":").strip()
            desc = cb.group(2).strip()
            if desc:
                full_desc = f"{prefix}: {desc}"
            else:
                full_desc = prefix
            assigned = False

            # 1. Data explícita "(dd/mm,"
            dm = _TJCE_DATE_IN_PREFIX_RE.search(prefix)
            if dm:
                d, mo = int(dm.group(1)), int(dm.group(2))
                try:
                    target = date(year, mo, d)
                    if target in days_map:
                        days_map[target].topics.append(full_desc)
                        assigned = True
                except ValueError:
                    pass

            # 2. "Dia N" ou "Dia N-M"
            if not assigned:
                dia_m = _TJCE_DIA_RE.match(prefix)
                if dia_m:
                    n = int(dia_m.group(1))
                    target = week_start + timedelta(days=n - 1)
                    if target in days_map:
                        days_map[target].topics.append(full_desc)
                        assigned = True

            # 3. Tarefa genérica da semana → primeiro dia
            if not assigned:
                days_map[week_start].topics.append(full_desc)

        # Resolve fase pela faixa de semanas
        phase_num: Optional[int] = None
        for p in phases:
            if p.week_range[0] <= wn <= p.week_range[1]:
                phase_num = p.numero
                break

        weeks.append(ParsedWeek(
            numero=wn,
            data_inicio=week_start,
            data_fim=week_end,
            tema=tema,
            phase_numero=phase_num,
            days=sorted(days_map.values(), key=lambda x: x.data),
        ))

    return ParsedPlan(phases=phases, weeks=weeks)


# ---- importador ----

async def import_plan(db, concurso_id: int, content: str, default_year: int = 2026) -> dict:
    """Substitui o plano do concurso pelo novo. Retorna contagens."""
    from sqlalchemy import select, delete
    from ..models import Phase, Week, StudyDay, Topic

    plan = parse_plan(content, default_year)
    if not plan.weeks:
        raise ValueError("Plano não tem nenhuma semana parseável")

    # Apaga em ordem topológica (sem CASCADE configurado)
    phase_ids = [r[0] for r in (await db.execute(
        select(Phase.id).where(Phase.concurso_id == concurso_id)
    )).all()]
    if phase_ids:
        week_ids = [r[0] for r in (await db.execute(
            select(Week.id).where(Week.phase_id.in_(phase_ids))
        )).all()]
        if week_ids:
            day_ids = [r[0] for r in (await db.execute(
                select(StudyDay.id).where(StudyDay.week_id.in_(week_ids))
            )).all()]
            if day_ids:
                await db.execute(delete(Topic).where(Topic.study_day_id.in_(day_ids)))
                await db.execute(delete(StudyDay).where(StudyDay.id.in_(day_ids)))
            await db.execute(delete(Week).where(Week.id.in_(week_ids)))
        await db.execute(delete(Phase).where(Phase.id.in_(phase_ids)))

    # Cria fases
    phase_map: dict[int, Phase] = {}
    for p in plan.phases:
        phase = Phase(concurso_id=concurso_id, numero=p.numero, nome=p.nome)
        db.add(phase)
        await db.flush()
        phase_map[p.numero] = phase

    # Fallback se o plano não declarou fases (cria uma genérica)
    default_phase: Optional[Phase] = None
    if not phase_map:
        default_phase = Phase(concurso_id=concurso_id, numero=1, nome="Plano")
        db.add(default_phase)
        await db.flush()

    counts = {"phases": len(plan.phases) or 1, "weeks": 0, "days": 0, "topics": 0}
    for w in plan.weeks:
        phase = phase_map.get(w.phase_numero) if w.phase_numero else None
        if not phase:
            # Sem fase declarada: usa a primeira ou a default
            phase = default_phase or next(iter(phase_map.values()), None)
        if not phase:
            continue

        week = Week(
            phase_id=phase.id,
            numero=w.numero,
            data_inicio=w.data_inicio,
            data_fim=w.data_fim,
            tema=w.tema,
        )
        db.add(week)
        await db.flush()
        counts["weeks"] += 1

        for d in w.days:
            day = StudyDay(week_id=week.id, data=d.data, tipo=d.tipo)
            db.add(day)
            await db.flush()
            counts["days"] += 1

            for i, t in enumerate(d.topics):
                db.add(Topic(study_day_id=day.id, descricao=t[:1000], ordem=i))
                counts["topics"] += 1

    await db.commit()
    return counts
