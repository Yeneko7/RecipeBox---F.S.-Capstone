import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lista import agrupar_pasillo, restar_despensa, sumar_lineas


def test_suma_mismo_producto():
    lineas = [
        {"name": "Cebolla", "unit": "ud", "aisle": "verduras", "quantity": 1},
        {"name": "cebolla", "unit": "ud", "aisle": "verduras", "quantity": 2},
    ]
    out = sumar_lineas(lineas)
    assert len(out) == 1
    assert out[0]["quantity"] == 3


def test_despensa_resta():
    lineas = [{"name": "huevo", "unit": "ud", "aisle": "lacteos", "quantity": 5}]
    despensa = [{"name": "huevo", "unit": "ud", "quantity": 2}]
    out = restar_despensa(lineas, despensa)
    assert out[0]["quantity"] == 3


def test_grupos_por_pasillo():
    grupos = agrupar_pasillo(
        [
            {"name": "pan", "unit": "ud", "aisle": "panaderia", "quantity": 1},
            {"name": "leche", "unit": "ml", "aisle": "lacteos", "quantity": 500},
        ]
    )
    nombres = [g["aisle"] for g in grupos]
    assert nombres == ["lacteos", "panaderia"]
