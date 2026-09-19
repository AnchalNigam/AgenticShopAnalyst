"""Create deterministic, story-driven development data for AgenticShop.

Run from the repository root:
    backend/.venv/bin/python -m database.seed --dry-run
    backend/.venv/bin/python -m database.seed --apply-schema --seed
"""

from __future__ import annotations

import argparse
import os
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable


SEED = 20260901
MONEY_QUANTUM = Decimal("0.01")
PROJECT_ROOT = Path(__file__).resolve().parents[1]

CITIES_BY_REGION = {
    "North": ("Delhi", "Jaipur", "Lucknow", "Chandigarh"),
    "South": ("Bengaluru", "Chennai", "Hyderabad", "Kochi"),
    "East": ("Kolkata", "Bhubaneswar", "Guwahati", "Patna"),
    "West": ("Mumbai", "Pune", "Ahmedabad", "Surat"),
}

PRODUCT_CATALOGUE = {
    "Electronics": (
        ("Pulse Wireless Earbuds", "2499.00"),
        ("Orbit Smartwatch", "3999.00"),
        ("Nova Bluetooth Speaker", "1799.00"),
        ("Swift USB-C Charger", "899.00"),
        ("Vision Webcam", "2899.00"),
        ("Echo Mechanical Keyboard", "4599.00"),
    ),
    "Fashion": (
        ("Everyday Cotton Shirt", "1299.00"),
        ("Classic Denim Jeans", "2199.00"),
        ("Canvas Sneakers", "1899.00"),
        ("Weekend Tote Bag", "999.00"),
        ("Linen Summer Dress", "2499.00"),
        ("Trail Running Shoes", "3299.00"),
    ),
    "Home": (
        ("Aura Table Lamp", "1599.00"),
        ("Cloud Comforter Set", "2799.00"),
        ("Bamboo Storage Basket", "699.00"),
        ("Steel Water Bottle", "549.00"),
        ("Ceramic Dinner Set", "1999.00"),
        ("Indoor Plant Stand", "1499.00"),
    ),
    "Beauty": (
        ("Daily Skincare Kit", "1199.00"),
        ("Vitamin C Serum", "799.00"),
        ("Hydrating Shampoo", "499.00"),
        ("Matte Lip Colour", "599.00"),
        ("Sunscreen SPF 50", "649.00"),
        ("Wellness Gift Box", "1699.00"),
    ),
}

MONTH_PROFILES = {
    7: {
        "orders_per_day": 38,
        "region_weights": (0.35, 0.24, 0.19, 0.22),
        "category_weights": (0.36, 0.25, 0.22, 0.17),
        "refund_rate": 0.03,
    },
    8: {
        "orders_per_day": 50,
        "region_weights": (0.36, 0.23, 0.18, 0.23),
        "category_weights": (0.41, 0.23, 0.20, 0.16),
        "refund_rate": 0.03,
    },
    9: {
        "orders_per_day": 30,
        "region_weights": (0.14, 0.31, 0.26, 0.29),
        "category_weights": (0.17, 0.30, 0.28, 0.25),
        "refund_rate": 0.13,
    },
}


def money(value: Decimal | int | str | float) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Customer:
    customer_id: int
    name: str
    signup_date: date
    region: str
    city: str


@dataclass(frozen=True)
class Product:
    product_id: int
    product_name: str
    category: str
    price: Decimal


@dataclass(frozen=True)
class Order:
    order_id: int
    customer_id: int
    order_date: date
    status: str
    total_amount: Decimal


@dataclass(frozen=True)
class OrderItem:
    order_item_id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class Refund:
    refund_id: int
    order_id: int
    refund_date: date
    amount: Decimal
    reason: str


@dataclass(frozen=True)
class SeedPlan:
    customers: list[Customer]
    products: list[Product]
    orders: list[Order]
    order_items: list[OrderItem]
    refunds: list[Refund]


def choose_weighted(rng: random.Random, values: Iterable[str], weights: tuple[float, ...]) -> str:
    return rng.choices(list(values), weights=weights, k=1)[0]


