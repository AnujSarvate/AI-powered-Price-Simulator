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
