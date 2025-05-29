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
