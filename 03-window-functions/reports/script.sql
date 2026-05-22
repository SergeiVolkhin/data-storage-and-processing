-- 1.Вывести распределение (количество) клиентов по сферам деятельности, отсортировав результат по убыванию количества.
SELECT
    c.job_industry_category,
    COUNT(c.customer_id) AS customer_cnt
FROM shop_db.customer c
WHERE c.job_industry_category IS NOT NULL
GROUP BY c.job_industry_category
ORDER BY customer_cnt DESC;

-- 2.Найти общую сумму дохода (list_price*quantity) по всем подтвержденным заказам за каждый месяц по сферам деятельности клиентов. Отсортировать результат по году, месяцу и сфере деятельности.
SELECT
	EXTRACT(YEAR FROM o.order_date) AS report_year,
	EXTRACT(MONTH FROM o.order_date) AS report_month,
	c.job_industry_category,
	SUM(oi.quantity * oi.item_list_price_at_sale) AS total_revenue
FROM shop_db.orders o
	JOIN shop_db.order_items oi ON o.order_id = oi.order_id
	JOIN shop_db.customer c ON o.customer_id = c.customer_id
WHERE o.order_status = 'Approved'
GROUP BY report_year, report_month, c.job_industry_category
ORDER BY report_year, report_month, c.job_industry_category;

-- 3.Вывести количество уникальных онлайн-заказов для всех брендов в рамках подтвержденных заказов клиентов из сферы IT. Включить бренды, у которых нет онлайн-заказов от IT-клиентов, — для них должно быть указано количество 0.
SELECT
	p.brand,
	COUNT(DISTINCT CASE
		WHEN c.job_industry_category = 'IT' AND o.order_status = 'Approved' AND o.online_order = 'True' THEN o.order_id
	ELSE NULL
    END) AS it_online_order_cnt
FROM shop_db.product p
	LEFT JOIN shop_db.order_items oi ON p.product_id = oi.product_id
	LEFT JOIN shop_db.orders o ON oi.order_id = o.order_id
	LEFT JOIN shop_db.customer c ON o.customer_id = c.customer_id
WHERE p.brand IS NOT NULL
GROUP BY p.brand
ORDER BY it_online_order_cnt DESC;

-- 4.Найти по всем клиентам: сумму всех заказов (общего дохода), максимум, минимум и количество заказов, а также среднюю сумму заказа по каждому клиенту. Отсортировать результат по убыванию суммы всех заказов и количества заказов. Выполнить двумя способами: используя только GROUP BY и используя только оконные функции. Сравнить результат.
-- Способ 1: Использование GROUP BY
WITH order_totals AS (
	SELECT
		o.customer_id,
		o.order_id,
		SUM(oi.quantity * oi.item_list_price_at_sale) AS order_value
    FROM shop_db.orders o
    	JOIN shop_db.order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Approved'
    GROUP BY o.customer_id, o.order_id
)
SELECT
    ot.customer_id,
    SUM(ot.order_value) AS total_revenue,
    MAX(ot.order_value) AS max_order_value,
    MIN(ot.order_value) AS min_order_value,
    COUNT(ot.order_id) AS orders_count,
    ROUND(AVG(ot.order_value), 2) AS avg_order_value
FROM order_totals ot
GROUP BY ot.customer_id 
ORDER BY total_revenue DESC, orders_count DESC;

-- Способ 2: Использование оконных функций
WITH order_totals AS (
    SELECT
        o.customer_id,
        o.order_id,
        SUM(oi.quantity * oi.item_list_price_at_sale) AS order_value
    FROM shop_db.orders o
    JOIN shop_db.order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Approved'
    GROUP BY o.customer_id, o.order_id
)
SELECT DISTINCT
    ot.customer_id,
    SUM(ot.order_value) OVER(PARTITION BY customer_id) AS total_revenue,
    MAX(ot.order_value) OVER(PARTITION BY customer_id) AS max_order_value,
    MIN(ot.order_value) OVER(PARTITION BY customer_id) AS min_order_value,
    COUNT(ot.order_id) OVER(PARTITION BY customer_id) AS orders_count,
    ROUND(AVG(ot.order_value) OVER(PARTITION BY customer_id), 2) AS avg_order_value
