-- Создание таблицы товаров с проверкой неотрицательных значений
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  price INTEGER NOT NULL CHECK (price >= 0),
  stock INTEGER NOT NULL CHECK (stock >= 0)
);

-- Создание таблицы заказов с проверкой валидности статуса
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','completed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Создание связующей таблицы позиций заказов
CREATE TABLE order_items (
  order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id INTEGER NOT NULL REFERENCES products(id),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  price_at_order INTEGER NOT NULL CHECK (price_at_order >= 0),
  PRIMARY KEY (order_id, product_id)
);

-- Создание индексов для оптимизации скорости выполнения SQL-запросов
CREATE INDEX idx_order_items_order_id ON order_items (order_id);
CREATE INDEX idx_products_name ON products (name);
