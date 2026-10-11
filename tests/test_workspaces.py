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