FROM order_totals ot
ORDER BY total_revenue DESC, orders_count DESC;

-- 5.Найти имена и фамилии клиентов с топ-3 минимальной и топ-3 максимальной суммой транзакций за весь период (учесть клиентов, у которых нет заказов, приняв их сумму транзакций за 0).
WITH customer_totals AS (
	SELECT
		c.first_name,
		c.last_name,
		COALESCE(SUM(oi.quantity * oi.item_list_price_at_sale), 0) AS total_amount
    FROM shop_db.customer c
    	LEFT JOIN shop_db.orders o ON c.customer_id = o.customer_id AND o.order_status = 'Approved'
    	LEFT JOIN shop_db.order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id, c.first_name, c.last_name
)
(SELECT 'MAX' AS type, st.first_name, st.last_name, st.total_amount FROM customer_totals st ORDER BY st.total_amount DESC LIMIT 3)
UNION ALL
(SELECT 'MIN' AS type, st.first_name, st.last_name, st.total_amount FROM customer_totals st ORDER BY st.total_amount ASC LIMIT 3);

-- 6.Вывести только вторые транзакции клиентов (если они есть) с помощью оконных функций. Если у клиента меньше двух транзакций, он не должен попасть в результат.
WITH ranked_transactions AS (
	SELECT
		s.order_id,
		s.customer_id,
		s.order_date,
		s.order_status,
		ROW_NUMBER() OVER(PARTITION BY s.customer_id ORDER BY s.order_date, s.order_id) AS transaction_rank
	FROM shop_db.orders s
)
SELECT
	rt.order_id,
	rt.customer_id,
	rt.order_date,
	rt.order_status
FROM ranked_transactions rt
where rt.transaction_rank = 2;

-- 7.Вывести имена, фамилии и профессии клиентов, а также длительность максимального интервала (в днях) между двумя последовательными заказами. Исключить клиентов, у которых только один или меньше заказов.
WITH order_intervals AS (
	SELECT
		s.customer_id,
		s.order_date,
		LAG(s.order_date) OVER(PARTITION BY customer_id ORDER BY order_date) as prev_order_date
	FROM shop_db.orders s
	WHERE order_status = 'Approved'
)
SELECT
    c.first_name,
    c.last_name,
    c.job_title,
    MAX(oi.order_date - oi.prev_order_date) AS max_days_between_orders
FROM order_intervals oi
	JOIN shop_db.customer c ON oi.customer_id = c.customer_id
WHERE oi.prev_order_date IS NOT NULL
GROUP BY c.customer_id, c.first_name, c.last_name, c.job_title
HAVING COUNT(oi.prev_order_date) >= 1
ORDER BY max_days_between_orders DESC;

-- 8.Найти топ-5 клиентов (по общему доходу) в каждом сегменте благосостояния (wealth_segment). Вывести имя, фамилию, сегмент и общий доход. Если в сегменте менее 5 клиентов, вывести всех.
WITH customer_revenue AS (
	SELECT
		c.customer_id,
		c.first_name,
		c.last_name,
		c.wealth_segment,
		SUM(oi.quantity * oi.item_list_price_at_sale) AS total_revenue
    FROM shop_db.customer c
		JOIN shop_db.orders o ON c.customer_id = o.customer_id
		JOIN shop_db.order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'Approved'
    GROUP BY c.customer_id, c.first_name, c.last_name, c.wealth_segment
),
ranked_customers AS (
    SELECT
        cr.first_name,
        cr.last_name,
        cr.wealth_segment,
        cr.total_revenue,
        ROW_NUMBER() OVER(PARTITION BY wealth_segment ORDER BY total_revenue DESC) AS rank_in_segment
    FROM customer_revenue cr
)
SELECT
    first_name,
    last_name,
    wealth_segment,
    total_revenue
FROM ranked_customers rs
WHERE rs.rank_in_segment <= 5
ORDER BY wealth_segment, total_revenue DESC;