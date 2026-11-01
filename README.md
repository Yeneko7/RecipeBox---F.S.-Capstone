# RecipeBox — Weekly Meal Planner with Automatic Shopping List

The hard part of cooking at home is not finding recipes. It is deciding the week and turning that decision into a shopping list. Most people skip that second step, so they overbuy, throw food away, and repeat the same dishes. RecipeBox does three things:

1. **Plans the week** by assigning a recipe to each day.
2. **Builds the shopping list automatically:** It adds up the ingredients of every planned recipe and groups them by supermarket section (produce, dairy, pantry…), so the list follows the order of the store instead of the order of the recipes.
3. **Adjusts the list to the pantry:** What is already at home is subtracted from the final list, ensuring you never buy ingredients twice.

The true value is the last step: converting a weekly plan into a smart list you can easily take to the store. The list can be viewed directly on the web app, copied as plain text for your phone, or exported as a paginated, reader-friendly A4 PDF for printing.

---

## Architecture & Microservices

The application is built using a **decoupled microservices architecture** splitting core data from business computations:

* **`recipebox-api` (Port 5001):** The core database engine. Manages recipes, ingredients, and calendar slots. Handles full CRUD operations over REST/JSON.
* **`recipebox-shopping` (Port 5002):** The business logic and document processing engine. Calculates fractions, subtracts local pantry inventory, and handles multi-format exports.

---

## Technologies & Methodologies

* **Front End:** HTML5, CSS3 (Custom Flexbox & Grid, mobile-first target at 390px), JavaScript (ES6+), React 18 (Client-side compilation via Babel CDN, zero node-build step), Native Fetch API.
* **Back End:** Python 3, Flask, Flask-SQLAlchemy (ORM), Marshmallow (Object Serialisation), Gunicorn (Production server), SQLite.
* **External Tools:** `fpdf2` (Server-side automated PDF layout rendering), RFC-compliant iCalendar (`.ics`) raw text generation module.
* **Methodologies:** RESTful API Design, Microservices, Relational Database Constraints (Cascade deletions, Foreign Keys), Functional Math Calculations, Testing (Pytest), Mobile UX Design.

---

## Local Development Setup

### 1. Core API Service
```bash
cd api
python -m pip install -r requirements.txt
python seed.py
python app.py
```

### 2. Shopping & Export Service
```bash
cd shopping
python -m pip install -r requirements.txt
python app.py
```

### 3. Web Front End
```bash
cd web
python -m http.server 8080
```
Once all three terminals are running, open your browser at: **`http://127.0.0.1:8080`**

### Running Automated Tests
```bash
python -m pip install -r requirements-dev.txt
python -m pytest api/tests shopping/tests
```

---

## Cloud Deployment (Render Plan B)

Due to the ephemeral storage limitations of free cloud hosting platforms, the local SQLite database files will clear on server restarts. To automate data resilience without external infrastructure costs, make sure to apply the following **Build Command chain** in Render's dashboard settings:

```bash
# Set this as the Build Command for the recipebox-api Web Service:
pip install -r requirements.txt && python seed.py
```

---

## Live Deployments & Repository Links

* **Frontend Web App:** https://recipebox-capstone-web.onrender.com/
* **Core API Endpoint:** https://recipebox-api-capstone.onrender.com
* **Shopping Service Engine:** https://recipebox-shopping.onrender.com
* **GitHub Repository:** https://github.com/Yeneko7/RecipeBox---F.S.-Capstone

---

## Data Reference & Acknowledgments
* **Mock Dataset:** Recipe names and base structures for the automated seed module are adapted from the Spanish cuisine section of the public [dpapathanasiou/recipes](https://github.com/dpapathanasiou/recipes) dataset (JSON, MIT License). Metric units and grocery quantities have been manually customized for kitchen optimization.
