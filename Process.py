
import json
import re
from datetime import date, datetime
from icalendar import Calendar


def procesar_calendario_canvas(
    archivo_ics_entrada,
    archivo_json_salida,
    palabra_clave=None,
    materia_filtro=None,
):
    with open(archivo_ics_entrada, "rb") as f:
        cal = Calendar.from_ical(f.read())

    eventos_limpios = []

    for componente in cal.walk():
        if componente.name == "VEVENT":
            summary_raw = str(componente.get("summary", ""))

            match_materia = re.search(r"\[(.*?)\]$", summary_raw.strip())
            codigo_materia = (
                match_materia.group(1)
                if match_materia
                else "General"
            )
            titulo = (
                summary_raw.replace(f"[{codigo_materia}]", "").strip()
                if match_materia
                else summary_raw.strip()
            )

            if (
                materia_filtro
                and materia_filtro.lower() not in codigo_materia.lower()
            ):
                continue

            dtstart_obj = (
                componente.get("dtstart").dt
                if componente.get("dtstart")
                else None
            )
            dtend_obj = (
                componente.get("dtend").dt if componente.get("dtend") else None
            )

            if isinstance(dtstart_obj, datetime):
                fecha_inicio = dtstart_obj.isoformat()
            elif isinstance(dtstart_obj, date):
                fecha_inicio = dtstart_obj.strftime("%Y-%m-%d")
            else:
                fecha_inicio = None

            descripcion_raw = str(componente.get("description", ""))
            descripcion_limpia = (
                descripcion_raw.replace("\\n", "\n")
                .replace("\\,", ",")
                .strip()
            )

            if (
                palabra_clave
                and palabra_clave.lower() not in titulo.lower()
                and palabra_clave.lower() not in descripcion_limpia.lower()
            ):
                continue

            eventos_limpios.append({
                "id_evento": str(componente.get("uid", "")),
                "materia_codigo": codigo_materia,
                "titulo": titulo,
                "fecha_inicio": fecha_inicio,
                "url_canvas": str(componente.get("url", "")),
                "descripcion": descripcion_limpia,
            })

    with open(archivo_json_salida, "w", encoding="utf-8") as f_json:
        json.dump(eventos_limpios, f_json, ensure_ascii=False, indent=4)

    print(f"Éxito: {len(eventos_limpios)} eventos procesados y guardados.")