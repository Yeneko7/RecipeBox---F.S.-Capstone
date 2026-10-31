import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ics import construir


def test_comida_a_las_14_y_compra_el_sabado():
    plan = {
        "week_start": "2026-10-19",
        "slots": [
            {"id": 1, "day": 0, "meal": "comida", "title": "Salmorejo cordobes"},
            {"id": 2, "day": 0, "meal": "cena", "title": "Lentejas guisadas"},
        ],
    }
    grupos = [{"aisle": "carniceria", "items": [{"name": "jamon"}]}]
    texto = construir(plan, grupos, 5, "11:00")
    assert texto.startswith("BEGIN:VCALENDAR\r\n")
    assert "SUMMARY:Comida: Salmorejo cordobes\r\n" in texto
    assert "DTSTART:20261019T140000\r\n" in texto
    assert "DTSTART:20261019T210000\r\n" in texto
    assert "SUMMARY:Compra de la semana\r\n" in texto
    assert "DTSTART:20261024T110000\r\n" in texto
    assert "Carniceria" in texto
    datetime(2026, 10, 19)
