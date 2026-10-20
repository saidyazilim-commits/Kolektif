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

async def test_register_rejects_invalid_input(client):
    # 1. geçersiz e-posta
    response = await client.post("/users/register", json={"email": "gecersiz", "password": "pytest-sifresi-1"})
    assert response.status_code == 422

    # 2. çok kısa şifre
    response = await client.post("/users/register", json={"email": "kisa@example.com", "password": "abc"})
    assert response.status_code == 422

    # 3. aşırı uzun şifre
    response = await client.post("/users/register", json={"email": "uzun@example.com", "password": "a" * 100})
    assert response.status_code == 422

    # 4. reddedilen istek kullanıcı oluşturmadı: aynı e-posta geçerli şifreyle kaydolabilir
    response = await client.post("/users/register", json={"email": "kisa@example.com", "password": "pytest-sifresi-1"})
    assert response.status_code == 200