import http from "k6/http";
import { check, sleep } from "k6";

// --- Настройки нагрузки ---
export const options = {
  vus: 50,           // 50 одновременных пользователей
  duration: "30s",   // нагрузка длится 30 секунд
  thresholds: {
    http_req_duration: ["p(95)<200"], // NFR-01: p95 ≤ 200ms
    http_req_failed: ["rate<0.01"],   // не более 1% ошибок
  },
};

// --- Целевой URL сервиса ---
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  const res = http.get(`${BASE_URL}/habits`);
  check(res, {
    "status is 200": (r) => r.status === 200,
  });
  sleep(1);
}
