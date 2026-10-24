from sqlalchemy import text


async def test_stranger_cannot_create_board(client, owner_headers, stranger_headers):
    # 1. sahip workspace oluşturur (test_workspaces'teki 1. adımın aynısı)
    response = await client.post("/workspaces/", json={"name": "board_test_ws"}, headers=owner_headers)
    assert response.status_code == 200
    ws_id = response.json()["id"]

    # 2. sahip board oluşturur
    response = await client.post(f"/workspaces/{ws_id}/boards", json={"name": "first_board"}, headers=owner_headers)
    assert response.status_code == 200

    # 3. yabancı board oluşturamaz
    response = await client.post(f"/workspaces/{ws_id}/boards", json={"name": "sizma"}, headers=stranger_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this workspace"

    # 4. yabancı board listesini göremez
    response = await client.get(f"/workspaces/{ws_id}/boards", headers=stranger_headers)
    assert response.status_code == 403

    # 5. sahip listeyi görür, listede tam 1 board var
    response = await client.get(f"/workspaces/{ws_id}/boards", headers=owner_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

async def test_deleting_board_removes_columns_and_tasks(client, owner_headers, column_id, engine):
    # 0. sahibin workspace ve board numarası
    response = await client.get("/workspaces/", headers=owner_headers)
    assert response.status_code == 200
    ws_id = response.json()[0]["id"]
    response = await client.get(f"/workspaces/{ws_id}/boards", headers=owner_headers)
    assert response.status_code == 200
    board_id = response.json()[0]["id"]

    # 1. kolonun içine bir task koyuyoruz
    response = await client.post(f"/columns/{column_id}/tasks", json={"title": "t1", "position": 0}, headers=owner_headers)
    assert response.status_code == 200

    # 2. owner board'u siler
    response = await client.delete(f"/boards/{board_id}", headers=owner_headers)
    assert response.status_code == 204

    # 3. board artık yok
    response = await client.get(f"/boards/{board_id}/columns", headers=owner_headers)
    assert response.status_code == 404

    # 4. altındaki kolon ve task da gitti
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT count(*) FROM board_columns"))
        column_count = result.scalar()
        result = await connection.execute(text("SELECT count(*) FROM tasks"))
        task_count = result.scalar()

    assert column_count == 0
    assert task_count == 0

async def test_member_cannot_delete_board(client, owner_headers, stranger_headers, column_id):
    # 0. numaralar
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200
    stranger_id = response.json()["id"]
    response = await client.get("/workspaces/", headers=owner_headers)
    assert response.status_code == 200
    ws_id = response.json()[0]["id"]
    response = await client.get(f"/workspaces/{ws_id}/boards", headers=owner_headers)
    assert response.status_code == 200
    board_id = response.json()[0]["id"]

    # 1. owner, yabancıyı "member" olarak ekler
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 200

    # 2. member board'u silemez
    response = await client.delete(f"/boards/{board_id}", headers=stranger_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Owner role required"

    # 3. board hâlâ yerinde
    response = await client.get(f"/workspaces/{ws_id}/boards", headers=owner_headers)
    assert len(response.json()) == 1

async def test_owner_can_delete_column_and_its_tasks(client, owner_headers, column_id):
    # 1. owner yeni kolona yeni bir task ekler
    response = await client.post(f"/columns/{column_id}/tasks", json={"title": "new_task", "position": 0}, headers=owner_headers)
    assert response.status_code == 200
    task_id = response.json()["id"]
    # 2. owner kolonu siler
    response = await client.delete(f"/columns/{column_id}", headers=owner_headers)
    assert response.status_code == 204
    # 3-a. kolon silinince görev de gider
    response = await client.delete(f"/tasks/{task_id}", headers=owner_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found!"
    

async def test_non_member_cannot_delete_column(client, owner_headers, stranger_headers, column_id):
    # 1. yabancı kolon silemez 
    response = await client.delete(f"/columns/{column_id}", headers=stranger_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this workspace"
    # 2. kolon hala var mı?
    response = await client.post(f"/columns/{column_id}/tasks", json={"title": "trial_title", "position": 0} ,headers=owner_headers)
    assert response.status_code == 200

async def test_member_cannot_delete_column(client, owner_headers, stranger_headers, column_id):
    # 0. numaralar
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200
    stranger_id = response.json()["id"]
    response = await client.get("/workspaces/", headers=owner_headers)
    assert response.status_code == 200
    ws_id = response.json()[0]["id"]
    # 1. owner, yabancıyı "member" olarak ekler
    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"} ,headers=owner_headers)
    assert response.status_code == 200
    # 2. member kolon silemez
    response = await client.delete(f"/columns/{column_id}", headers=stranger_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Owner role required"

async def test_delete_missing_column_returns_404(client, owner_headers):
    # 1. owner, olmayan kolonu siler
    response = await client.delete(f"/columns/{99999}", headers=owner_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Column not found"

async def test_delete_column_only_affects_that_columns_board(client, owner_headers, column_id):
    response = await client.get("/workspaces/", headers=owner_headers)
    assert response.status_code == 200
    ws_id = response.json()[0]["id"]
    # owner workspace'inde ikinci board oluşturma
    response = await client.post(f"/workspaces/{ws_id}/boards", json={"name": "second_board"} ,headers=owner_headers)
    assert response.status_code == 200, response.text
    board_id = response.json()["id"]

    # ikinci boarda kolon ekleme
    response = await client.post(f"/boards/{board_id}/columns", json={"name": "second_board_column", "position": 0}, headers=owner_headers)
    assert response.status_code == 200, response.text
    board_column_id = response.json()["id"]

    # ikinci boardun kolonunu silme
    response = await client.delete(f"/columns/{board_column_id}", headers=owner_headers)
    assert response.status_code == 204, response.text

    # ilk boarda task ekleme
    response = await client.post(f"/columns/{column_id}/tasks", json={"title": "new_task", "position": 0}, headers=owner_headers)
    assert response.status_code == 200, response.text

    # silinen ikinci boardun kolonuna task ekleme
    response = await client.post(f"/columns/{board_column_id}/tasks", json={"title": "silinen_kolon_taski", "position": 0}, headers=owner_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Column not found!"

async def test_member_can_rename_board(client, owner_headers, stranger_headers):
    # owner, workspace açar
    response = await client.post(f"/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # owner, workspace'te board oluşturma
    response = await client.post(f"/workspaces/{ws_id}/boards", json={"name": "first_board"} ,headers=owner_headers)
    assert response.status_code == 200, response.text
    board_id = response.json()["id"]

    # owner, stranger'ı member olarak ekler
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200, response.text
    stranger_id = response.json()["id"]

    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 200, response.text

    # stranger, workspace'in board'unun adı değiştirir
    response = await client.patch(f"/boards/{board_id}", json={"name": "yeni_board_adi"}, headers=stranger_headers)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "yeni_board_adi"

async def test_non_member_cannot_rename_board(client, owner_headers, stranger_headers):
    # owner, workspace açar
    response = await client.post(f"/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # owner, workspace'te board oluşturma
    response = await client.post(f"/workspaces/{ws_id}/boards", json={"name": "first_board"} ,headers=owner_headers)
    assert response.status_code == 200, response.text
    board_id = response.json()["id"]


    # stranger, workspace'in board'unun adı değiştiremez
    response = await client.patch(f"/boards/{board_id}", json={"name": "yeni_board_adi"}, headers=stranger_headers)
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not a member of this workspace"

    # owner, board listesine bakar
    response = await client.get(f"/workspaces/{ws_id}/boards", headers=owner_headers)
    assert response.status_code == 200, response.text
    names = [b["name"] for b in response.json()]
    assert "first_board" in names

async def test_rename_missing_board_returns_404(client, owner_headers):
    # 1. owner, olmayan kolonun ismini değiştiremez
    response = await client.patch(f"/boards/{99999}", json={"name": "not_exist_column"} ,headers=owner_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Board not found"

async def test_rename_board_rejects_empty_name(client, owner_headers, stranger_headers):
    # owner, workspace açar
    response = await client.post(f"/workspaces/", json={"name": "workspace_1"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()["id"]

    # owner, workspace'te board oluşturma
    response = await client.post(f"/workspaces/{ws_id}/boards", json={"name": "first_board"} ,headers=owner_headers)
    assert response.status_code == 200, response.text
    board_id = response.json()["id"]


    # owner, board ismini boş isim ile değştiremez
    response = await client.patch(f"/boards/{board_id}", json={"name": ""}, headers= owner_headers)
    assert response.status_code == 422, response.text

    # owner, stranger'ı member olarak ekler
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200, response.text
    stranger_id = response.json()["id"]

    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 200, response.text

    # member, board ismini boş isim ile değiştiremez
    response = await client.patch(f"/boards/{board_id}", json={"name": ""}, headers=stranger_headers)
    assert response.status_code == 422, response.text

    # owner, board listesine bakar
    response = await client.get(f"/workspaces/{ws_id}/boards", headers=owner_headers)
    assert response.status_code == 200, response.text
    names = [b["name"] for b in response.json()]
    assert "first_board" in names

async def test_member_can_rename_column(client, owner_headers, stranger_headers, column_id):

    # workspace numarası
    response = await client.get("/workspaces/", headers=owner_headers)
    assert response.status_code == 200, response.text
    ws_id = response.json()[0]["id"]

    # owner, stranger'ı member olarak ekler
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200, response.text
    stranger_id = response.json()["id"]

    response = await client.post(f"/workspaces/{ws_id}/members", json={"user_id": stranger_id, "role": "member"}, headers=owner_headers)
    assert response.status_code == 200, response.text
    
    # yabancı kolonun adını değiştirir
    response = await client.patch(f"/columns/{column_id}", json={"name": "renamed_column"}, headers=stranger_headers)
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "renamed_column"

async def test_non_member_cannot_rename_column(client, owner_headers, stranger_headers, column_id):
    # yabancı kolonun adını değiştiremez
    response = await client.patch(f"/columns/{column_id}", json={"name": "renamed_column"}, headers=stranger_headers)
    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not a member of this workspace"

async def test_rename_missing_column_returns_404(client, owner_headers):
    # 1. owner, olmayan kolonun ismini değiştiremez
    response = await client.patch(f"/columns/{99999}", json={"name": "not_exist_column"} ,headers=owner_headers)
    assert response.status_code == 404, response.text
    assert response.json()["detail"] == "Column not found"

async def test_rename_column_rejects_empty_name(client, owner_headers, column_id):
    # owner, kolon ismini boş isim ile değiştiremez
    response = await client.patch(f"/columns/{column_id}", json={"name": ""}, headers=owner_headers)
    assert response.status_code == 422, response.text

