from app import Ingredient, Recipe, app, db

# Nombres de platos de la seccion Spanish de
# github.com/dpapathanasiou/recipes (JSON, MIT).
# Cantidades para la lista de la compra: mias.

RECETAS = [
    {
        "title": "Tortilla de patatas",
        "servings": 4,
        "notes": "Cuajada o jugosa, a gusto.",
        "ingredients": [
            ("huevos", 6, "ud", "lacteos"),
            ("patatas", 700, "g", "verduras"),
            ("aceite de oliva", 80, "ml", "despensa"),
            ("cebolla", 1, "ud", "verduras"),
        ],
    },
    {
        "title": "Gambas al ajillo",
        "servings": 4,
        "notes": "El aceite, bien caliente.",
        "ingredients": [
            ("gambas", 400, "g", "pescaderia"),
            ("ajo", 6, "diente", "verduras"),
            ("guindilla", 1, "ud", "despensa"),
            ("aceite de oliva", 80, "ml", "despensa"),
            ("perejil", 1, "manojo", "verduras"),
        ],
    },
    {
        "title": "Pan con tomate",
        "servings": 4,
        "notes": "Pan tostado, tomate maduro.",
        "ingredients": [
            ("pan", 4, "rebanada", "panaderia"),
            ("tomate", 2, "ud", "verduras"),
            ("ajo", 1, "diente", "verduras"),
            ("aceite de oliva", 30, "ml", "despensa"),
        ],
    },
    {
        "title": "Arroz con pollo",
        "servings": 4,
        "notes": "El arroz, en el caldo del pollo.",
        "ingredients": [
            ("arroz", 320, "g", "despensa"),
            ("pollo", 800, "g", "carniceria"),
            ("tomate", 2, "ud", "verduras"),
            ("pimiento rojo", 1, "ud", "verduras"),
            ("guisante", 150, "g", "congelados"),
            ("aceite de oliva", 40, "ml", "despensa"),
        ],
    },
    {
        "title": "Judias verdes con tomate",
        "servings": 4,
        "notes": "De segundo o de guarnicion.",
        "ingredients": [
            ("judias verdes", 600, "g", "verduras"),
            ("tomate", 3, "ud", "verduras"),
            ("ajo", 2, "diente", "verduras"),
            ("cebolla", 1, "ud", "verduras"),
            ("aceite de oliva", 30, "ml", "despensa"),
        ],
    },
    {
        "title": "Sopa de ajo",
        "servings": 4,
        "notes": "Huevo poche al final.",
        "ingredients": [
            ("pan", 150, "g", "panaderia"),
            ("ajo", 6, "diente", "verduras"),
            ("huevo", 4, "ud", "lacteos"),
            ("pimenton", 1, "cucharadita", "despensa"),
            ("caldo", 1000, "ml", "despensa"),
            ("aceite de oliva", 40, "ml", "despensa"),
        ],
    },
]


def seed():
    with app.app_context():
        db.create_all()
        if Recipe.query.first() is not None:
            print("ya hay recetas, no toco la base")
            return
        for receta in RECETAS:
            row = Recipe(
                title=receta["title"],
                servings=receta["servings"],
                notes=receta["notes"],
            )
            db.session.add(row)
            db.session.flush()
            for name, qty, unit, aisle in receta["ingredients"]:
                db.session.add(
                    Ingredient(
                        recipe_id=row.id,
                        name=name,
                        quantity=qty,
                        unit=unit,
                        aisle=aisle,
                    )
                )
        db.session.commit()
        print("semilla lista:", Recipe.query.count(), "recetas")


if __name__ == "__main__":
    seed()
