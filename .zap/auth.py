# Этот скрипт выполняется в ZAP (Jython 2.7)
# Не требует дополнительных зависимостей

import json


def authenticate(helper, paramsValues, credentials):
    """
    Упрощённый скрипт аутентификации для ZAP
    """
    print("[ZAP Auth] Starting authentication...")

    # Получаем параметры
    username = credentials.getParam("username")
    password = credentials.getParam("password")
    base_url = "http://localhost:8080"

    # Формируем URL и данные
    login_url = base_url + "/login"
    data = {"username": username, "password": password}

    # Отправляем запрос через ZAP API
    # ZAP предоставляет объект 'helper' для HTTP запросов
    try:
        # Кодируем данные в JSON
        json_data = json.dumps(data)

        # Отправляем POST запрос
        response = helper.post(login_url, json_data)
        status_code = response.getStatusCode()
        response_body = response.getResponseBody().toString()

        print(f"[ZAP Auth] Response status: {status_code}")
        print(f"[ZAP Auth] Response body: {response_body[:100]}...")

        if status_code == 200:
            # Парсим JSON и получаем токен
            response_json = json.loads(response_body)
            token = response_json.get("access_token")

            if token:
                print(f"[ZAP Auth] Success! Token: {token[:30]}...")

                # Критически важные строки:
                # 1. Сохраняем токен в сессию ZAP
                helper.setParam("token", token)

                # 2. Добавляем заголовок Authorization ко всем запросам
                helper.addCustomRequestHeader("Authorization", "Bearer " + token)

                return response
            else:
                print("[ZAP Auth] ERROR: No access_token in response")
                return None
        else:
            print(f"[ZAP Auth] ERROR: Login failed with status {status_code}")
            return None

    except Exception as e:
        print(f"[ZAP Auth] EXCEPTION: {str(e)}")
        return None


def getRequiredParamsNames():
    return ["username", "password"]


def getOptionalParamsNames():
    return []


def getCredentialsParamsNames():
    return ["username", "password"]


def getLoggedInIndicator():
    return '"token_type":"bearer"'


def getLoggedOutIndicator():
    return '"code":"INVALID_CREDENTIALS"'
