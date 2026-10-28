import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


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


@pytest.mark.parametrize("bad_name", ["", "   "])
async def test_create_workspace_rejects_invalid_name(client, owner_headers, bad_name):
    # 1. owner, geçersiz adla workspace açmayı dener
    response = await client.post("/workspaces/", json={"name": bad_name}, headers=owner_headers)
    assert response.status_code == 422, response.text

    # 2. hiçbir workspace oluşmadı
    response = await client.get("/workspaces/", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert response.json() == []


async def test_rename_workspace_rejects_whitespace_only_name(client, owner_headers):
    # 1. owner, workspace açar
    response = await client.post("/workspaces/", json={"name": "rol_testi"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # 2. owner, adı yalnızca boşlukla değiştirmeyi dener
    response = await client.patch(f"/workspaces/{ws_id}", json={"name": " "}, headers= owner_headers)
    assert response.status_code == 422, response.text

    # 3. ad değişmedi
    response = await client.get(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.json()["name"] == "rol_testi"


async def test_member_cannot_add_members(client, owner_headers, stranger_headers, third_headers):
    # 0. kullanıcı numaraları
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200, response.text
    stranger_id = response.json()["id"]
    response = await client.get("/users/me", headers=third_headers)
    assert response.status_code == 200, response.text
    third_id = response.json()["id"]

    # 1. sahip workspace oluşturur
    response = await client.post("/workspaces/", json={"name": "rol_testi"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # 2. sahip, yabancıyı "member" olarak ekler
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 200, response.text

    # 3. artık üye: workspace'i okuyabilir
    response = await client.get(f"/workspaces/{ws_id}", headers=stranger_headers)
    assert response.status_code == 200, response.text

    # 4. ama üye ekleyemez
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": third_id, "role": "member"}, headers=stranger_headers)
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Owner role required"

    # 5. üçüncü kişi hâlâ dışarıda
    response = await client.get(f"/workspaces/{ws_id}", headers=third_headers)
    assert response.status_code == 403, response.text


async def test_non_member_cannot_add_members(client, owner_headers, stranger_headers, third_headers):
    # owner, workspace açar
    response = await client.post("/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # third user information
    response = await client.get("/users/me", headers=third_headers)
    assert response.status_code == 200, response.text
    third_id = response.json()["id"]

    # 2. yabancı, third user "member" olarak ekleyemez
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": third_id, "role": "member"}, headers=stranger_headers)
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not a member of this workspace"


async def test_add_member_to_missing_workspace_returns_404(client, owner_headers, third_headers):
    # 1. third kullanıcının id'sini al
    response = await client.get("/users/me", headers=third_headers)
    assert response.status_code == 200, response.text
    third_id = response.json()["id"]

    # 2. var olmayan workspace'e üye eklemeyi dene (owner olarak)
    response = await client.post(f"/workspaces/{999999}/members", json={"user_id": third_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Workspace not found"


async def test_cannot_add_same_member_twice(client, owner_headers, stranger_headers):
    # 1. stranger'ın id'sini al
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200, response.text
    stranger_id = response.json()["id"]

    # 2. owner, workspace açar
    response = await client.post("/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # 3. owner, stranger'ı ilk kez ekler: başarılı
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 200, response.text

    # 4. owner, aynı kişiyi ikinci kez eklemeyi dener
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "User is already a member"


async def test_database_rejects_duplicate_membership(client, owner_headers, engine):
    # 1. owner'ın id'sini al
    response = await client.get("/users/me", headers=owner_headers)
    assert response.status_code == 200, response.text
    owner_id = response.json()["id"]

    # 2. owner workspace açar (owner üyeliği otomatik oluşur)
    response = await client.post("/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # 3. aynı (user_id, workspace_id) çiftini doğrudan SQL ile ikinci kez ekle
    with pytest.raises(IntegrityError):
        async with engine.begin() as connection:
            await connection.execute(
                text("INSERT INTO workspace_members (user_id, workspace_id, role, joined_at) VALUES (:u, :w, 'member', now())"),
                {"u": owner_id, "w": ws_id},
            )


async def test_invalid_role_is_rejected(client, owner_headers, stranger_headers):
    # 0. yabancının numarası
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200, response.text
    stranger_id = response.json()["id"]

    # 1. sahip workspace oluşturur
    response = await client.post("/workspaces/", json={"name": "rol_dogrulama"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # 2. sahip geçersiz bir rolle eklemeyi dener
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "superadmin"}, headers=owner_headers)
    assert response.status_code == 422, response.text

    # 3. yabancı hâlâ üye değil
    response = await client.get(f"/workspaces/{ws_id}", headers=stranger_headers)
    assert response.status_code == 403, response.text


async def test_owner_can_delete_workspace_and_its_boards(client, owner_headers):
    # 1-a. sahip workspace oluşturur
    response = await client.post("/workspaces/", json={"name": "workspace_silme_testi"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # 2. owner, aynı workspace ait board oluşturur
    response = await client.post(f"/workspaces/{ws_id}/boards", json={"name": "first_board"} ,headers=owner_headers)
    assert response.status_code == 200, response.text

    # 3. owner, workspace siler ve boardlar gider
    response = await client.delete(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.status_code == 204, response.text

    # 4. silinmiş workspace boards listeleme
    # Soru: “Silinmiş workspace’in board listesi 404 mü, neden?”
    # Cevap: workspace yok.
    response = await client.get(f"/workspaces/{ws_id}/boards", headers=owner_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Workspace not found"


async def test_member_cannot_delete_workspace(client, owner_headers, stranger_headers):
    # 1. owner, workspace oluşturur
    response = await client.post("/workspaces/", json={"name": "silme_testi"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]
    
    # 0. kullanıcı numaraları
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200, response.text  
    stranger_id = response.json()["id"]

    # 1-a. owner, yabancıyı "member" olarak ekler
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"} ,headers=owner_headers)
    assert response.status_code == 200, response.text

    # 2. member, workspace silemez
    response = await client.delete(f"/workspaces/{ws_id}", headers=stranger_headers)
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Owner role required"

    # 3. workspace hala duruyor mu
    response = await client.get(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "silme_testi"


async def test_non_member_cannot_delete_workspace(client, owner_headers, stranger_headers):
    # 1. sahip workspace oluşturur
    response = await client.post("/workspaces/", json={"name": "silme_testi"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # 2. yabancı workspace silemez
    response = await client.delete(f"/workspaces/{ws_id}", headers=stranger_headers)
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not a member of this workspace"

    # 3. workspace hala duruyor mu
    response = await client.get(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "silme_testi"


async def test_delete_missing_workspace_returns_404(client, owner_headers):
    
    # 1. owner, workspace siler ve 404 alır
    response = await client.delete(f"/workspaces/{999999}", headers=owner_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Workspace not found"


async def test_delete_workspace_does_not_affect_other_workspaces(client, owner_headers):
    # 1. owner, ilk workspace oluşturur
    response = await client.post(f"/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws1_id = response.json()["id"]

    # 2. owner, ikinci workspace oluşturur
    response = await client.post(f"/workspaces/", json={"name": "workspace_2"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws2_id = response.json()["id"]

    # owner, ilk workspace bir board ekler
    response = await client.post(f"/workspaces/{ws1_id}/boards", json={"name": "first_board"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    
    # owner, ikinci workspace bir board ekler
    response = await client.post(f"/workspaces/{ws2_id}/boards", json={"name": "second_board"}, headers=owner_headers)
    assert response.status_code == 200, response.text

    # owner, ilk workspace'i siler
    response = await client.delete(f"/workspaces/{ws1_id}", headers=owner_headers)
    assert response.status_code == 204, response.text

    # owner, ikinci workspace'in board listensinin 1 olduğunu doğrular
    response = await client.get(f"/workspaces/{ws2_id}/boards", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert len(response.json()) == 1


async def test_member_can_rename_workspace(client, owner_headers, stranger_headers):
    # owner, workspace açar
    response = await client.post(f"/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]
    # owner, workspace görür
    response = await client.get(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.status_code == 200, response.text

    # owner, stranger'ı member olarak ekler
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200, response.text
    stranger_id = response.json()["id"]

    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 200, response.text

    # stranger, workspace adı değiştirir
    response = await client.patch(f"/workspaces/{ws_id}", json={"name": "yeni_workspace_adi"}, headers=stranger_headers)
    assert response.status_code == 200, response.text

    # owner, GET ile aynı adı görür
    response = await client.get(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "yeni_workspace_adi"


async def test_owner_can_rename_workspace(client, owner_headers):
    # owner, workspace açar
    response = await client.post(f"/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]
    # owner, workspace görür
    response = await client.get(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.status_code == 200, response.text

    # owner, workspace adı değiştirir
    response = await client.patch(f"/workspaces/{ws_id}", json={"name": "yeni_workspace_adi"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "yeni_workspace_adi"


async def test_non_member_cannot_rename_workspace(client, owner_headers, stranger_headers):
    # owner, workspace açar
    response = await client.post(f"/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # stranger, workspace adı değiştirir
    response = await client.patch(f"/workspaces/{ws_id}", json={"name": "yeni_workspace_adi"}, headers=stranger_headers)
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not a member of this workspace"

    # owner, GET ile eski workspace adını doğrular
    response = await client.get(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.json()["name"] == "workspace_1"


async def test_rename_missing_workspace_returns_404(client, owner_headers):
    # 1. owner, workspace göremez ve 404 alır
    response = await client.patch(f"/workspaces/{999999}",json={"name": "herhangi_bir_ad"}, headers=owner_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Workspace not found"


async def test_rename_workspace_rejects_empty_name(client, owner_headers, stranger_headers):
    # owner, workspace açar
    response = await client.post(f"/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # owner, workspace ismini boş isim ile değştiremez
    response = await client.patch(f"/workspaces/{ws_id}", json={"name": ""}, headers= owner_headers)
    assert response.status_code == 422, response.text

    # owner, stranger'ı member olarak ekler
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200, response.text
    stranger_id = response.json()["id"]

    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 200, response.text

    # member, workspace isminni boş isim ile değiştiremez
    response = await client.patch(f"/workspaces/{ws_id}", json={"name": ""}, headers=stranger_headers)
    assert response.status_code == 422, response.text

    # owner ismin değişmediği görür
    response = await client.get(f"/workspaces/{ws_id}", headers=owner_headers)
    assert response.json()["name"] == "workspace_1"

    # member, ismin değişmediğini görür
    response = await client.get(f"/workspaces/{ws_id}", headers=stranger_headers)
    assert response.json()["name"] == "workspace_1"


async def test_get_missing_workspace_returns_404(client, owner_headers):
    # 1. owner olmayan workspace okuyamaz
    response = await client.get(f"/workspaces/{999999}", headers=owner_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Workspace not found"

async def test_add_nonexistent_user_returns_404(client, owner_headers):
    # 1. owner workspace açar
    response = await client.post("/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # 2. olmayan bir kullanıcıyı eklemeyi dener
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": 99999, "role": "member"}, headers=owner_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "User not found"