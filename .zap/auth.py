import json


def authenticate(helper, paramsValues, credentials):
    print("=== ZAP AUTH START ===")
    print("Credentials object: " + str(credentials))

    # Получаем параметры
    username = credentials.getParam("username")
    password = credentials.getParam("password")
    print("Username from context: " + str(username))
    print("Password from context: " + ("*" * len(password) if password else "None"))

    base_url = "http://localhost:8080"
    login_url = base_url + "/login"
    data = {"username": username, "password": password}

    print("Login URL: " + login_url)
    print("Request data: " + json.dumps(data))

    try:
        # Преобразуем в JSON
        json_data = json.dumps(data)
        print("Sending POST request...")

        # Отправляем запрос через helper
        response = helper.post(login_url, json_data)
        status_code = response.getStatusCode()
        response_body = response.getResponseBody().toString()

        print("Response status: " + str(status_code))
        print("Response body (first 200 chars): " + response_body[:200])

        if status_code == 200:
            response_json = json.loads(response_body)
            token = response_json.get("access_token")

            if token:
                print("SUCCESS! Token obtained: " + token[:30] + "...")

                # 1. Добавляем заголовок ко всем запросам
                helper.addCustomRequestHeader("Authorization", "Bearer " + token)
                # 2. Сохраняем токен в параметры сессии
                helper.setParam("token", token)

                return response
            else:
                print("ERROR: No 'access_token' in response")
        else:
            print("ERROR: HTTP " + str(status_code))

    except Exception as e:
        print("EXCEPTION: " + str(e))
        import traceback

        traceback.print_exc()

    print("=== ZAP AUTH FAILED ===")
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
