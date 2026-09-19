from database.seed import build_seed_plan, validate_plan


def test_seed_plan_has_valid_and_intentional_business_signals() -> None:
    plan = build_seed_plan()
    metrics = validate_plan(plan)

    assert len(plan.customers) == 800
    assert len(plan.products) == 24
    assert metrics["august_revenue"] > metrics["july_revenue"]
    assert metrics["september_revenue"] < metrics["august_revenue"]
    assert metrics["september_electronics_revenue"] < metrics["august_electronics_revenue"]
    assert metrics["september_north_orders"] < metrics["august_north_orders"]
    assert metrics["september_refunds"] > metrics["august_refunds"]
