import { mixedWorkload } from './workload.js';

/**
 * T3: Spike Test — тест на скачки нагрузки.
 *
 * Два резких скачка с 50 до 1000 VUs с периодом восстановления между ними.
 * Цель: Проверить скорость создания горутин (Go) vs задач Event Loop (Python),
 * а также способность к восстановлению после пика.
 */

export const options = {
    stages: [
        { duration: '30s', target: 50 },    // Baseline
        { duration: '30s', target: 50 },    // Стабильная работа
        { duration: '10s', target: 1000 },  // SPIKE #1
        { duration: '30s', target: 1000 },  // Удержание пика
        { duration: '10s', target: 50 },    // Спад
        { duration: '1m50s', target: 50 },  // Восстановление
        { duration: '10s', target: 1000 },  // SPIKE #2
        { duration: '30s', target: 1000 },  // Удержание
        { duration: '30s', target: 0 },     // Завершение
    ],
    thresholds: {},
};

export default function () {
    mixedWorkload();
}
