-- Enable pg_stat_statements extension for query monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create a sample table for testing
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    price DECIMAL(10, 2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending'
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

-- Insert some sample data
INSERT INTO orders (customer_id, product_name, quantity, price, status)
SELECT 
    (random() * 1000)::INTEGER,
    'Product ' || generate_series,
    (random() * 10 + 1)::INTEGER,
    (random() * 100 + 10)::DECIMAL(10, 2),
    CASE (random() * 3)::INTEGER 
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'completed'
        ELSE 'shipped'
    END
FROM generate_series(1, 10000);

-- Create a function to generate load (for testing)
CREATE OR REPLACE FUNCTION generate_load(n INTEGER DEFAULT 1000)
RETURNS VOID AS $$
BEGIN
    FOR i IN 1..n LOOP
        INSERT INTO orders (customer_id, product_name, quantity, price)
        VALUES (
            (random() * 1000)::INTEGER,
            'LoadTest Product ' || i,
            (random() * 10 + 1)::INTEGER,
            (random() * 100 + 10)::DECIMAL(10, 2)
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions for monitoring
GRANT SELECT ON ALL TABLES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;
