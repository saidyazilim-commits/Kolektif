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