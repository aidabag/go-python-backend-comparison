import { mixedWorkload } from './workload.js';

/**
 * T5: Mixed Production Load — имитация реального production-трафика.
 * Профиль: Warm-up 30s → Steady 3m (200 VUs) → Cool-down 30s
 *
 * Бизнес-логика: 70% чтение, 20% запись, 10% аналитика.
 */

export const options = {
    stages: [
        { duration: '30s', target: 200 },  // Warm-up
        { duration: '3m', target: 200 },   // Steady State
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
