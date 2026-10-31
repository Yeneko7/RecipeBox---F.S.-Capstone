import json
import os
import urllib.error
import urllib.request

from flask import Flask, Response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

from ics import construir as dibujar_ics
from lista import agrupar_pasillo, restar_despensa, sumar_lineas
from pdf import dibujar

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "despensa.sqlite").replace("\\", "/")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:5001").rstrip("/")


class PantryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit = db.Column(db.String(40), default="")


class PantrySchema(Schema):
    id = fields.Integer()
    name = fields.String()
    quantity = fields.Float()
    unit = fields.String()


pantry_schema = PantrySchema()
pantry_many = PantrySchema(many=True)


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = os.environ.get("CORS_ORIGIN", "*")
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return resp


@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def options(path):
    return ("", 204)


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _pedir(path):
    url = API_BASE + path
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return {"error": err.reason, "status": err.code}
    except urllib.error.URLError:
        return {"error": "la API no responde", "status": 502}


def _lista_semana(week):
    plan = _pedir(f"/weeks/{week}")
    if "error" in plan:
        return plan, plan.get("status", 502)
    lineas = []
    for slot in plan.get("slots") or []:
        receta = _pedir(f"/recipes/{slot['recipe_id']}")
        if "error" in receta:
            continue
        base = receta.get("servings") or 1
        factor = (slot.get("servings") or base) / base
        for ing in receta.get("ingredients") or []:
            lineas.append(
                {
                    "name": ing["name"],
                    "unit": ing.get("unit") or "",
                    "aisle": ing.get("aisle") or "otros",
                    "quantity": float(ing["quantity"]) * factor,
                }
            )
    juntadas = sumar_lineas(lineas)
    despensa = pantry_many.dump(PantryItem.query.all())
    falta = restar_despensa(juntadas, despensa)
    return {"week_start": week, "groups": agrupar_pasillo(falta)}, 200


@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "shopping"})


@app.route("/pantry", methods=["GET"])
def list_pantry():
    return jsonify(pantry_many.dump(PantryItem.query.order_by(PantryItem.name).all()))


@app.route("/pantry", methods=["POST"])
def add_pantry():
    data = _body()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "hace falta el nombre"}), 400
    try:
        qty = float(data.get("quantity", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "cantidad no valida"}), 400
    if qty <= 0:
        return jsonify({"error": "la cantidad tiene que ser mayor que 0"}), 400
    item = PantryItem(name=name, quantity=qty, unit=(data.get("unit") or "").strip())
    db.session.add(item)
    db.session.commit()
    return jsonify(pantry_schema.dump(item)), 201


@app.route("/pantry/<int:item_id>", methods=["DELETE"])
def delete_pantry(item_id):
    item = db.session.get(PantryItem, item_id)
    if item is None:
        return jsonify({"error": "no esta en la despensa"}), 404
    db.session.delete(item)
    db.session.commit()
    return ("", 204)


@app.route("/list")
def shopping_list():
    week = request.args.get("week") or ""
    if len(week) != 10:
        return jsonify({"error": "pasa week=YYYY-MM-DD"}), 400
    payload, status = _lista_semana(week)
    return jsonify(payload), status


@app.route("/pdf")
def shopping_pdf():
    week = request.args.get("week") or ""
    if len(week) != 10:
        return jsonify({"error": "pasa week=YYYY-MM-DD"}), 400
    payload, status = _lista_semana(week)
    if status != 200:
        return jsonify(payload), status
    doc = dibujar(payload["groups"], week)
    raw = bytes(doc.output())
    return Response(
        raw,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=lista-{week}.pdf"},
    )


@app.route("/ics")
def calendario():
    week = request.args.get("week") or ""
    if len(week) != 10:
        return jsonify({"error": "pasa week=YYYY-MM-DD"}), 400
    plan = _pedir(f"/weeks/{week}")
    if "error" in plan:
        return jsonify(plan), plan.get("status", 502)
    payload, status = _lista_semana(week)
    if status != 200:
        return jsonify(payload), status
    shop_day = request.args.get("shop_day", "5")
    shop_hour = request.args.get("shop_hour") or "11:00"
    try:
        shop_day = int(shop_day)
    except (TypeError, ValueError):
        return jsonify({"error": "shop_day va de 0 (lunes) a 6 (domingo)"}), 400
    texto = dibujar_ics(plan, payload.get("groups") or [], shop_day, shop_hour)
    return Response(
        texto.encode("utf-8"),
        mimetype="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=semana-{week}.ics"},
    )


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5002)), debug=True)
