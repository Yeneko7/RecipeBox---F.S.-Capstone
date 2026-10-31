import os
import re

from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields
from sqlalchemy.exc import IntegrityError

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
_db_path = os.environ.get("RECIPEBOX_DB") or os.path.join(basedir, "app.sqlite")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + _db_path.replace("\\", "/")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

SEMANA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
COMIDAS = ("comida", "cena")
PASILLOS = (
    "verduras",
    "fruteria",
    "carniceria",
    "pescaderia",
    "lacteos",
    "panaderia",
    "despensa",
    "congelados",
    "bebidas",
    "otros",
)


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=True, nullable=False)
    servings = db.Column(db.Integer, nullable=False, default=2)
    notes = db.Column(db.Text, default="")
    ingredients = db.relationship(
        "Ingredient", backref="recipe", cascade="all, delete-orphan"
    )


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit = db.Column(db.String(40), default="")
    aisle = db.Column(db.String(40), default="otros")


class WeekPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_start = db.Column(db.String(10), unique=True, nullable=False)
    slots = db.relationship(
        "PlanSlot", backref="plan", cascade="all, delete-orphan"
    )


class PlanSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("week_plan.id"), nullable=False)
    day = db.Column(db.Integer, nullable=False)
    meal = db.Column(db.String(20), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    servings = db.Column(db.Integer, nullable=False, default=2)
    recipe = db.relationship("Recipe")


class IngredientSchema(ma.Schema):
    id = fields.Integer()
    recipe_id = fields.Integer()
    name = fields.String()
    quantity = fields.Float()
    unit = fields.String()
    aisle = fields.String()


class RecipeSchema(ma.Schema):
    id = fields.Integer()
    title = fields.String()
    servings = fields.Integer()
    notes = fields.String()
    ingredients = fields.List(fields.Nested(IngredientSchema))


class SlotSchema(ma.Schema):
    id = fields.Integer()
    day = fields.Integer()
    meal = fields.String()
    recipe_id = fields.Integer()
    servings = fields.Integer()
    title = fields.String()


recipe_schema = RecipeSchema()
recipes_schema = RecipeSchema(many=True)
ingredient_schema = IngredientSchema()
slot_schema = SlotSchema()


def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = os.environ.get("CORS_ORIGIN", "*")
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    return resp


@app.after_request
def after(resp):
    return _cors(resp)


@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def options(path):
    return ("", 204)


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _int(value, default, minimo=1, maximo=99):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimo, min(maximo, n))


def _recipe_dump(recipe):
    return recipe_schema.dump(
        {
            "id": recipe.id,
            "title": recipe.title,
            "servings": recipe.servings,
            "notes": recipe.notes or "",
            "ingredients": recipe.ingredients,
        }
    )


def _slot_dump(slot):
    return {
        "id": slot.id,
        "day": slot.day,
        "meal": slot.meal,
        "recipe_id": slot.recipe_id,
        "servings": slot.servings,
        "title": slot.recipe.title if slot.recipe else "",
    }


def _plan_or_new(week_start):
    plan = WeekPlan.query.filter_by(week_start=week_start).first()
    if plan is None:
        plan = WeekPlan(week_start=week_start)
        db.session.add(plan)
        db.session.commit()
    return plan


@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "api"})


@app.route("/recipes", methods=["GET"])
def list_recipes():
    rows = Recipe.query.order_by(Recipe.title).all()
    return jsonify(recipes_schema.dump(rows))


@app.route("/recipes", methods=["POST"])
def create_recipe():
    data = _body()
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "hace falta un titulo"}), 400
    recipe = Recipe(
        title=title,
        servings=_int(data.get("servings"), 2),
        notes=(data.get("notes") or "").strip(),
    )
    db.session.add(recipe)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "ya hay una receta con ese titulo"}), 409
    return jsonify(_recipe_dump(recipe)), 201


@app.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": "receta no encontrada"}), 404
    return jsonify(_recipe_dump(recipe))


@app.route("/recipes/<int:recipe_id>", methods=["PUT"])
def update_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": "receta no encontrada"}), 404
    data = _body()
    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "hace falta un titulo"}), 400
        recipe.title = title
    if "servings" in data:
        recipe.servings = _int(data.get("servings"), recipe.servings)
    if "notes" in data:
        recipe.notes = (data.get("notes") or "").strip()
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "ya hay una receta con ese titulo"}), 409
    return jsonify(_recipe_dump(recipe))


