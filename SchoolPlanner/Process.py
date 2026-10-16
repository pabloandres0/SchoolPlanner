import json
import re
from datetime import date, datetime

from icalendar import Calendar


def split_summary(summary_raw):
    summary = summary_raw.strip()
    match = re.search(r"\[(.*?)\]$", summary)
    if match is None:
        return summary, "General"
    course_code = match.group(1)
    title = summary.replace(f"[{course_code}]", "").strip()
    return title, course_code


def format_start(start_value):
    if isinstance(start_value, datetime):   # check datetime first: it is also a date
        return start_value.isoformat()
    if isinstance(start_value, date):
        return start_value.strftime("%Y-%m-%d")
    return None


def clean_description(description_raw):
    return (
        description_raw.replace("\\n", "\n")
        .replace("\\,", ",")
        .strip()
    )


def procesar_calendario_canvas(
    archivo_ics_entrada,
    archivo_json_salida,
    palabra_clave=None,
    materia_filtro=None,
):
    with open(archivo_ics_entrada, "rb") as ics_file:
        calendar = Calendar.from_ical(ics_file.read())

    clean_events = []

    for component in calendar.walk():
        if component.name != "VEVENT":
            continue

        title, course_code = split_summary(str(component.get("summary", "")))

        if materia_filtro and materia_filtro.lower() not in course_code.lower():
            continue

        start_property = component.get("dtstart")
        start_text = format_start(start_property.dt if start_property else None)
        description = clean_description(str(component.get("description", "")))

        if (
            palabra_clave
            and palabra_clave.lower() not in title.lower()
            and palabra_clave.lower() not in description.lower()
        ):
            continue

        clean_events.append({
            "id_evento": str(component.get("uid", "")),
            "materia_codigo": course_code,
            "titulo": title,
            "fecha_inicio": start_text,
            "url_canvas": str(component.get("url", "")),
            "descripcion": description,
        })

    with open(archivo_json_salida, "w", encoding="utf-8") as json_file:
        json.dump(clean_events, json_file, ensure_ascii=False, indent=4)

    return len(clean_events)
