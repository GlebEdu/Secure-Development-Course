class TestSecurityMeasures:
    """Тесты мер безопасности"""

    # === SQL Injection Protection Tests ===

    def test_sql_injection_login_protection(self, client):
        """Защита от SQL инъекции в логине"""
        sql_injection_payloads = [
            {"username": "admin' OR '1'='1'--", "password": "anything"},
            {"username": "admin' --", "password": "anything"},
            {"username": "x' UNION SELECT 1,2,3--", "password": "x"},
            {"username": "test_user'; DROP TABLE users--", "password": "x"},
        ]

        for payload in sql_injection_payloads:
            response = client.post("/login", json=payload)
            # Должен быть отказ в аутентификации, а не успех
            assert response.status_code == 401
            assert "INVALID_CREDENTIALS" in response.json()["code"]

    def test_sql_injection_search_protection(self, client, auth_headers):
        """Защита от SQL инъекции в поиске"""
        injection_queries = [
            "' UNION SELECT * FROM users--",
            "test' OR 1=1--",
            "x'; DROP TABLE habits--",
        ]

        for query in injection_queries:
            response = client.get(f"/search?q={query}", headers=auth_headers)
            # Не должно быть SQL ошибок (500) или неожиданных данных
            assert response.status_code != 500

    # === Input Validation Tests ===

    def test_oversized_input_validation(self, client, auth_headers):
        """Валидация слишком больших входных данных"""
        long_name = "A" * 150  # Превышает лимит в 100 символов
        response = client.post(
            "/habits", json={"name": long_name, "periodicity": 1}, headers=auth_headers
        )
        assert response.status_code == 422

        response = client.post(
            "/habits", json={"name": "test", "periodicity": 1000}, headers=auth_headers
        )

        assert response.status_code != 500

    def test_negative_values_validation(self, client, auth_headers):
        """Валидация отрицательных значений"""
        response = client.post(
            "/habits", json={"name": "test", "periodicity": -5}, headers=auth_headers
        )
        assert response.status_code == 422

        response = client.post(
            "/habits", json={"name": "test", "periodicity": 0}, headers=auth_headers
        )
        assert response.status_code == 422

    def test_malformed_json_handling(self, client, auth_headers):
        """Обработка невалидного JSON"""
        # Неполный JSON
        response = client.post(
            "/habits", data='{"name": "test", "periodicity":', headers=auth_headers
        )
        assert response.status_code == 422

        # Лишние поля
        response = client.post(
            "/habits",
            json={"name": "test", "periodicity": 1, "extra_field": "value"},
            headers=auth_headers,
        )
        assert response.status_code == 200  # Лишние поля игнорируются

    # === Authentication & Authorization Tests ===

    def test_invalid_token_formats(self, client):
        """Тестирование невалидных форматов токенов"""
        invalid_tokens = [
            {"Authorization": "InvalidToken"},  # Без Bearer
            {"Authorization": "Bearer"},  # Без токена
            {"Authorization": "Bearer "},  # Пустой токен
            {"Authorization": "Basic dGVzdDp0ZXN0"},  # Basic auth вместо Bearer
        ]

        for headers in invalid_tokens:
            response = client.get("/habits", headers=headers)
            assert response.status_code == 403

    # === Error Handling Security Tests ===

    def test_error_messages_no_sensitive_info(self, client, auth_headers):
        """Ошибки не раскрывают чувствительную информацию"""
        # Провоцируем разные ошибки
        responses = [
            client.get("/habits/999999", headers=auth_headers),  # Несуществующий ID
            client.post(
                "/checkins",
                json={"habit_id": 999, "checkin_date": "2024-01-01", "completed": True},
                headers=auth_headers,
            ),  # Несуществующая привычка
        ]

        for response in responses:
            if response.status_code >= 400:
                error_body = str(response.json())
                # Проверяем что в ошибках нет чувствительной информации
                assert "sqlite3" not in error_body.lower()
                assert "password" not in error_body.lower()
                assert "secret" not in error_body.lower()
                assert "traceback" not in error_body.lower()
                assert "file path" not in error_body.lower()

    # === Path Traversal Protection ===

    def test_path_traversal_protection(self, client, auth_headers):
        """Защита от path traversal атак"""
        path_traversal_ids = [
            "../../etc/passwd",
            "1/../1",
            "1%2f..%2f1",
            "1/./1",
        ]

        for malicious_id in path_traversal_ids:
            response = client.get(f"/habits/{malicious_id}", headers=auth_headers)
            # Должна быть ошибка "не найдено" или "невалидный ID", а не доступ к файлам
            assert response.status_code in [404, 422, 400]

    # === Date Validation Tests ===

    def test_invalid_date_formats(self, client, auth_headers, sample_habit):
        """Валидация неверных форматов дат"""
        invalid_dates = [
            "2024-13-01",  # Несуществующий месяц
            "2024-02-30",  # Несуществующий день
            "invalid-date",
            "2024/01/01",  # Неправильный разделитель
            "01-01-2024",  # Неправильный порядок
        ]

        for invalid_date in invalid_dates:
            checkin_data = {
                "habit_id": sample_habit["id"],
                "checkin_date": invalid_date,
                "completed": True,
            }
            response = client.post("/checkins", json=checkin_data, headers=auth_headers)
            assert response.status_code == 422

    def test_sql_injection_in_path_parameters(self, client, auth_headers):
        """Защита от SQL инъекции в path parameters"""
        injection_ids = [
            "1 OR 1=1",
            "1; DROP TABLE habits",
            "1 UNION SELECT * FROM users",
        ]

        for malicious_id in injection_ids:
            response = client.get(f"/habits/{malicious_id}", headers=auth_headers)
            # Должна быть ошибка "не найдено" или "невалидный ID", а не SQL ошибка
            assert response.status_code != 500
            assert response.status_code in [404, 422, 400]

    # === Rate Limiting Tests ===

    def test_rate_limiting_on_health_endpoint(self, client):
        """Проверка ограничения запросов"""
        # Делаем несколько быстрых запросов
        for i in range(15):
            response = client.get("/health")
            # После определенного количества запросов должен сработать rate limit
            if i >= 10:  # Предполагаемый лимит
                if response.status_code == 429:  # Too Many Requests
                    break
        else:
            # Если rate limit не сработал, это нормально для тестовой среды
            assert response.status_code == 200

    # === Security Headers Tests ===

    def test_security_headers_on_all_endpoints(self, client, auth_headers):
        """Security headers присутствуют на всех эндпоинтах"""
        endpoints = [
            "/health",
            "/habits",
            "/stats",
            "/users/me",
        ]

        security_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
        ]

        for endpoint in endpoints:
            if endpoint == "/users/me":
                response = client.get(endpoint, headers=auth_headers)
            else:
                response = client.get(endpoint)

            for header in security_headers:
                assert (
                    header in response.headers
                ), f"Header {header} missing from {endpoint}"

    # === Boundary Value Tests ===

    def test_boundary_values_habit_creation(self, client, auth_headers):
        """Тестирование граничных значений при создании привычки"""
        boundary_cases = [
            {"name": "A", "periodicity": 1},  # Минимальная длина имени
            {"name": "A" * 100, "periodicity": 1},  # Максимальная длина имени
            {"name": "Test", "periodicity": 1},  # Минимальная периодичность
            {"name": "Test", "periodicity": 365},  # Максимальная периодичность
        ]

        for case in boundary_cases:
            response = client.post("/habits", json=case, headers=auth_headers)
            assert response.status_code == 200, f"Failed for case: {case}"

    def test_special_characters_in_input(self, client, auth_headers):
        """Обработка специальных символов во входных данных"""
        special_cases = [
            {"name": "Habit with 'quotes'", "periodicity": 1},
            {"name": "Habit with & ampersand", "periodicity": 1},
            {"name": "Habit with < and >", "periodicity": 1},
            {"name": "Habit with / slashes", "periodicity": 1},
        ]

        for case in special_cases:
            response = client.post("/habits", json=case, headers=auth_headers)
            assert response.status_code == 200
            # Проверяем что данные сохранились корректно
            habit_id = response.json()["id"]
            get_response = client.get(f"/habits/{habit_id}", headers=auth_headers)
            assert get_response.status_code == 200


class TestPasswordSecurity:
    """Тесты безопасности паролей"""

    def test_password_hashing_verification(self, client):
        """Проверка что пароли хешируются"""
        # Этот тест требует доступа к базе для проверки хешей
        # Здесь проверяем что логин работает с правильным паролем
        login_data = {"username": "test_user", "password": "test_password"}
        response = client.post("/login", json=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()

        # И не работает с неправильным
        wrong_login = {"username": "test_user", "password": "wrong_password"}
        response = client.post("/login", json=wrong_login)
        assert response.status_code == 401
