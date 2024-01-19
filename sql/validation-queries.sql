-- Database checks for the practice shop.
-- Tables: users, products, cart_items, carts, orders, order_items (CREATE statements are in app/shop.py).
-- Prices and totals are in paise, so 248.00 is 24800.
--
-- Run: sqlite3 -header .data/shop.db < sql/validation-queries.sql
-- Tried on SQLite only. Plain joins, CASE and GROUP BY, so it should work on MySQL as well,
-- but I have not run it there.


-- Q1  Stock should be opening stock minus everything that was ordered. No rows = fine.
-- (TC-DB-01)
SELECT p.id, p.name, p.stock, p.opening_stock - COALESCE(SUM(oi.quantity), 0) AS expected_stock
FROM products p
LEFT JOIN order_items oi ON oi.product_id = p.id
GROUP BY p.id, p.name, p.stock, p.opening_stock
HAVING p.stock <> p.opening_stock - COALESCE(SUM(oi.quantity), 0);


-- Q2  Products with negative stock. Should be empty. (TC-DB-02)
SELECT id, name, stock
FROM products
WHERE stock < 0;


-- Q3  Orders whose numbers do not add up: subtotal vs the order lines,
-- and total vs subtotal - discount + shipping. Should be empty. (TC-DB-03)
SELECT o.order_no, o.subtotal_paise, l.lines_total, o.total_paise
FROM orders o
JOIN (SELECT order_id, SUM(unit_price_paise * quantity) AS lines_total
      FROM order_items
      GROUP BY order_id) l ON l.order_id = o.id
WHERE o.subtotal_paise <> l.lines_total
   OR o.total_paise <> o.subtotal_paise - o.discount_paise + o.shipping_paise;


-- Q4  Same email registered more than once, ignoring upper/lower case. Should be empty. (TC-DB-04)
SELECT lower(email) AS email, COUNT(*) AS accounts
FROM users
GROUP BY lower(email)
HAVING COUNT(*) > 1;


-- Q5  Orders with no items, and items that point to no order. Should be empty. (TC-DB-05)
SELECT 'order without items' AS problem, o.order_no AS ref
FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.id)
UNION ALL
SELECT 'item without order', CAST(i.id AS CHAR)
FROM order_items i
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.id = i.order_id);


-- Q6  What each customer should see on My orders. Compare the totals with the screen. (TC-DB-06)
SELECT u.email, o.order_no, o.placed_at, o.total_paise / 100.0 AS total
FROM orders o
JOIN users u ON u.id = o.user_id
ORDER BY u.email, o.id DESC;
