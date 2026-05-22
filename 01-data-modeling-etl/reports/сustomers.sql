-- Таблица customer
SELECT
	c.customer_id,
	c.first_name,
	c.last_name,
	c.gender,
	c.dob AS "DOB",
	c.job_title,
	ji.category_name AS job_industry_category,
	ws.segment_name AS wealth_segment,
	c.deceased_indicator,
	c.owns_car,
	c.address,
	c.postcode,
	s.state_name AS state,
	cn.country_name AS country,
	c.property_valuation
FROM shop_db.customers c
	LEFT JOIN shop_db.job_industries ji ON c.job_industry_category_id = ji.id
	LEFT JOIN shop_db.wealth_segments ws ON c.wealth_segment_id = ws.id
	LEFT JOIN shop_db.postcodes p ON c.postcode = p.postcode
	LEFT JOIN shop_db.states s ON p.state_id = s.id
	LEFT JOIN shop_db.countries cn ON s.country_id = cn.id
ORDER by c.customer_id;