def build_seed_plan() -> SeedPlan:
    rng = random.Random(SEED)
    regions = tuple(CITIES_BY_REGION)
    categories = tuple(PRODUCT_CATALOGUE)

    products: list[Product] = []
    product_id = 1
    for category, entries in PRODUCT_CATALOGUE.items():
        for product_name, price in entries:
            products.append(Product(product_id, product_name, category, money(price)))
            product_id += 1

    customers: list[Customer] = []
    first_names = ("Aarav", "Ananya", "Arjun", "Diya", "Ishaan", "Kavya", "Meera", "Rohan", "Saanvi", "Vihaan")
    last_names = ("Agarwal", "Bose", "Gupta", "Iyer", "Kapoor", "Khan", "Mehta", "Nair", "Reddy", "Sharma")
    signup_start = date(2026, 1, 1)
    for customer_id in range(1, 801):
        region = choose_weighted(rng, regions, (0.32, 0.25, 0.18, 0.25))
        customers.append(
            Customer(
                customer_id=customer_id,
                name=f"{rng.choice(first_names)} {rng.choice(last_names)}",
                signup_date=signup_start + timedelta(days=rng.randrange(273)),
                region=region,
                city=rng.choice(CITIES_BY_REGION[region]),
            )
        )

    products_by_category: dict[str, list[Product]] = defaultdict(list)
    for product in products:
        products_by_category[product.category].append(product)
    customers_by_region: dict[str, list[Customer]] = defaultdict(list)
    for customer in customers:
        customers_by_region[customer.region].append(customer)

    orders: list[Order] = []
    order_items: list[OrderItem] = []
    refunds: list[Refund] = []
    order_id = 1
    order_item_id = 1
    refund_id = 1

    for month, profile in MONTH_PROFILES.items():
        day = date(2026, month, 1)
        while day.month == month:
            daily_orders = profile["orders_per_day"] + rng.randint(-3, 3)
            for _ in range(daily_orders):
                region = choose_weighted(rng, regions, profile["region_weights"])
                eligible_customers = [customer for customer in customers_by_region[region] if customer.signup_date <= day]
                customer = rng.choice(eligible_customers)
                status = choose_weighted(rng, ("completed", "pending", "cancelled"), (0.93, 0.03, 0.04))

                line_items: list[OrderItem] = []
                for _ in range(rng.choices((1, 2, 3), weights=(0.58, 0.30, 0.12), k=1)[0]):
                    category = choose_weighted(rng, categories, profile["category_weights"])
                    product = rng.choice(products_by_category[category])
                    quantity = rng.choices((1, 2, 3), weights=(0.75, 0.20, 0.05), k=1)[0]
                    discount = Decimal(str(rng.choice(("0.90", "0.95", "1.00", "1.00", "1.00"))))
                    unit_price = money(product.price * discount)
                    line_items.append(OrderItem(order_item_id, order_id, product.product_id, quantity, unit_price))
                    order_item_id += 1

                total_amount = money(sum(item.unit_price * item.quantity for item in line_items))
                orders.append(Order(order_id, customer.customer_id, day, status, total_amount))
                order_items.extend(line_items)

                if status == "completed" and rng.random() < profile["refund_rate"]:
                    next_month = date(day.year + (day.month == 12), (day.month % 12) + 1, 1)
                    refund_date = min(day + timedelta(days=rng.randint(1, 7)), next_month - timedelta(days=1))
                    refund_amount = money(total_amount * Decimal(str(rng.choice(("0.35", "0.50", "1.00")))))
                    refunds.append(
                        Refund(refund_id, order_id, refund_date, refund_amount, rng.choice(("Damaged item", "Changed mind", "Late delivery", "Wrong item")))
                    )
                    refund_id += 1

                order_id += 1
            day += timedelta(days=1)

    return SeedPlan(customers, products, orders, order_items, refunds)


def metrics_for(plan: SeedPlan) -> dict[str, Decimal | int]:
    orders_by_id = {order.order_id: order for order in plan.orders}
    products_by_id = {product.product_id: product for product in plan.products}
    revenue_by_month: defaultdict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    category_revenue: defaultdict[tuple[int, str], Decimal] = defaultdict(lambda: Decimal("0"))
    north_orders: defaultdict[int, int] = defaultdict(int)
    customer_by_id = {customer.customer_id: customer for customer in plan.customers}
    refunds_by_month: defaultdict[int, Decimal] = defaultdict(lambda: Decimal("0"))

    for order in plan.orders:
        if order.status == "completed":
            revenue_by_month[order.order_date.month] += order.total_amount
            if customer_by_id[order.customer_id].region == "North":
                north_orders[order.order_date.month] += 1
    for item in plan.order_items:
        order = orders_by_id[item.order_id]
        if order.status == "completed":
            category_revenue[(order.order_date.month, products_by_id[item.product_id].category)] += item.unit_price * item.quantity
    for refund in plan.refunds:
        refunds_by_month[refund.refund_date.month] += refund.amount

    return {
        "july_revenue": money(revenue_by_month[7]),
        "august_revenue": money(revenue_by_month[8]),
        "september_revenue": money(revenue_by_month[9]),
        "august_electronics_revenue": money(category_revenue[(8, "Electronics")]),
        "september_electronics_revenue": money(category_revenue[(9, "Electronics")]),
        "august_north_orders": north_orders[8],
        "september_north_orders": north_orders[9],
        "august_refunds": money(refunds_by_month[8]),
        "september_refunds": money(refunds_by_month[9]),
    }


