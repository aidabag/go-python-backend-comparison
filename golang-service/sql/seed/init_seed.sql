SELECT setseed(0.12345);
-- Полная очистка таблиц
TRUNCATE TABLE order_items RESTART IDENTITY CASCADE;
TRUNCATE TABLE orders RESTART IDENTITY CASCADE;
TRUNCATE TABLE products RESTART IDENTITY CASCADE;

-- Инициализация тестовых наборов данных

-- 1. Товары: 1000 позиций
INSERT INTO products (name, price, stock)
SELECT 
  'Product ' || generate_series,
  (random() * 9900 + 100)::INTEGER,
  (random() * 500 + 10)::INTEGER
FROM generate_series(1, 1000);

-- 2. Заказы: 5000 позиций
INSERT INTO orders (status, created_at)
SELECT 
  CASE WHEN random() < 0.7 THEN 'new' ELSE 'completed' END,
  now() - (random() * interval '30 days')
FROM generate_series(1, 5000);

-- 3. Позиции заказов: ~20000 элементов, генерация уникальных пар (order_id, product_id)
WITH order_product_pairs AS (
  SELECT
    o.id AS order_id,
    p.id AS product_id,
    (random() * 9 + 1)::INTEGER AS quantity,
    p.price AS price_at_order
  FROM orders o
  CROSS JOIN LATERAL (
    SELECT id, price FROM products ORDER BY random() LIMIT 4
  ) p
)
INSERT INTO order_items (order_id, product_id, quantity, price_at_order)
SELECT *
FROM order_product_pairs;
