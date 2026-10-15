async def test_stranger_cannot_touch_tasks(client, owner_headers, stranger_headers, column_id):
    # 1. sahip task oluşturur
    response = await client.post(f"/columns/{column_id}/tasks", json={"title": "t1", "position": 0}, headers=owner_headers)
    assert response.status_code == 200
    task_id = response.json()["id"]

    # 2. yabancı task oluşturamaz
    response = await client.post(f"/columns/{column_id}/tasks", json={"title": "sizma", "position": 1}, headers=stranger_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this workspace"

    # 3. yabancı task listesini göremez
    response = await client.get(f"/columns/{column_id}/tasks", headers=stranger_headers)
    assert response.status_code == 403

    # 4. yabancı task silemez
    response = await client.delete(f"/tasks/{task_id}", headers=stranger_headers)
    assert response.status_code == 403

    # 4b. yabancı task'ı güncelleyemez
    response = await client.patch(f"/tasks/{task_id}", json={"title": "hack"}, headers=stranger_headers)
    assert response.status_code == 403

    # 5. sahip listeyi görür, tam 1 task var (silme denemesi task'ı silmedi)
    response = await client.get(f"/columns/{column_id}/tasks", headers=owner_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "t1"

async def test_cannot_move_task_to_foreign_column(client, owner_headers, stranger_headers, column_id, foreign_column_id):
    # 1. sahip kendi kolonunda task oluşturur
    response = await client.post(f"/columns/{column_id}/tasks", json={"title": "t1", "position": 0}, headers=owner_headers)
    assert response.status_code == 200
    task_id = response.json()["id"]

    # 2. sahip task'ı yabancının kolonuna taşımayı dener
    response = await client.patch(f"/tasks/{task_id}", json={"column_id": foreign_column_id}, headers=owner_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this workspace"

    # 3. task hâlâ sahibin kolonunda
    response = await client.get(f"/columns/{column_id}/tasks", headers=owner_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

    # 4. yabancının kolonuna hiçbir şey girmedi
    response = await client.get(f"/columns/{foreign_column_id}/tasks", headers=stranger_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0

async def test_cannot_assign_non_member(client, owner_headers, stranger_headers, column_id):
    # 0. yabancının kullanıcı numarası
    response = await client.get("/users/me", headers=stranger_headers)
    assert response.status_code == 200
    stranger_id = response.json()["id"]

    # 1. sahip, task oluştururken üye olmayanı atamayı dener
    response = await client.post(f"/columns/{column_id}/tasks", json={"title": "t1", "position": 0, "assignee_id": stranger_id}, headers=owner_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not a member of this workspace"

    # 2. sahip, atamasız bir task oluşturur
    response = await client.post(f"/columns/{column_id}/tasks", json={"title": "t2", "position": 1}, headers=owner_headers)
    assert response.status_code == 200
    task_id = response.json()["id"]

    # 3. sahip, sonradan üye olmayanı atamayı dener
    response = await client.patch(f"/tasks/{task_id}", json={"assignee_id": stranger_id}, headers=owner_headers)
    assert response.status_code == 403

    # 4. sahip listeyi çeker
    response = await client.get(f"/columns/{column_id}/tasks", headers=owner_headers)
    assert len(response.json()) == 1
    assert response.json()[0]["assignee_id"] is None