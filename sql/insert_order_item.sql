INSERT INTO order_items (order_id, product_id, quantity, price_at_order)
VALUES ($1, $2, $3, $4)
ON CONFLICT (order_id, product_id) 
DO UPDATE SET quantity = order_items.quantity + EXCLUDED.quantity;
