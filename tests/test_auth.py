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

    # 5. 40 karakter ama 80 bayt: bcrypt sınırını aşar
    response = await client.post("/users/register", json={"email": "turkce@example.com", "password": "ş" * 40})
    assert response.status_code == 422

async def test_login_with_overlong_password_does_not_crash(client):
    # 1. normal kullanıcı
    response = await client.post("/users/register", json={"email": "login@example.com", "password": "pytest-sifresi-1"})
    assert response.status_code == 200

    # 2. 100 karakterlik şifreyle giriş denemesi
    response = await client.post("/users/login", json={"email": "login@example.com", "password": "a" * 100})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

    # 2b. var olmayan e-postayla aynı cevap: kayıtlı olup olmadığı sızmıyor
    response = await client.post("/users/login", json={"email": "yok@example.com", "password": "a" * 100})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

    # 3. doğru şifre hâlâ çalışıyor
    response = await client.post("/users/login", json={"email": "login@example.com", "password": "pytest-sifresi-1"})
    assert response.status_code == 200