import os
import sys
import tempfile

import pytest

os.environ["RECIPEBOX_DB"] = tempfile.mktemp(suffix=".sqlite")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, db


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as c:
        yield c
