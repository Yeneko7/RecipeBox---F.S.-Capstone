from datetime import datetime, timedelta

PASILLO = {
    "verduras": "Verduras",
    "fruteria": "Fruteria",
    "carniceria": "Carniceria",
    "pescaderia": "Pescaderia",
    "lacteos": "Lacteos",
    "panaderia": "Panaderia",
    "despensa": "Despensa",
    "congelados": "Congelados",
    "bebidas": "Bebidas",
    "otros": "Otros",
}


def _esc(texto):
    return (
        (texto or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _lunes(week):
    partes = week.split("-")
    return datetime(int(partes[0]), int(partes[1]), int(partes[2]))


def _stamp(dia, hora, minuto):
    return dia.strftime("%Y%m%dT") + f"{hora:02d}{minuto:02d}00"


def _evento(uid, inicio, fin, titulo, descripcion=""):
    lineas = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTART:{inicio}",
        f"DTEND:{fin}",
        f"SUMMARY:{_esc(titulo)}",
    ]
    if descripcion:
        lineas.append(f"DESCRIPTION:{_esc(descripcion)}")
    lineas.append("END:VEVENT")
    return lineas


def construir(plan, grupos, shop_day, shop_hour):
    lunes = _lunes(plan["week_start"])
    lineas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//RecipeBox//ES",
        "CALSCALE:GREGORIAN",
    ]
    for slot in plan.get("slots") or []:
        dia = lunes + timedelta(days=int(slot["day"]))
        comida = slot.get("meal") == "cena"
        hora = 21 if comida else 14
        etiqueta = "Cena" if comida else "Comida"
        titulo = f"{etiqueta}: {slot.get('title') or 'menu'}"
        lineas.extend(
            _evento(
                f"slot-{slot.get('id')}@recipebox",
                _stamp(dia, hora, 0),
                _stamp(dia, hora + 1, 0),
                titulo,
            )
        )
    try:
        hh, mm = shop_hour.split(":")
        hora_c, min_c = int(hh), int(mm)
    except (TypeError, ValueError):
        hora_c, min_c = 11, 0
    dia_compra = lunes + timedelta(days=max(0, min(6, int(shop_day))))
    pasillos = ", ".join(
        PASILLO.get(g["aisle"], g["aisle"]) for g in (grupos or []) if g.get("items")
    )
    if not pasillos:
        pasillos = "nada que comprar"
    lineas.extend(
        _evento(
            f"compra-{plan['week_start']}@recipebox",
            _stamp(dia_compra, hora_c, min_c),
            _stamp(dia_compra, hora_c + 1, min_c),
            "Compra de la semana",
            f"Pasillos: {pasillos}",
        )
    )
    lineas.append("END:VCALENDAR")
    return "\r\n".join(lineas) + "\r\n"
