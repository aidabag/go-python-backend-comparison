SELECT price, stock FROM products WHERE id = $1 FOR UPDATE;
