import http from 'k6/http';
import { check, sleep } from 'k6';
import { commonOptions, BASE_URL } from './shared.js';

/**
 * Сценарий S4: Аналитическая обработка данных (Analytics).
 * Оценка производительности при выполнении сложных SQL-запросов и агрегирующих функций.
 */

export const options = commonOptions;

export default function () {
    // Формирование рейтинга популярных товарных позиций (GET /analytics/products/top)
    const topRes = http.get(`${BASE_URL}/analytics/products/top?limit=10`);
    
    check(topRes, {
        'top products status is 200': (r) => r.status === 200,
        'top products is array': (r) => Array.isArray(r.json()),
    });

    sleep(2); // Период ознакомления с отчетными данными

    // Вычисление среднего значения чека за отчетный интервал (GET /analytics/orders/average)
    const avgRes = http.get(`${BASE_URL}/analytics/orders/average`);
    
    check(avgRes, {
        'average status is 200': (r) => r.status === 200,
        'average is object': (r) => typeof r.json().average !== 'undefined',
    });

    sleep(3); // Ожидание следующей итерации аналитического запроса
}
