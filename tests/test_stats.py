class TestStats:
    """Тесты для статистики"""

    def test_get_stats_empty(self, client, auth_headers):
        """Тест статистики при пустой базе"""
        response = client.get("/stats", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_habits"] == 0
        assert stats["total_checkins"] == 0
        assert stats["completed_checkins"] == 0
        assert stats["completion_rate"] == 0.0

    def test_get_stats_with_data(self, client, auth_headers):
        """Тест статистики с данными"""

        habits_data = [
            {"name": "Привычка 1", "periodicity": 1},
            {"name": "Привычка 2", "periodicity": 7},
        ]

        for habit_data in habits_data:
            client.post("/habits", json=habit_data, headers=auth_headers)

        checkins_data = [
            {"habit_id": 1, "checkin_date": "2024-10-15", "completed": True},
            {"habit_id": 1, "checkin_date": "2024-10-16", "completed": True},
            {"habit_id": 2, "checkin_date": "2024-10-15", "completed": True},
            {"habit_id": 2, "checkin_date": "2024-10-16", "completed": False},
        ]

        for checkin_data in checkins_data:
            client.post("/checkins", json=checkin_data, headers=auth_headers)

        response = client.get("/stats", headers=auth_headers)
        assert response.status_code == 200
        stats = response.json()

        assert stats["total_habits"] == 2
        assert stats["total_checkins"] == 4
        assert stats["completed_checkins"] == 3
        assert stats["completion_rate"] == 75.0

    def test_get_habit_stats(self, client, sample_habit, auth_headers):
        """Тест статистики по конкретной привычке"""
        # Создаем несколько отметок для привычки
        checkins_data = [
            {
                "habit_id": sample_habit["id"],
                "checkin_date": "2024-10-15",
                "completed": True,
            },
            {
                "habit_id": sample_habit["id"],
                "checkin_date": "2024-10-16",
                "completed": True,
            },
            {
                "habit_id": sample_habit["id"],
                "checkin_date": "2024-10-17",
                "completed": False,
            },
        ]

        for checkin_data in checkins_data:
            client.post("/checkins", json=checkin_data, headers=auth_headers)

        response = client.get(
            f"/habits/{sample_habit['id']}/stats", headers=auth_headers
        )
        assert response.status_code == 200
        stats = response.json()

        assert stats["habit_id"] == sample_habit["id"]
        assert stats["habit_name"] == "Тестовая привычка"
        assert stats["total_checkins"] == 3
        assert stats["completed_checkins"] == 2
        assert stats["completion_rate"] == round((2 / 3) * 100, 2)
        assert stats["periodicity"] == 1

    def test_get_habit_stats_not_found(self, client, auth_headers):
        """Тест статистики для несуществующей привычки"""
        response = client.get("/habits/999/stats", headers=auth_headers)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "NOT_FOUND"
        assert body["detail"] == "Habit not found"

    def test_access_stats_without_auth(self, client):
        """Тест доступа к статистике без аутентификации"""
        response = client.get("/stats")
        assert response.status_code == 403
        response = client.get("/habits/1/stats")
        assert response.status_code == 403
