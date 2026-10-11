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