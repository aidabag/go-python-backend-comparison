import { mixedWorkload } from './workload.js';

/**
 * T4: Scalability Test — вертикальная масштабируемость.
 *
 * Количество VUs задаётся через переменную окружения SCALE_VUS.
 * Используется совместно с изменением CPU лимитов в docker-compose.yml.
 *
 * Запуск:
 *   k6 run t4_scale.js --env SCALE_VUS=50   (для 1 CPU)
 *   k6 run t4_scale.js --env SCALE_VUS=100  (для 2 CPU)
 *   k6 run t4_scale.js --env SCALE_VUS=200  (для 4 CPU)
 *
 * Профиль: Warm-up 30s → Steady 4m → Cool-down 30s
 * Метрики: RPS, Latency p95, Scaling Efficiency.
 */

const vus = parseInt(__ENV.SCALE_VUS || '200');

export const options = {
    stages: [
        { duration: '30s', target: vus },  // Warm-up
        { duration: '4m', target: vus },   // Steady State
        { duration: '30s', target: 0 },    // Cool-down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],
        http_req_failed: ['rate<0.01'],
    },
};

export default function () {
    mixedWorkload();
}
