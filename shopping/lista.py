def clave(nombre, unidad):
    return ((nombre or "").strip().lower(), (unidad or "").strip().lower())


def sumar_lineas(lineas):
    cubos = {}
    for linea in lineas:
        k = (clave(linea["name"], linea["unit"])[0], clave(linea["name"], linea["unit"])[1], linea.get("aisle") or "otros")
        if k not in cubos:
            cubos[k] = 0.0
        cubos[k] += float(linea["quantity"])
    return [
        {"name": name, "unit": unit, "aisle": aisle, "quantity": round(qty, 2)}
        for (name, unit, aisle), qty in sorted(cubos.items())
        if qty > 0
    ]


def restar_despensa(lineas, despensa):
    stock = {}
    for item in despensa:
        k = clave(item["name"], item.get("unit", ""))
        stock[k] = stock.get(k, 0.0) + float(item.get("quantity") or 0)
    resultado = []
    for linea in lineas:
        k = clave(linea["name"], linea["unit"])
        hay = stock.get(k, 0.0)
        falta = float(linea["quantity"]) - hay
        if falta > 0.001:
            copia = dict(linea)
            copia["quantity"] = round(falta, 2)
            resultado.append(copia)
    return resultado


def agrupar_pasillo(lineas):
    grupos = {}
    for linea in lineas:
        pasillo = linea.get("aisle") or "otros"
        grupos.setdefault(pasillo, []).append(linea)
    return [{"aisle": pasillo, "items": items} for pasillo, items in sorted(grupos.items())]
