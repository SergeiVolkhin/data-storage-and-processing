-- Таблица transaction
SELECT
	t.transaction_id,
	t.product_id,
	t.customer_id,
	t.transaction_date,
	t.online_order,
	os.status_name AS order_status,
	b.brand_name AS brand,
	pl.line_name AS product_line,
	pc.class_name AS product_class,
	ps.size_name AS product_size,
	p.list_price,
	p.standard_cost
FROM  shop_db.transactions t
	LEFT JOIN shop_db.order_statuses os ON t.order_status_id = os.id
	LEFT JOIN shop_db.products p ON t.product_id = p.product_id
	LEFT JOIN shop_db.brands b ON p.brand_id = b.id
	LEFT JOIN shop_db.product_lines pl ON p.product_line_id = pl.id
	LEFT JOIN shop_db.product_classes pc ON p.product_class_id = pc.id
	LEFT JOIN shop_db.product_sizes ps ON p.product_size_id = ps.id
ORDER BY t.transaction_id;