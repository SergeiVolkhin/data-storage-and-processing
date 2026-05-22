-- 1.Вывести все уникальные бренды, у которых есть хотя бы один продукт со стандартной стоимостью выше 1500 долларов, и суммарными продажами не менее 1000 единиц.
SELECT p.brand
FROM shop_db.product p
	JOIN shop_db.order_items oi ON p.product_id = oi.product_id
WHERE p.standard_cost > 1500
GROUP BY p.brand
HAVING SUM(oi.quantity) >= 1000;

-- 2.Для каждого дня в диапазоне с 2017-04-01 по 2017-04-09 включительно вывести количество подтвержденных онлайн-заказов и количество уникальных клиентов, совершивших эти заказы.
SELECT 
	s.order_date,
	COUNT(DISTINCT s.order_id) AS cnt_order,
	COUNT(DISTINCT s.customer_id) AS cnt_customers
FROM shop_db.orders s
WHERE s.order_date BETWEEN '2017-04-01' AND '2017-04-09'
	AND s.order_status = 'Approved'
	AND s.online_order IS TRUE
GROUP BY s.order_date
ORDER BY s.order_date;

-- 3.Вывести профессии клиентов:
-- из сферы IT, чья профессия начинается с Senior;
-- из сферы Financial Services, чья профессия начинается с Lead.
-- Для обеих групп учитывать только клиентов старше 35 лет. Объединить выборки с помощью UNION ALL.
SELECT s.job_title
FROM shop_db.customer s
WHERE s.job_industry_category = 'IT'
  AND s.job_title LIKE 'Senior%'
  AND EXTRACT(YEAR FROM AGE(dob)) > 35

UNION ALL

SELECT s.job_title
FROM shop_db.customer s
WHERE s.job_industry_category = 'Financial Services'
 	AND s.job_title LIKE 'Lead%'
  	AND EXTRACT(YEAR FROM AGE(dob)) > 35;

-- 4. Вывести бренды, которые были куплены клиентами из сферы Financial Services, но не были куплены клиентами из сферы IT.
SELECT DISTINCT p.brand
FROM shop_db.product p
	JOIN shop_db.order_items oi ON p.product_id = oi.product_id
	JOIN shop_db.orders o ON oi.order_id = o.order_id
	JOIN shop_db.customer c ON o.customer_id = c.customer_id
WHERE c.job_industry_category = 'Financial Services'

EXCEPT

SELECT DISTINCT p.brand
FROM shop_db.product p
	JOIN shop_db.order_items oi ON p.product_id = oi.product_id
	JOIN shop_db.orders o ON oi.order_id = o.order_id
	JOIN shop_db.customer c ON o.customer_id = c.customer_id
WHERE c.job_industry_category = 'IT';


-- 5.Вывести 10 клиентов (ID, имя, фамилия), которые совершили наибольшее количество онлайн-заказов (в штуках) брендов Giant Bicycles, Norco Bicycles, Trek Bicycles, при условии, что они активны и имеют оценку имущества (property_valuation) выше среднего среди клиентов из того же штата.
SELECT 
	c.customer_id,
	c.first_name,
	c.last_name,
	COUNT(oi.order_item_id) AS cnt_orders_online
FROM shop_db.customer c
	JOIN shop_db.orders o ON c.customer_id = o.customer_id
	JOIN shop_db.order_items oi ON o.order_id = oi.order_id
	JOIN shop_db.product p ON oi.product_id = p.product_id
WHERE p.brand IN ('Giant Bicycles', 'Norco Bicycles', 'Trek Bicycles')
	AND o.online_order IS TRUE
    AND c.deceased_indicator = 'N'
	AND c.property_valuation > (
		SELECT AVG(c2.property_valuation)
		FROM shop_db.customer c2
		WHERE c2.state = c.state
	)
GROUP BY c.customer_id
ORDER BY cnt_orders_online DESC
LIMIT 10;

-- 6.Вывести всех клиентов (ID, имя, фамилия), у которых нет подтвержденных онлайн-заказов за последний год, но при этом они владеют автомобилем и их сегмент благосостояния не Mass Customer.
SELECT 
    c.customer_id, 
    c.first_name, 
    c.last_name
FROM shop_db.customer c
WHERE c.owns_car = 'Yes'
	AND c.wealth_segment != 'Mass Customer'
	AND NOT EXISTS (
        SELECT 1
        FROM shop_db.orders o
        WHERE o.customer_id = c.customer_id
          AND o.online_order = TRUE
          AND o.order_status = 'Approved'
          AND o.order_date >= (CURRENT_DATE - INTERVAL '1 year')
    );


-- 7.Вывести всех клиентов из сферы 'IT' (ID, имя, фамилия), которые купили 2 из 5 продуктов с самой высокой list_price в продуктовой линейке Road.
WITH top_road_products AS (
	SELECT product_id
	FROM shop_db.product
	WHERE product_line = 'Road'
	ORDER BY list_price DESC
	LIMIT 5
)
SELECT 
	c.customer_id, 
	c.first_name, 
	c.last_name
FROM shop_db.customer c
	JOIN shop_db.orders o ON c.customer_id = o.customer_id
	JOIN shop_db.order_items oi ON o.order_id = oi.order_id
WHERE c.job_industry_category = 'IT'
	AND o.order_status = 'Approved'
	AND oi.product_id IN (SELECT product_id FROM top_road_products)
GROUP BY c.customer_id
HAVING COUNT(DISTINCT oi.product_id) = 2;

-- 8. Вывести клиентов (ID, имя, фамилия, сфера деятельности) из сфер IT или Health, которые совершили не менее 3 подтвержденных заказов в период 2017-01-01 по 2017-03-01, и при этом их общий доход от этих заказов превышает 10 000 долларов.
-- Разделить вывод на две группы (IT и Health) с помощью UNION.

SELECT 
	c.customer_id, 
	c.first_name, 
	c.last_name, 
	c.job_industry_category
FROM shop_db.customer c
	JOIN shop_db.orders o ON c.customer_id = o.customer_id
	JOIN shop_db.order_items oi ON o.order_id = oi.order_id
WHERE c.job_industry_category = 'IT'
	AND o.order_date BETWEEN '2017-01-01' AND '2017-03-01'
	AND o.order_status = 'Approved'
GROUP BY c.customer_id, c.job_industry_category
HAVING COUNT(DISTINCT o.order_id) >= 3 
	AND SUM(oi.quantity * oi.item_list_price_at_sale) > 10000

UNION

SELECT 
	c.customer_id, 
	c.first_name, 
	c.last_name, 
	c.job_industry_category
FROM shop_db.customer c
JOIN shop_db.orders o ON c.customer_id = o.customer_id
JOIN shop_db.order_items oi ON o.order_id = oi.order_id
WHERE c.job_industry_category = 'Health'
  AND o.order_date BETWEEN '2017-01-01' AND '2017-03-01'
  AND o.order_status = 'Approved'
GROUP BY c.customer_id, c.job_industry_category
HAVING COUNT(DISTINCT o.order_id) >= 3 
   AND SUM(oi.quantity * oi.item_list_price_at_sale) > 10000;