def validate_plan(plan: SeedPlan) -> dict[str, Decimal | int]:
    orders_by_id = {order.order_id: order for order in plan.orders}
    item_totals: defaultdict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    refund_totals: defaultdict[int, Decimal] = defaultdict(lambda: Decimal("0"))
    for item in plan.order_items:
        item_totals[item.order_id] += item.unit_price * item.quantity
    for refund in plan.refunds:
        if orders_by_id[refund.order_id].status != "completed":
            raise ValueError("Only completed orders can have refunds.")
        refund_totals[refund.order_id] += refund.amount
    for order in plan.orders:
        if money(item_totals[order.order_id]) != order.total_amount:
            raise ValueError(f"Order {order.order_id} total does not match its item lines.")
        if refund_totals[order.order_id] > order.total_amount:
            raise ValueError(f"Refunds exceed total for order {order.order_id}.")

    metrics = metrics_for(plan)
    if not metrics["august_revenue"] > metrics["july_revenue"] > 0:
        raise ValueError("August revenue must exceed July revenue.")
    if not metrics["september_revenue"] < metrics["august_revenue"]:
        raise ValueError("September revenue must fall below August revenue.")
    if not metrics["september_electronics_revenue"] < metrics["august_electronics_revenue"]:
        raise ValueError("September Electronics revenue must fall below August.")
    if not metrics["september_north_orders"] < metrics["august_north_orders"]:
        raise ValueError("September North orders must fall below August.")
    if not metrics["september_refunds"] > metrics["august_refunds"]:
        raise ValueError("September refunds must exceed August refunds.")
    return metrics


def load_database_url() -> str:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing from .env.")
    return database_url


def apply_schema() -> None:
    import psycopg

    schema = (PROJECT_ROOT / "database" / "001_v1_schema.sql").read_text()
    with psycopg.connect(load_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.customers')")
            if cursor.fetchone()[0] is not None:
                raise RuntimeError("Schema already exists; no changes were made.")
            cursor.execute(schema)


def seed_database(plan: SeedPlan) -> None:
    import psycopg

    with psycopg.connect(load_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.customers')")
            if cursor.fetchone()[0] is None:
                raise RuntimeError("Schema is missing. Run with --apply-schema first.")
            cursor.execute("SELECT EXISTS (SELECT 1 FROM customers)")
            if cursor.fetchone()[0]:
                raise RuntimeError("Customers already exist; seeding stopped to protect existing data.")

            cursor.executemany(
                "INSERT INTO customers (customer_id, name, signup_date, region, city) VALUES (%s, %s, %s, %s, %s)",
                [(row.customer_id, row.name, row.signup_date, row.region, row.city) for row in plan.customers],
            )
            cursor.executemany(
                "INSERT INTO products (product_id, product_name, category, price) VALUES (%s, %s, %s, %s)",
                [(row.product_id, row.product_name, row.category, row.price) for row in plan.products],
            )
            cursor.executemany(
                "INSERT INTO orders (order_id, customer_id, order_date, status, total_amount) VALUES (%s, %s, %s, %s, %s)",
                [(row.order_id, row.customer_id, row.order_date, row.status, row.total_amount) for row in plan.orders],
            )
            cursor.executemany(
                "INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s, %s)",
                [(row.order_item_id, row.order_id, row.product_id, row.quantity, row.unit_price) for row in plan.order_items],
            )
            cursor.executemany(
                "INSERT INTO refunds (refund_id, order_id, refund_date, amount, reason) VALUES (%s, %s, %s, %s, %s)",
                [(row.refund_id, row.order_id, row.refund_date, row.amount, row.reason) for row in plan.refunds],
            )
            for table, column in (
                ("customers", "customer_id"),
                ("products", "product_id"),
                ("orders", "order_id"),
                ("order_items", "order_item_id"),
                ("refunds", "refund_id"),
            ):
                cursor.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), (SELECT MAX({column}) FROM {table}))"
                )


def verify_seed() -> list[tuple[date, Decimal, int]]:
    """Run database-side assertions and return the monthly summary query."""
    import psycopg

    validation_sql = (PROJECT_ROOT / "database" / "verify_seed.sql").read_text()
    with psycopg.connect(load_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(validation_sql)
            if not cursor.nextset():
                raise RuntimeError("Seed validation did not return its monthly summary.")
            return cursor.fetchall()


def print_summary(plan: SeedPlan, metrics: dict[str, Decimal | int]) -> None:
    print(f"Planned rows: {len(plan.customers)} customers, {len(plan.products)} products, {len(plan.orders)} orders, {len(plan.order_items)} order items, {len(plan.refunds)} refunds")
    print("Known business signals:")
    for label in (
        "july_revenue",
        "august_revenue",
        "september_revenue",
        "august_electronics_revenue",
        "september_electronics_revenue",
        "august_north_orders",
        "september_north_orders",
        "august_refunds",
        "september_refunds",
    ):
        print(f"  {label}: {metrics[label]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AgenticShop deterministic development-data seeder")
    parser.add_argument("--apply-schema", action="store_true", help="Create the V1 schema only if it is currently absent.")
    parser.add_argument("--seed", action="store_true", help="Insert data only if customers is empty.")
    parser.add_argument("--verify", action="store_true", help="Run database-side assertions against existing seed data.")
    args = parser.parse_args()

    plan = build_seed_plan()
    metrics = validate_plan(plan)
    if args.apply_schema:
        apply_schema()
        print("V1 schema created.")
    if args.seed:
        seed_database(plan)
        print("Seed data inserted.")
    if args.verify:
        monthly_summary = verify_seed()
        print("Database assertions passed.")
        for month, revenue, order_count in monthly_summary:
            print(f"  {month}: completed revenue={revenue}, orders received={order_count}")
    print_summary(plan, metrics)


if __name__ == "__main__":
    main()
