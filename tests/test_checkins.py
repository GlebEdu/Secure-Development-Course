class TestCheckinsCRUD:
    """Тесты CRUD операций для отметок"""

    def test_create_checkin_success(self, client, sample_habit):
        """Тест успешного создания отметки"""
        checkin_data = {
            "habit_id": sample_habit["id"],
            "checkin_date": "2025-10-15",
            "completed": True,
        }
        response = client.post("/checkins", json=checkin_data)
        assert response.status_code == 200
        body = response.json()
        assert body["habit_id"] == sample_habit["id"]
        assert body["checkin_date"] == "2025-10-15"
        assert body["completed"] is True

    def test_create_checkin_habit_not_found(self, client):
        """Тест создания отметки для несуществующей привычки"""
        checkin_data = {
            "habit_id": 999,
            "checkin_date": "2025-10-15",
            "completed": True,
        }
        response = client.post("/checkins", json=checkin_data)
        assert response.status_code == 404

    def test_get_all_checkins(self, client, sample_checkin):
        """Тест получения всех отметок"""
        response = client.get("/checkins")
        assert response.status_code == 200
        checkins = response.json()
        assert len(checkins) == 1

    def test_get_checkin_by_id(self, client, sample_checkin):
        """Тест получения отметки по ID"""
        checkin_id = sample_checkin["id"]
        response = client.get(f"/checkins/{checkin_id}")
        assert response.status_code == 200
        checkin = response.json()
        assert checkin["id"] == checkin_id

    def test_get_checkin_not_found(self, client):
        """Тест получения несуществующей отметки"""
        response = client.get("/checkins/999")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "not_found"
        assert "message" in body["error"]

    def test_update_checkin(self, client, sample_checkin):
        """Тест обновления отметки"""
        checkin_id = sample_checkin["id"]
        habit_id = sample_checkin["habit_id"]

        update_data = {
            "habit_id": habit_id,
            "checkin_date": "2025-10-16",
            "completed": False,
        }
        response = client.put(f"/checkins/{checkin_id}", json=update_data)
        assert response.status_code == 200
        updated_checkin = response.json()
        assert updated_checkin["checkin_date"] == "2025-10-16"
        assert updated_checkin["completed"] is False

    def test_update_checkin_not_found(self, client):
        """Тест обновления несуществующей отметки"""
        update_data = {"habit_id": 1, "checkin_date": "2025-10-15", "completed": True}
        response = client.put("/checkins/999", json=update_data)
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "not_found"
        assert "message" in body["error"]

    def test_delete_checkin(self, client, sample_checkin):
        """Тест удаления отметки"""
        checkin_id = sample_checkin["id"]
        response = client.delete(f"/checkins/{checkin_id}")
        assert response.status_code == 200
        assert response.json() == {"message": "Checkin deleted"}

    def test_delete_checkin_not_found(self, client):
        """Тест удаления несуществующей отметки"""
        response = client.delete("/checkins/999")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "not_found"
        assert "message" in body["error"]
