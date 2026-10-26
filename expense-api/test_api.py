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


def test_upload_csv_imports_rows_and_creates_new_merchants(client):
    csv_text = (
        "date,amount,merchant,category\n"
        "2026-10-14,350,Java House,Food\n"
        "2026-10-15,500,Uber,Transport\n"
        "2026-10-16,1500,KPLC,Bills\n"
        "2026-10-17,200,Naivas,Food\n"
        "2026-10-18,900,Spotify,Entertainment\n"
    )
    response = client.post(
        "/transactions/upload",
        files={"file": ("t.csv", csv_text, "text/csv")},
    )
    assert response.status_code == 200
    assert response.json() == {"imported": 5, "errors": []}

    # KPLC and Spotify did not exist before, so they must exist now.
    merchants = [m["name"] for m in client.get("/merchants").json()]
    assert "KPLC" in merchants
    assert "Spotify" in merchants


def test_upload_csv_reports_bad_rows_but_imports_good_ones(client):
    csv_text = (
        "date,amount,merchant,category\n"
        "2026-10-19,-40,Uber,Transport\n"      # line 2: negative amount
        "banana,100,Uber,Transport\n"          # line 3: bad date
        "2026-10-20,100,Uber,Transport\n"      # line 4: good
    )
    response = client.post(
        "/transactions/upload",
        files={"file": ("t.csv", csv_text, "text/csv")},
    )
    body = response.json()
    assert body["imported"] == 1
    assert [e["line"] for e in body["errors"]] == [2, 3]