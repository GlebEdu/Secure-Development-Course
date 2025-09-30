class TestStats:
    """Тесты для статистики"""

    def test_get_stats_empty(self, client):
        """Тест статистики при пустой базе"""
        response = client.get("/stats")
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_habits"] == 0
        assert stats["total_checkins"] == 0
        assert stats["completed_checkins"] == 0
        assert stats["completion_rate"] == 0.0

    def test_get_stats_with_data(self, client):
        """Тест статистики с данными"""

        habits_data = [
            {"name": "Привычка 1", "periodicity": 1},
            {"name": "Привычка 2", "periodicity": 7},
        ]

        for habit_data in habits_data:
            client.post("/habits", json=habit_data)

        checkins_data = [
            {"habit_id": 1, "checkin_date": "2025-10-15", "completed": True},
            {"habit_id": 1, "checkin_date": "2025-10-16", "completed": True},
            {"habit_id": 2, "checkin_date": "2025-10-15", "completed": True},
            {"habit_id": 2, "checkin_date": "2025-10-16", "completed": False},
        ]

        for checkin_data in checkins_data:
            client.post("/checkins", json=checkin_data)

        response = client.get("/stats")
        assert response.status_code == 200
        stats = response.json()

        assert stats["total_habits"] == 2
        assert stats["total_checkins"] == 4
        assert stats["completed_checkins"] == 3
        assert stats["completion_rate"] == 75.0
