import http from "k6/http";
import { check, sleep } from "k6";

// --- Настройки нагрузки ---
export const options = {
  vus: 50,           // 50 одновременных пользователей
  duration: "30s",   // нагрузка длится 30 секунд
  thresholds: {
    http_req_duration: ["p(95)<200"],
    http_req_failed: ["rate<0.01"],
  },
};

// --- Целевой URL сервиса ---
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

// Получаем токен один раз перед тестом
let authToken = "";

export function setup() {
  const loginResponse = http.post(
    `${BASE_URL}/login`,
    JSON.stringify({
      username: "test_user",
      password: "test_password"
    }),
    { headers: { "Content-Type": "application/json" } }
  );

  if (loginResponse.status === 200) {
    return { authToken: loginResponse.json("access_token") };
  }
  throw new Error("Failed to get auth token");
}

export default function (data) {
  const headers = {
    "Authorization": `Bearer ${data.authToken}`,
  };

  const res = http.get(`${BASE_URL}/habits`, { headers });

  check(res, {
    "status is 200": (r) => r.status === 200,
  });

  sleep(1);
}
