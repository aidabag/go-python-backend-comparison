INSERT INTO orders (status, created_at)
VALUES ('new', now())
RETURNING id, status, created_at;
