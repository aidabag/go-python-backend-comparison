import http from 'k6/http';
import { check, sleep } from 'k6';
import { commonOptions, BASE_URL, getRandomId, DEFAULT_HEADERS } from './shared.js';

/**
 * Сценарий S2: Моделирование процесса оформления заказа (Ordering).
 * Интенсивная нагрузка на механизмы транзакционной целостности и блокировки данных 
 * на уровне СУБД при конкурентном доступе.
 */

export const options = commonOptions;

export default function () {
    // Операция инициации заказа (POST /orders)
    // Формирование корзины из 1-3 случайных позиций
    const items = [];
    const numItems = Math.floor(Math.random() * 3) + 1;
    
    for (let i = 0; i < numItems; i++) {
        items.push({
            product_id: getRandomId(500), // Приобретение товаров из всей номенклатуры (500 позиций)
            quantity: Math.floor(Math.random() * 2) + 1,
        });
    }

    const payload = JSON.stringify({ items: items });
    const orderRes = http.post(`${BASE_URL}/orders`, payload, { headers: DEFAULT_HEADERS });

    const isCreated = check(orderRes, {
        'order created (201)': (r) => r.status === 201,
        'order has id': (r) => r.json().id !== undefined,
    });

    if (isCreated) {
        const orderId = orderRes.json().id;
        
        sleep(1); // Технологическая пауза перед проверкой статуса

        // Извлечение сводной информации по заказу (GET /orders/{id}/summary)
        const summaryRes = http.get(`${BASE_URL}/orders/${orderId}/summary`);
        check(summaryRes, {
            'summary status is 200': (r) => r.status === 200,
            'summary total is correct': (r) => r.json().total > 0,
        });
    }

    sleep(3); // Межсессионный интервал между транзакциями одного пользователя
}