@app.route("/recipes/<int:recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": "receta no encontrada"}), 404
    if PlanSlot.query.filter_by(recipe_id=recipe.id).first():
        return jsonify({"error": "esa receta esta en el menu, quitala de la semana primero"}), 409
    db.session.delete(recipe)
    db.session.commit()
    return ("", 204)


@app.route("/recipes/<int:recipe_id>/ingredients", methods=["POST"])
def add_ingredient(recipe_id):
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": "receta no encontrada"}), 404
    data = _body()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "hace falta el nombre del ingrediente"}), 400
    aisle = (data.get("aisle") or "otros").strip().lower()
    if aisle not in PASILLOS:
        aisle = "otros"
    try:
        qty = float(data.get("quantity", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "cantidad no valida"}), 400
    if qty <= 0:
        return jsonify({"error": "la cantidad tiene que ser mayor que 0"}), 400
    item = Ingredient(
        recipe_id=recipe.id,
        name=name,
        quantity=qty,
        unit=(data.get("unit") or "").strip(),
        aisle=aisle,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(ingredient_schema.dump(item)), 201


@app.route("/ingredients/<int:item_id>", methods=["DELETE"])
def delete_ingredient(item_id):
    item = db.session.get(Ingredient, item_id)
    if item is None:
        return jsonify({"error": "ingrediente no encontrado"}), 404
    db.session.delete(item)
    db.session.commit()
    return ("", 204)


@app.route("/weeks/<week_start>", methods=["GET"])
def get_week(week_start):
    if not SEMANA_RE.match(week_start):
        return jsonify({"error": "la semana tiene que ser YYYY-MM-DD"}), 400
    plan = _plan_or_new(week_start)
    return jsonify(
        {
            "week_start": plan.week_start,
            "slots": [_slot_dump(s) for s in sorted(plan.slots, key=lambda s: (s.day, s.meal))],
        }
    )


@app.route("/weeks/<week_start>/slots", methods=["POST"])
def add_slot(week_start):
    if not SEMANA_RE.match(week_start):
        return jsonify({"error": "la semana tiene que ser YYYY-MM-DD"}), 400
    data = _body()
    recipe_id = data.get("recipe_id")
    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return jsonify({"error": "receta no encontrada"}), 404
    try:
        day = int(data.get("day"))
    except (TypeError, ValueError):
        return jsonify({"error": "dia no valido"}), 400
    if day < 0 or day > 6:
        return jsonify({"error": "el dia va de 0 (lunes) a 6 (domingo)"}), 400
    meal = (data.get("meal") or "").strip().lower()
    if meal not in COMIDAS:
        return jsonify({"error": "la comida es comida o cena"}), 400
    plan = _plan_or_new(week_start)
    existente = PlanSlot.query.filter_by(plan_id=plan.id, day=day, meal=meal).first()
    if existente:
        existente.recipe_id = recipe.id
        existente.servings = _int(data.get("servings"), recipe.servings)
        db.session.commit()
        return jsonify(_slot_dump(existente))
    slot = PlanSlot(
        plan_id=plan.id,
        day=day,
        meal=meal,
        recipe_id=recipe.id,
        servings=_int(data.get("servings"), recipe.servings),
    )
    db.session.add(slot)
    db.session.commit()
    return jsonify(_slot_dump(slot)), 201


@app.route("/slots/<int:slot_id>", methods=["PUT"])
def update_slot(slot_id):
    slot = db.session.get(PlanSlot, slot_id)
    if slot is None:
        return jsonify({"error": "registro no encontrado"}), 404
    data = _body()
    if "servings" in data:
        slot.servings = _int(data.get("servings"), slot.servings)
    db.session.commit()
    return jsonify(_slot_dump(slot))


@app.route("/slots/<int:slot_id>", methods=["DELETE"])
def delete_slot(slot_id):
    slot = db.session.get(PlanSlot, slot_id)
    if slot is None:
        return jsonify({"error": "registro no encontrado"}), 404
    db.session.delete(slot)
    db.session.commit()
    return ("", 204)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5001)), debug=True)
