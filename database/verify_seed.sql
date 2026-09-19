DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        GROUP BY o.order_id, o.total_amount
        HAVING o.total_amount <> COALESCE(SUM(oi.quantity * oi.unit_price), 0)
    ) THEN
        RAISE EXCEPTION 'Seed validation failed: an order total differs from its item totals.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM refunds r
        JOIN orders o ON o.order_id = r.order_id
        GROUP BY r.order_id, o.total_amount
        HAVING SUM(r.amount) > o.total_amount
    ) THEN
        RAISE EXCEPTION 'Seed validation failed: refunds exceed an order total.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM refunds r
        JOIN orders o ON o.order_id = r.order_id
        WHERE o.status <> 'completed'
    ) THEN
        RAISE EXCEPTION 'Seed validation failed: a non-completed order has a refund.';
    END IF;

    IF (
        SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'completed' AND order_date >= DATE '2026-08-01' AND order_date < DATE '2026-09-01'
    ) <= (
        SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'completed' AND order_date >= DATE '2026-07-01' AND order_date < DATE '2026-08-01'
    ) THEN
        RAISE EXCEPTION 'Seed validation failed: August revenue should exceed July.';
    END IF;

    IF (
        SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'completed' AND order_date >= DATE '2026-09-01' AND order_date < DATE '2026-10-01'
    ) >= (
        SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status = 'completed' AND order_date >= DATE '2026-08-01' AND order_date < DATE '2026-09-01'
    ) THEN
        RAISE EXCEPTION 'Seed validation failed: September revenue should be below August.';
    END IF;

    IF (
        SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0)
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.status = 'completed' AND p.category = 'Electronics' AND o.order_date >= DATE '2026-09-01' AND o.order_date < DATE '2026-10-01'
    ) >= (
        SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0)
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.status = 'completed' AND p.category = 'Electronics' AND o.order_date >= DATE '2026-08-01' AND o.order_date < DATE '2026-09-01'
    ) THEN
        RAISE EXCEPTION 'Seed validation failed: September Electronics revenue should be below August.';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.status = 'completed' AND c.region = 'North' AND o.order_date >= DATE '2026-09-01' AND o.order_date < DATE '2026-10-01'
    ) >= (
        SELECT COUNT(*)
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.status = 'completed' AND c.region = 'North' AND o.order_date >= DATE '2026-08-01' AND o.order_date < DATE '2026-09-01'
    ) THEN
        RAISE EXCEPTION 'Seed validation failed: September North-region completed orders should be below August.';
    END IF;

    IF (
        SELECT COALESCE(SUM(amount), 0) FROM refunds WHERE refund_date >= DATE '2026-09-01' AND refund_date < DATE '2026-10-01'
    ) <= (
        SELECT COALESCE(SUM(amount), 0) FROM refunds WHERE refund_date >= DATE '2026-08-01' AND refund_date < DATE '2026-09-01'
    ) THEN
        RAISE EXCEPTION 'Seed validation failed: September refunds should exceed August.';
    END IF;
END $$;

SELECT
    DATE_TRUNC('month', order_date)::date AS month,
    SUM(total_amount) FILTER (WHERE status = 'completed') AS completed_revenue,
    COUNT(*) AS orders_received
FROM orders
GROUP BY 1
ORDER BY 1;
