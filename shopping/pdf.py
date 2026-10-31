from fpdf import FPDF

OSCURO = (32, 36, 32)
VERDE = (46, 107, 62)
GRIS = (90, 96, 90)

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


class ListaPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*OSCURO)
        self.cell(0, 10, "RecipeBox", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*GRIS)
        self.cell(0, 7, "Lista de la compra", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)


def _latin(txt):
    return str(txt).encode("latin-1", "replace").decode("latin-1")


def cantidad(n, unit):
    if float(n).is_integer():
        n = int(n)
    unidad = (unit or "").strip()
    return f"{n} {unidad}".strip()


def dibujar(grupos, semana):
    doc = ListaPDF()
    doc.add_page()
    doc.set_font("Helvetica", "", 11)
    doc.set_text_color(*GRIS)
    doc.cell(0, 6, f"Semana del {semana}", new_x="LMARGIN", new_y="NEXT")
    doc.ln(3)
    if not grupos:
        doc.set_text_color(*OSCURO)
        doc.cell(0, 8, "No hay nada que comprar esta semana.", new_x="LMARGIN", new_y="NEXT")
        return doc
    for grupo in grupos:
        doc.set_font("Helvetica", "B", 13)
        doc.set_text_color(*VERDE)
        titulo = PASILLO.get(grupo["aisle"], grupo["aisle"])
        doc.cell(0, 8, _latin(titulo), new_x="LMARGIN", new_y="NEXT")
        doc.set_font("Helvetica", "", 11)
        doc.set_text_color(*OSCURO)
        for item in grupo["items"]:
            texto = f"[ ]  {item['name']}  -  {cantidad(item['quantity'], item['unit'])}"
            doc.cell(0, 7, _latin(texto), new_x="LMARGIN", new_y="NEXT")
        doc.ln(2)
    return doc
