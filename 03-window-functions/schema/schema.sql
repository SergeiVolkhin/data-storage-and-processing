-- ШАГ 1. СОЗДАНИЕ ТАБЛИЦ

-- 1. Таблица customer
CREATE TABLE IF NOT EXISTS shop_db.customer (
	customer_id INTEGER,
	first_name VARCHAR(50),
	last_name VARCHAR(50),
	gender VARCHAR(20),
	dob DATE,
	job_title VARCHAR(100),
	job_industry_category VARCHAR(100),
	wealth_segment VARCHAR(50),
	deceased_indicator VARCHAR(5),
	owns_car VARCHAR(5),
	address TEXT,
	postcode INTEGER,
	state VARCHAR(50),
	country VARCHAR(50),
	property_valuation INTEGER
);

-- 2. Таблица product
CREATE TABLE IF NOT EXISTS shop_db.product (
	product_id INTEGER,
	brand VARCHAR(100),
	product_line VARCHAR(50),
	product_class VARCHAR(50),
	product_size VARCHAR(50),
	list_price NUMERIC(10, 2),
	standard_cost NUMERIC(10, 2)
);

-- 3. Таблица orders
CREATE TABLE IF NOT EXISTS shop_db.orders (
	order_id INTEGER,
	customer_id INTEGER,
	order_date DATE,
	online_order BOOLEAN,
	order_status VARCHAR(50)
);

-- 4. Таблица order_items
CREATE TABLE IF NOT EXISTS shop_db.order_items (
	order_item_id INTEGER,
	order_id INTEGER,
	product_id INTEGER,
	quantity INTEGER,
	item_list_price_at_sale NUMERIC(10, 2),
	item_standard_cost_at_sale NUMERIC(10, 2)
);

-- ШАГ 2. ИМПОРТ ДАННЫХ (CSV)

-- ШАГ 3. ОЧИСТКА ДАННЫХ

-- 1. Дедубликация product
CREATE TABLE IF NOT EXISTS shop_db.product_clean AS
SELECT 
	product_id, brand, product_line, product_class, product_size, list_price, standard_cost
FROM (
    SELECT 
        *,
        ROW_NUMBER() OVER(PARTITION BY product_id ORDER BY list_price DESC) as rn
    FROM product
) t
WHERE rn = 1;

-- Подменяем исправленную таблицу на чистую
DROP TABLE IF EXISTS shop_db.product;
ALTER TABLE shop_db.product_clean RENAME TO product;