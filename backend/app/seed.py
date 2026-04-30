import re
from datetime import date
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Phase, Week, StudyDay, Topic


def _parse_plano():
    # backend/app/../../plano.md = audifaz/plano.md (dev), /app/plano.md (container)
    plano_path = Path(__file__).parent.parent.parent / "plano.md"
    if not plano_path.exists():
        plano_path = Path("/app/plano.md")
    content = plano_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    phases = []
    weeks = []
    days = []

    current_phase = None
    current_week = None
    weekend_dates = None

    phase_re = re.compile(r'### FASE (\d+) [—-] "([^"]+)"')
    week_re = re.compile(r"### SEMANA (\d+) \| (\d{1,2})/(\d{2}) [–\-] (\d{1,2})/(\d{2}) \| (.+)")
    day_re = re.compile(r"- \*\*(\d{1,2})/(\d{2})([^*]*)\*\*[: ]+(.+)")
    weekend_re = re.compile(r"#### Fim de semana (\d{1,2})-(\d{1,2})/(\d{2})")
    sab_re = re.compile(r"- \*\*Sáb[^*]*\*\*[: ]+(.+)")
    dom_re = re.compile(r"- \*\*Dom[^*]*\*\*[: ]+(.+)")

    for line in lines:
        m = phase_re.search(line)
        if m:
            current_phase = {"numero": int(m.group(1)), "nome": m.group(2)}
            phases.append(current_phase)
            continue

        m = week_re.search(line)
        if m:
            wn = int(m.group(1))
            s_day, s_month = int(m.group(2)), int(m.group(3))
            e_day, e_month = int(m.group(4)), int(m.group(5))
            tema = m.group(6).strip()
            current_week = {
                "numero": wn,
                "fase": current_phase,
                "tema": tema,
                "data_inicio": date(2026, s_month, s_day),
                "data_fim": date(2026, e_month, e_day),
            }
            weeks.append(current_week)
            weekend_dates = None
            continue

        m = weekend_re.search(line)
        if m:
            d1, d2, month = int(m.group(1)), int(m.group(2)), int(m.group(3))
            weekend_dates = (date(2026, month, d1), date(2026, month, d2))
            continue

        m = sab_re.search(line)
        if m and weekend_dates and current_week:
            days.append({
                "data": weekend_dates[0],
                "tipo": "sabado",
                "topico": m.group(1).strip(),
                "week": current_week,
            })
            continue

        m = dom_re.search(line)
        if m and weekend_dates and current_week:
            days.append({
                "data": weekend_dates[1],
                "tipo": "domingo",
                "topico": m.group(1).strip(),
                "week": current_week,
            })
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
                d = date(2026, month_num, day_num)
                days.append({
                    "data": d,
                    "tipo": tipo,
                    "topico": description,
                    "week": current_week,
                })
            except ValueError:
                pass

    # Dedup by date (keep last occurrence)
    seen = {}
    for day in days:
        seen[day["data"]] = day
    days = list(seen.values())
    days.sort(key=lambda d: d["data"])

    return phases, weeks, days


async def seed_if_needed(db: AsyncSession):
    result = await db.execute(select(Phase))
    if result.scalars().first():
        return  # already seeded

    phases_data, weeks_data, days_data = _parse_plano()

    # Create phases
    phase_map = {}
    for p in phases_data:
        phase = Phase(numero=p["numero"], nome=p["nome"])
        db.add(phase)
        await db.flush()
        phase_map[p["numero"]] = phase

    # Create weeks
    week_map = {}
    for w in weeks_data:
        phase_num = w["fase"]["numero"] if w["fase"] else 1
        week = Week(
            phase_id=phase_map[phase_num].id,
            numero=w["numero"],
            data_inicio=w["data_inicio"],
            data_fim=w["data_fim"],
            tema=w["tema"],
        )
        db.add(week)
        await db.flush()
        week_map[w["numero"]] = week

    # Create days and topics
    for d in days_data:
        week_num = d["week"]["numero"] if d["week"] else 1
        week_obj = week_map.get(week_num)
        if not week_obj:
            continue
        day = StudyDay(
            week_id=week_obj.id,
            data=d["data"],
            tipo=d["tipo"],
        )
        db.add(day)
        await db.flush()

        topic = Topic(
            study_day_id=day.id,
            descricao=d["topico"],
            ordem=0,
        )
        db.add(topic)

    await db.commit()
