/**
 * Общая конфигурация и утилиты нагрузочного тестирования.
 * Каждый тестовый профиль (T1-T5) определяет свой собственный набор options.
 */

// Адрес тестируемого сервиса
export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

// Генерация случайного идентификатора в диапазоне [1, max]
export function getRandomId(max) {
    return Math.floor(Math.random() * max) + 1;
}

// Стандартные заголовки для запросов с телом (POST, PUT, PATCH)
export const DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
};
