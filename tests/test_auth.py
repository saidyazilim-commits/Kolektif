async def test_register_success(client):
    email = "example@example.com"
    response = await client.post("/users/register", json={"email": email, "password": "pytest-sifresi-1"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "hashed_password" not in data

async def test_register_duplicate_email(client):
    body = {"email": "example@example.com", "password": "pytest-sifresi-1"}

    first = await client.post("/users/register", json=body)
    assert first.status_code == 200

    second = await client.post("/users/register", json=body)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"