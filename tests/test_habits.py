class TestHabitsCRUD:
    """Тесты CRUD операций для привычек"""

    def test_create_habit_success(self, client, auth_headers):
        """Тест успешного создания привычки"""
        habit_data = {"name": "Утренняя зарядка", "periodicity": 1}
        response = client.post("/habits", json=habit_data, headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Утренняя зарядка"
        assert body["periodicity"] == 1
        assert body["user_id"] == 1  # ID тестового пользователя
        assert "id" in body

    def test_create_habit_validation_error(self, client, auth_headers):
        """Тест ошибки валидации при создании привычки"""
        habit_data = {"name": "", "periodicity": 1}
        response = client.post("/habits", json=habit_data, headers=auth_headers)
        assert response.status_code == 422

    def test_get_all_habits(self, client, sample_habit, auth_headers):
        """Тест получения всех привычек"""
        response = client.get("/habits", headers=auth_headers)
        assert response.status_code == 200
        habits = response.json()
        assert len(habits) == 1
        assert habits[0]["name"] == "Тестовая привычка"

    def test_get_habit_by_id(self, client, sample_habit, auth_headers):
        """Тест получения привычки по ID"""
        habit_id = sample_habit["id"]
        response = client.get(f"/habits/{habit_id}", headers=auth_headers)
        assert response.status_code == 200
        habit = response.json()
        assert habit["name"] == "Тестовая привычка"
        assert habit["id"] == habit_id

    def test_get_habit_not_found(self, client, auth_headers):
        """Тест получения несуществующей привычки"""
        response = client.get("/habits/999", headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Habit not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body

    def test_update_habit(self, client, sample_habit, auth_headers):
        """Тест обновления привычки"""
        habit_id = sample_habit["id"]
        update_data = {"name": "Новое название", "periodicity": 7}
        response = client.put(
            f"/habits/{habit_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200
        updated_habit = response.json()
        assert updated_habit["name"] == "Новое название"
        assert updated_habit["periodicity"] == 7

    def test_update_habit_not_found(self, client, auth_headers):
        """Тест обновления несуществующей привычки"""
        update_data = {"name": "Тест", "periodicity": 1}
        response = client.put("/habits/999", json=update_data, headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Habit not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body

    def test_delete_habit(self, client, sample_habit, auth_headers):
        """Тест удаления привычки"""
        habit_id = sample_habit["id"]
        response = client.delete(f"/habits/{habit_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Habit deleted"}

    def test_delete_habit_not_found(self, client, auth_headers):
        """Тест удаления несуществующей привычки"""
        response = client.delete("/habits/999", headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["title"] == "Not Found"
        assert body["detail"] == "Habit not found"
        assert body["status"] == 404
        assert "correlation_id" in body
        assert "timestamp" in body

    def test_access_without_auth(self, client, sample_habit):
        """Тест доступа без аутентификации"""
        response = client.get("/habits")
        assert response.status_code == 403

        response = client.get(f"/habits/{sample_habit['id']}")
        assert response.status_code == 403

        response = client.post("/habits", json={"name": "test", "periodicity": 1})
        assert response.status_code == 403

        response = client.put(
            f"/habits/{sample_habit['id']}", json={"name": "test", "periodicity": 1}
        )
        assert response.status_code == 403

        response = client.delete(f"/habits/{sample_habit['id']}")
        assert response.status_code == 403

    def test_xss_protection_in_habit_name(self, client, auth_headers):
        """Тест защиты от XSS в названии привычки"""
        habit_data = {"name": "<script>alert('XSS')</script>", "periodicity": 1}
        response = client.post("/habits", json=habit_data, headers=auth_headers)
        assert response.status_code == 200

        habit_id = response.json()["id"]
        get_response = client.get(f"/habits/{habit_id}", headers=auth_headers)
        name = get_response.json()["name"]

        # Проверяем что скрипт экранирован
        assert "<script>" not in name
        assert "&lt;script&gt;" in name
