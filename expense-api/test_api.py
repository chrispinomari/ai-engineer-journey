import pytest
from fastapi.testclient import TestClient

import main
from setup_db import create_database


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Setup before each test: build a fresh, throwaway database.
    db_file = str(tmp_path / "test.db")
    create_database(db_file)
    monkeypatch.setattr(main, "DB_PATH", db_file)
    return TestClient(main.app)


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200


def test_list_categories(client):
    response = client.get("/categories")
    assert response.status_code == 200
    assert len(response.json()) == 4


def test_filter_by_category(client):
    response = client.get("/transactions?category=Food")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_add_transaction(client):
    new_tx = {"date": "2026-10-15", "amount": 300,
              "merchant_id": 1, "category_id": 1}
    response = client.post("/transactions", json=new_tx)
    assert response.status_code == 201
    assert response.json()["amount"] == 300


def test_negative_amount_rejected(client):
    bad_tx = {"date": "2026-10-15", "amount": -50,
              "merchant_id": 1, "category_id": 1}
    response = client.post("/transactions", json=bad_tx)
    assert response.status_code == 422


def test_unknown_merchant_gives_404(client):
    tx = {"date": "2026-10-15", "amount": 300,
          "merchant_id": 99, "category_id": 1}
    response = client.post("/transactions", json=tx)
    assert response.status_code == 404


def test_spending_by_merchant_is_sorted_highest_first(client):
    response = client.get("/spending/by-merchant")
    totals = [row["total"] for row in response.json()]
    assert totals == sorted(totals, reverse=True)


def test_spending_by_merchant_tie_is_alphabetical(client):
    response = client.get("/spending/by-merchant")
    top = response.json()[0]
    assert top["merchant"] == "Java House"
    assert top["total"] == 1250