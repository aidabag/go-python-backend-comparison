/**
 * Регламентация общей конфигурации и утилит для проведения нагрузочного тестирования.
 * Определение единых профилей нагрузки (stages) для обеспечения идентичности условий 
 * экспериментов между различными реализациями сервисов.
 */

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

// Конфигурация профиля нагрузки (Traffic Profile)
// Реализация трехступенчатой модели: прогрев -> стабилизация -> стресс-тестирование.
export const commonOptions = {
    stages: [
        { duration: '30s', target: 20 },  // 1. Инициализация и прогрев (Warm-up)
        { duration: '30s', target: 50 },  // 2. Исследование стабильного состояния (Steady Load)
        { duration: '1m', target: 100 },  // 3. Моделирование повышенной нагрузки (Heavy Load)
        { duration: '1m', target: 500 },  // 4. Поиск предельной пропускной способности (Stress Scaling)
        { duration: '30s', target: 0 },   // 5. Завершение и освобождение ресурсов (Cool-down)
    ],
    thresholds: {
        http_req_failed: ['rate<0.05'], // Допускаем менее 5% ошибок во время стресс-теста
        http_req_duration: ['p(95)<1000'], // 95% запросов должны уложиться в 1 секунду
    },
};

// Хелпер для случайных ID
export function getRandomId(max) {
    return Math.floor(Math.random() * max) + 1;
}

// Заголовки по умолчанию
export const DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
};
