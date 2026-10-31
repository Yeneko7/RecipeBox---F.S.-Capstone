def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["ok"] is True


def test_receta_sin_titulo(client):
    res = client.post("/recipes", json={})
    assert res.status_code == 400


def test_crud_receta_y_plan(client):
    alta = client.post("/recipes", json={"title": "Sopa", "servings": 2})
    assert alta.status_code == 201
    receta = alta.get_json()
    ing = client.post(
        f"/recipes/{receta['id']}/ingredients",
        json={"name": "calabaza", "quantity": 400, "unit": "g", "aisle": "verduras"},
    )
    assert ing.status_code == 201
    semana = client.get("/weeks/2026-10-19")
    assert semana.status_code == 200
    registro = client.post(
        "/weeks/2026-10-19/slots",
        json={"day": 0, "meal": "comida", "recipe_id": receta["id"], "servings": 2},
    )
    assert registro.status_code == 201
    assert registro.get_json()["title"] == "Sopa"
    raciones = client.put(f"/slots/{registro.get_json()['id']}", json={"servings": 4})
    assert raciones.status_code == 200
    assert raciones.get_json()["servings"] == 4
    bloqueo = client.delete(f"/recipes/{receta['id']}")
    assert bloqueo.status_code == 409
