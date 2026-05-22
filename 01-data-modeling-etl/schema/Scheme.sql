CREATE SCHEMA IF NOT EXISTS shop_db;

CREATE TABLE IF NOT EXISTS shop_db.countries (
    id serial PRIMARY KEY,
    country_name varchar UNIQUE NOT NULL
);
COMMENT ON TABLE shop_db.countries IS 'Справочник стран';

CREATE TABLE IF NOT EXISTS shop_db.states (
    id serial PRIMARY KEY,
    state_name varchar NOT NULL,
    country_id int NOT NULL,
    FOREIGN KEY (country_id) REFERENCES shop_db.countries(id)
);
COMMENT ON TABLE shop_db.states IS 'Справочник штатов/регионов';

CREATE TABLE IF NOT EXISTS shop_db.postcodes (
    postcode VARCHAR PRIMARY KEY,
    state_id INT NOT NULL,
    FOREIGN KEY (state_id) REFERENCES shop_db.states(id)
);
COMMENT ON TABLE shop_db.postcodes IS 'Справочник почтовых индексов';

CREATE TABLE IF NOT EXISTS shop_db.job_industries (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR UNIQUE NOT NULL
);
COMMENT ON TABLE shop_db.job_industries IS 'Справочник сфер деятельности';

CREATE TABLE IF NOT EXISTS shop_db.wealth_segments (
    id SERIAL PRIMARY KEY,
    segment_name VARCHAR UNIQUE NOT NULL
);
COMMENT ON TABLE shop_db.wealth_segments IS 'Справочник категорий благосостояния';


CREATE TABLE IF NOT EXISTS shop_db.brands (
    id SERIAL PRIMARY KEY,
    brand_name VARCHAR UNIQUE NOT NULL
);
COMMENT ON TABLE shop_db.brands IS 'Справочник брендов';

CREATE TABLE IF NOT EXISTS shop_db.product_lines (
    id SERIAL PRIMARY KEY,
    line_name VARCHAR UNIQUE NOT NULL
);
COMMENT ON TABLE shop_db.product_lines IS 'Справочник продуктовых линеек';

CREATE TABLE IF NOT EXISTS shop_db.product_classes (
    id SERIAL PRIMARY KEY,
    class_name VARCHAR UNIQUE NOT NULL
);
COMMENT ON TABLE shop_db.product_classes IS 'Справочник классов продукта (high, medium, low)';

CREATE TABLE IF NOT EXISTS shop_db.product_sizes (
    id SERIAL PRIMARY KEY,
    size_name VARCHAR UNIQUE NOT NULL
);
COMMENT ON TABLE shop_db.product_sizes IS 'Справочник размеров продукта';

CREATE TABLE IF NOT EXISTS shop_db.order_statuses (
    id SERIAL PRIMARY KEY,
    status_name VARCHAR UNIQUE NOT NULL
);
COMMENT ON TABLE shop_db.order_statuses IS 'Справочник статусов заказа';

CREATE TABLE IF NOT EXISTS shop_db.customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NULL,
    gender CHAR(1) DEFAULT 'U',
    DOB DATE NULL,
    job_title VARCHAR NULL,
    job_industry_category_id INT NULL,
    wealth_segment_id INT NOT NULL,
    deceased_indicator BOOLEAN NOT NULL DEFAULT false,
    owns_car BOOLEAN NOT NULL DEFAULT false,
    address VARCHAR NULL,
    postcode VARCHAR NULL,
    property_valuation SMALLINT NULL,
    
    FOREIGN KEY (job_industry_category_id) REFERENCES shop_db.job_industries(id),
    FOREIGN KEY (wealth_segment_id) REFERENCES shop_db.wealth_segments(id),
    FOREIGN KEY (postcode) REFERENCES shop_db.postcodes(postcode)
);
COMMENT ON TABLE shop_db.customers IS 'Клиенты';
COMMENT ON COLUMN shop_db.customers.first_name IS 'Имя';
COMMENT ON COLUMN shop_db.customers.last_name IS 'Фамилия';
COMMENT ON COLUMN shop_db.customers.gender IS 'Пол (M, F, U - Unknown)';
COMMENT ON COLUMN shop_db.customers.DOB IS 'Дата рождения';
COMMENT ON COLUMN shop_db.customers.job_title IS 'Должность';
COMMENT ON COLUMN shop_db.customers.deceased_indicator IS 'Статус (Жив/Умер)';
COMMENT ON COLUMN shop_db.customers.owns_car IS 'Наличие автомобиля';
COMMENT ON COLUMN shop_db.customers.address IS 'Адресс';
COMMENT ON COLUMN shop_db.customers.property_valuation IS 'Оценка недвижимости';

CREATE TABLE IF NOT EXISTS shop_db.products (
    product_id INT PRIMARY KEY,
    brand_id INT NOT NULL,
    product_line_id INT NOT NULL,
    product_class_id INT NOT NULL,
    product_size_id INT NOT NULL,
    list_price DECIMAL(10, 2) DEFAULT 0,
    standard_cost DECIMAL(10, 2) DEFAULT 0,
    
    FOREIGN KEY (brand_id) REFERENCES shop_db.brands(id),
    FOREIGN KEY (product_line_id) REFERENCES shop_db.product_lines(id),
    FOREIGN KEY (product_class_id) REFERENCES shop_db.product_classes(id),
    FOREIGN KEY (product_size_id) REFERENCES shop_db.product_sizes(id)
);
COMMENT ON TABLE shop_db.products IS 'Каталог продуктов и их характеристики';
COMMENT ON COLUMN shop_db.products.product_id IS 'Это id из csv, он не авто-инкрементный';
COMMENT ON COLUMN shop_db.products.list_price IS 'Розничная цена';
COMMENT ON COLUMN shop_db.products.standard_cost IS 'Себестоимость';

CREATE TABLE IF NOT EXISTS shop_db.transactions (
    transaction_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    customer_id INT NOT NULL,
    transaction_date DATE NOT NULL,
    online_order BOOLEAN NULL,
    order_status_id INT NOT NULL,
    
    FOREIGN KEY (product_id) REFERENCES shop_db.products(product_id),
    FOREIGN KEY (customer_id) REFERENCES shop_db.customers(customer_id),
    FOREIGN KEY (order_status_id) REFERENCES shop_db.order_statuses(id)
);
COMMENT ON COLUMN shop_db.transactions.transaction_date IS 'Дата транзакции';
COMMENT ON COLUMN shop_db.transactions.online_order IS 'True - онлайн, False - офлайн, NULL - неизвестно';