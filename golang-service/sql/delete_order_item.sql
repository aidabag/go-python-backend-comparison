DELETE FROM order_items
WHERE order_id = $1 AND product_id = $2
RETURNING quantity;
