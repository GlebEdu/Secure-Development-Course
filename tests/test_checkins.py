class TestCheckinsCRUD:
    """Тесты CRUD операций для отметок"""

    def test_create_checkin_success(self, client, sample_habit, auth_headers):
        """Тест успешного создания отметки"""
        checkin_data = {
            "habit_id": sample_habit["id"],
            "checkin_date": "2024-10-15",
            "completed": True,
        }
        response = client.post("/checkins", json=checkin_data, headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["habit_id"] == sample_habit["id"]
        assert body["checkin_date"] == "2024-10-15"
        assert body["completed"] is True

    def test_create_checkin_habit_not_found(self, client, auth_headers):
        """Тест создания отметки для несуществующей привычки"""
        checkin_data = {
            "habit_id": 999,
            "checkin_date": "2024-10-15",
            "completed": True,
        }
        response = client.post("/checkins", json=checkin_data, headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Habit not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body

    def test_get_all_checkins(self, client, sample_checkin, auth_headers):
        """Тест получения всех отметок"""
        response = client.get("/checkins", headers=auth_headers)
        assert response.status_code == 200
        checkins = response.json()
        assert len(checkins) == 1

    def test_get_checkin_by_id(self, client, sample_checkin, auth_headers):
        """Тест получения отметки по ID"""
        checkin_id = sample_checkin["id"]
        response = client.get(f"/checkins/{checkin_id}", headers=auth_headers)
        assert response.status_code == 200
        checkin = response.json()
        assert checkin["id"] == checkin_id

    def test_get_checkin_not_found(self, client, auth_headers):
        """Тест получения несуществующей отметки"""
        response = client.get("/checkins/999", headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Checkin not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body

    def test_update_checkin(self, client, sample_checkin, auth_headers):
        """Тест обновления отметки"""
        checkin_id = sample_checkin["id"]
        habit_id = sample_checkin["habit_id"]

        update_data = {
            "habit_id": habit_id,
            "checkin_date": "2024-10-16",
            "completed": False,
        }
        response = client.put(
            f"/checkins/{checkin_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200
        updated_checkin = response.json()
        assert updated_checkin["checkin_date"] == "2024-10-16"
        assert updated_checkin["completed"] is False

    def test_update_checkin_not_found(self, client, auth_headers):
        """Тест обновления несуществующей отметки"""
        update_data = {"habit_id": 1, "checkin_date": "2024-10-15", "completed": True}
        response = client.put("/checkins/999", json=update_data, headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Checkin not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body

    def test_delete_checkin(self, client, sample_checkin, auth_headers):
        """Тест удаления отметки"""
        checkin_id = sample_checkin["id"]
        response = client.delete(f"/checkins/{checkin_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Checkin deleted"}

    def test_delete_checkin_not_found(self, client, auth_headers):
        """Тест удаления несуществующей отметки"""
        response = client.delete("/checkins/999", headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Checkin not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body

    def test_create_checkin_duplicate(self, client, sample_checkin, auth_headers):
        """Тест создания дублирующей отметки"""
        checkin_data = {
            "habit_id": sample_checkin["habit_id"],
            "checkin_date": sample_checkin["checkin_date"],
            "completed": True,
        }
        response = client.post("/checkins", json=checkin_data, headers=auth_headers)
        assert response.status_code == 400
        body = response.json()
        assert body["code"] == "DUPLICATE_CHECKIN"

    def test_access_without_auth(self, client, sample_checkin):
        """Тест доступа без аутентификации"""
        response = client.get("/checkins")
        assert response.status_code == 403

        response = client.get(f"/checkins/{sample_checkin['id']}")
        assert response.status_code == 403
        response = client.post("/checkins", json={})
        assert response.status_code == 403

        response = client.put(f"/checkins/{sample_checkin['id']}", json={})
        assert response.status_code == 403

        response = client.delete(f"/checkins/{sample_checkin['id']}")
        assert response.status_code == 403
