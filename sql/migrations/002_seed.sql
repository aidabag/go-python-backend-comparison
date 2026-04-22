-- Заполнение таблицы товаров эталонными данными (500 позиций)
INSERT INTO products (name, price, stock)
SELECT 
    'Product ' || i,
    (random() * 10000 + 100)::int,
    1000
FROM generate_series(1, 500) AS i;

-- Генерация начальных заказов (250 позиций) для обеспечения данных в аналитике
DO $$
DECLARE
    order_id_val INT;
    product_id_val INT;
    random_price INT;
BEGIN
    FOR i IN 1..250 LOOP
        -- Создание заказа
        INSERT INTO orders (status, created_at) 
        VALUES ('completed', now() - (random() * interval '7 days'))
        RETURNING id INTO order_id_val;

        -- Добавление 1-3 товаров в каждый заказ
        FOR j IN 1..(1 + (random() * 2)::int) LOOP
            product_id_val := (random() * 499 + 1)::int;
            random_price := (random() * 10000 + 100)::int;
            
            -- Использование INSERT ... ON CONFLICT для предотвращения дубликатов в order_items
            INSERT INTO order_items (order_id, product_id, quantity, price_at_order)
            VALUES (order_id_val, product_id_val, (random() * 5 + 1)::int, random_price)
            ON CONFLICT DO NOTHING;
        END LOOP;
    END LOOP;
END $$;
