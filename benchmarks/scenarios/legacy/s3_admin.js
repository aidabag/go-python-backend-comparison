import http from 'k6/http';
import { check, sleep } from 'k6';
import { commonOptions, BASE_URL, getRandomId, DEFAULT_HEADERS } from './shared.js';

/**
 * Сценарий S3: Имитация действий администратора (Admin Updates).
 * Оценка эффективности выполнения операций обновления данных в БД (UPDATE).
 */

export const options = commonOptions;

export default function () {
    // Корректировка параметров стоимости и остатка продукции (PUT /products/{id})
    const productId = getRandomId(500);
    
    const payload = JSON.stringify({
        name: `Laptop Pro Updated ${productId}`,
        price: 110000 + productId,
        stock: 40 + (productId % 10),
    });

    const updateRes = http.patch(`${BASE_URL}/products/${productId}`, payload, { headers: DEFAULT_HEADERS });

    check(updateRes, {
        'update status is 200': (r) => r.status === 200,
        'update price is correct': (r) => r.json().price >= 110000,
    });

    sleep(1.5); // Интервал между операциями модификации данных
}
