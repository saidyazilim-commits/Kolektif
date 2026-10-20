import pytest
from sqlalchemy import text

async def test_stranger_cannot_read_workspace(client, owner_headers, stranger_headers):
    # 1. sahip workspace oluşturur
    response = await client.post("/workspaces/", json={"name": "workspace_test"}, headers=owner_headers)
    assert response.status_code == 200
    ws_id = response.json()["id"]

    # 2. sahip kendi workspace'ini okuyabilir
    response = await client.get(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.status_code == 200

    # 3. yabancı okuyamaz
    response = await client.get(f"/workspaces/{ws_id}", headers=stranger_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this workspace"

    # 4. header yok
    response = await client.get(f"/workspaces/{ws_id}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

async def test_workspace_creation_is_atomic(client, owner_headers, engine, monkeypatch):
    # 1. üyelik nesnesi oluşturmayı bozuyoruz, ikinci adım patlasın
    def broken_member(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.api.v1.workspaces.WorkspaceMember", broken_member)

    # 2. istek patlar
    with pytest.raises(RuntimeError):
        await client.post("/workspaces/", json={"name": "yarim_kalan"}, headers=owner_headers)

    # 3. veritabanında sahipsiz workspace kalmamalı
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT count(*) FROM workspaces"))
        count = result.scalar()

    assert count == 0

async def test_member_cannot_add_members(client, owner_headers, stranger_headers, third_headers):
    # 0. kullanıcı numaraları
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200
    stranger_id = response.json()["id"]
    response = await client.get("/users/me", headers=third_headers)
    assert response.status_code == 200
    third_id = response.json()["id"]

    # 1. sahip workspace oluşturur
    response = await client.post("/workspaces/", json={"name": "rol_testi"}, headers=owner_headers)
    assert response.status_code == 200
    ws_id = response.json()["id"]

    # 2. sahip, yabancıyı "member" olarak ekler
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 200

    # 3. artık üye: workspace'i okuyabilir
    response = await client.get(f"/workspaces/{ws_id}", headers=stranger_headers)
    assert response.status_code == 200

    # 4. ama üye ekleyemez
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": third_id, "role": "member"}, headers=stranger_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not the owner of this workspace"

    # 5. üçüncü kişi hâlâ dışarıda
    response = await client.get(f"/workspaces/{ws_id}", headers=third_headers)
    assert response.status_code == 403

async def test_invalid_role_is_rejected(client, owner_headers, stranger_headers):
    # 0. yabancının numarası
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200
    stranger_id = response.json()["id"]

    # 1. sahip workspace oluşturur
    response = await client.post("/workspaces/", json={"name": "rol_dogrulama"}, headers=owner_headers)
    assert response.status_code == 200
    ws_id = response.json()["id"]

    # 2. sahip geçersiz bir rolle eklemeyi dener
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "superadmin"}, headers=owner_headers)
    assert response.status_code == 422

    # 3. yabancı hâlâ üye değil
    response = await client.get(f"/workspaces/{ws_id}", headers=stranger_headers)
    assert response.status_code == 403