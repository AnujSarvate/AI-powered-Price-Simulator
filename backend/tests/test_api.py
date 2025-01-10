def test_health(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_product_crud_and_simulation(client):
    p = client.post(
        "/v1/products",
        json={
            "sku": "MUG-001",
            "name": "Coffee Mug",
            "unit_cost": 4,
            "list_price": 12,
            "elasticity": 1.2,
            "q0": 80,
        },
    )
    assert p.status_code == 201
    product_id = p.json()["product_id"]

    s = client.post(
        "/v1/scenarios",
        json={
            "name": "Baseline",
            "horizon_weeks": 8,
            "product_ids": [product_id],
        },
    )
    assert s.status_code == 201
    scenario_id = s.json()["scenario_id"]

    run = client.post(f"/v1/scenarios/{scenario_id}/simulate", json={"mode": "deterministic"})
    assert run.status_code == 200
    body = run.json()
    assert body["total_profit"] > 0
    assert product_id in body["series"]
