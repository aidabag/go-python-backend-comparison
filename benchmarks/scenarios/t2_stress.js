import { mixedWorkload } from './workload.js';

/**
 * T2: Stress Test — поиск точки отказа.
 *
 * Ступенчатый рост нагрузки до 2000 VUs.
 * Мягкий стоп: если ошибок > 80%, тест прерывается автоматически,
 * чтобы не повесить БД и не потерять данные.
 *
 * Цель: Найти предел пропускной способности каждого языка.
 */

export const options = {
    stages: [
        { duration: '2m', target: 500 },   // Ступень 1: базовая нагрузка
        { duration: '2m', target: 1000 },  // Ступень 2: повышенная нагрузка
        { duration: '2m', target: 1500 },  // Ступень 3: тяжёлая нагрузка
        { duration: '2m', target: 2000 },  // Ступень 4: предельная нагрузка
        { duration: '1m', target: 0 },     // Cool-down
    ],
    thresholds: {
        http_req_failed: [{ threshold: 'rate<0.80', abortOnFail: true }],
    },
};

export default function () {
    mixedWorkload();
}
