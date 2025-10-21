class TestHabitsCRUD:
    """Тесты CRUD операций для привычек"""

    def test_create_habit_success(self, client):
        """Тест успешного создания привычки"""
        habit_data = {"name": "Утренняя зарядка", "periodicity": 1}
        response = client.post("/habits", json=habit_data)
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Утренняя зарядка"
        assert body["periodicity"] == 1
        assert body["user_id"] == 1
        assert "id" in body

    def test_create_habit_validation_error(self, client):
        """Тест ошибки валидации при создании привычки"""
        habit_data = {"name": "", "periodicity": 1}
        response = client.post("/habits", json=habit_data)
        assert response.status_code == 422

    def test_get_all_habits(self, client, sample_habit):
        """Тест получения всех привычек"""
        response = client.get("/habits")
        assert response.status_code == 200
        habits = response.json()
        assert len(habits) == 1
        assert habits[0]["name"] == "Тестовая привычка"

    def test_get_habit_by_id(self, client, sample_habit):
        """Тест получения привычки по ID"""
        habit_id = sample_habit["id"]
        response = client.get(f"/habits/{habit_id}")
        assert response.status_code == 200
        habit = response.json()
        assert habit["name"] == "Тестовая привычка"
        assert habit["id"] == habit_id

    def test_get_habit_not_found(self, client):
        """Тест получения несуществующей привычки"""
        response = client.get("/habits/999")
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Habit not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body

    def test_update_habit(self, client, sample_habit):
        """Тест обновления привычки"""
        habit_id = sample_habit["id"]
        update_data = {"name": "Новое название", "periodicity": 7}
        response = client.put(f"/habits/{habit_id}", json=update_data)
        assert response.status_code == 200
        updated_habit = response.json()
        assert updated_habit["name"] == "Новое название"
        assert updated_habit["periodicity"] == 7

    def test_update_habit_not_found(self, client):
        """Тест обновления несуществующей привычки"""
        update_data = {"name": "Тест", "periodicity": 1}
        response = client.put("/habits/999", json=update_data)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Habit not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body

    def test_delete_habit(self, client, sample_habit):
        """Тест удаления привычки"""
        habit_id = sample_habit["id"]
        response = client.delete(f"/habits/{habit_id}")
        assert response.status_code == 200
        assert response.json() == {"message": "Habit deleted"}

    def test_delete_habit_not_found(self, client):
        """Тест удаления несуществующей привычки"""
        response = client.delete("/habits/999")
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Habit not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body
