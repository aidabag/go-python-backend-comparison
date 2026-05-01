import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL, getRandomId, DEFAULT_HEADERS } from './shared.js';

/**
 * T1: Load Test — 4 бизнес-сценария для стабильной нагрузки.
 *
 * Запуск нужного сценария через переменную окружения SCENARIO:
 *   k6 run t1_load.js --env SCENARIO=browsing
 *   k6 run t1_load.js --env SCENARIO=orders
 *   k6 run t1_load.js --env SCENARIO=admin
 *   k6 run t1_load.js --env SCENARIO=analytics
 *
 * Профиль: Warm-up 30s → Steady 3.5m (200 VUs) → Cool-down 30s
 * Цель: Измерить стабильную производительность по типу операции.
 */

export const options = {
    stages: [
        { duration: '30s', target: 200 },   // Warm-up
        { duration: '3m30s', target: 200 }, // Steady State
        { duration: '30s', target: 0 },     // Cool-down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],
        http_req_failed: ['rate<0.01'],
    },
};

const scenario = __ENV.SCENARIO || 'browsing';

export default function () {
    switch (scenario) {
        case 'browsing':
            scenarioBrowsing();
            break;
        case 'orders':
            scenarioOrders();
            break;
        case 'admin':
            scenarioAdmin();
            break;
        case 'analytics':
            scenarioAnalytics();
            break;
        default:
            scenarioBrowsing();
    }
}

// S1: Просмотр каталога (Read-heavy)
function scenarioBrowsing() {
    const offset = Math.floor(Math.random() * 20);
    const listRes = http.get(`${BASE_URL}/products?limit=10&offset=${offset}`);
    check(listRes, {
        'list status is 200': (r) => r.status === 200,
        'list is array': (r) => Array.isArray(r.json()),
    });

    sleep(0.5);

    const productId = getRandomId(500);
    const detailRes = http.get(`${BASE_URL}/products/${productId}`);
    check(detailRes, {
        'detail status is 200': (r) => r.status === 200,
        'detail has correct id': (r) => r.json().id !== undefined,
    });

    sleep(0.5);
}

// S2: Оформление заказов (Write-heavy, транзакции)
function scenarioOrders() {
    const items = [];
    const numItems = Math.floor(Math.random() * 3) + 1;
    for (let i = 0; i < numItems; i++) {
        items.push({
            product_id: getRandomId(500),
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
        sleep(0.5);
        const summaryRes = http.get(`${BASE_URL}/orders/${orderId}/summary`);
        check(summaryRes, {
            'summary status is 200': (r) => r.status === 200,
            'summary total > 0': (r) => r.json().total > 0,
        });
    }

    sleep(1);
}

// S3: Администрирование (конкурентные UPDATE)
function scenarioAdmin() {
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

    sleep(0.5);
}

// S4: Аналитика (тяжёлые SQL-агрегации)
function scenarioAnalytics() {
    const topRes = http.get(`${BASE_URL}/analytics/products/top?limit=10`);
    check(topRes, {
        'top products status is 200': (r) => r.status === 200,
        'top products is array': (r) => Array.isArray(r.json()),
    });

    sleep(1);

    const avgRes = http.get(`${BASE_URL}/analytics/orders/average`);
    check(avgRes, {
        'average status is 200': (r) => r.status === 200,
        'average is object': (r) => typeof r.json().average !== 'undefined',
    });

    sleep(1);
}
