"""Unit and integration tests for the deterministic Financial Projection Engine."""

import pytest
from app.schemas.financial import FinancialAssumptions, FinancialSaveRequest
from app.services.financial_service import (
    calculate_break_even,
    calculate_monthly_projections,
    compute_full_financial_model,
    generate_scenarios,
)


def test_deterministic_revenue_and_margins():
    """Verify exact known revenue, variable costs, and contribution margin math."""
    assumptions = FinancialAssumptions(
        currency="USD",
        starting_cash=5000.0,
        one_time_startup_costs=1000.0,
        monthly_fixed_expenses=1000.0,
        marketing_expenditure=500.0,
        salaries_costs=2000.0,
        selling_price=100.0,
        variable_cost_per_unit=20.0,
        expected_sales_volume=50,
        monthly_growth_rate_pct=0.0,  # 0% growth for constant baseline verification
        payment_processing_pct=3.0,
        tax_rate_pct=20.0,
        forecast_months=12,
    )

    # 1. Break-even check
    # Selling price = 100, variable cost = 20, fee = 3% of 100 = 3.0
    # Contribution per unit = 100 - 20 - 3 = 77.0
    # Total fixed monthly burn = 1000 + 500 + 2000 = 3500.0
    # Break-even units = ceil(3500 / 77) = ceil(45.4545) = 46 units
    be = calculate_break_even(assumptions)
    assert be.contribution_margin_per_unit == 77.0
    assert be.contribution_margin_ratio == 0.77
    assert be.monthly_fixed_operating_costs == 3500.0
    assert be.break_even_units_per_month == 46
    assert be.break_even_revenue_per_month == 4600.0
    assert be.is_break_even_achievable is True

    # 2. Monthly projections
    # Units = 50. Revenue = 50 * 100 = 5000.0
    # Direct var = 50 * 20 = 1000.0, Fees = 5000 * 0.03 = 150.0. Total var = 1150.0
    # Gross profit = 5000 - 1150 = 3850.0
    # Operating expenses = 3500.0
    # Operating profit = 3850 - 3500 = 350.0
    # Tax = 20% of 350 = 70.0
    # Net profit = 350 - 70 = 280.0
    monthly, summary = calculate_monthly_projections(assumptions)
    assert len(monthly) == 12

    m1 = monthly[0]
    assert m1.month == 1
    assert m1.units_sold == 50
    assert m1.revenue == 5000.0
    assert m1.direct_variable_costs == 1000.0
    assert m1.payment_fees == 150.0
    assert m1.total_variable_costs == 1150.0
    assert m1.gross_profit == 3850.0
    assert m1.operating_profit == 350.0
    assert m1.tax_expense == 70.0
    assert m1.net_profit == 280.0

    # Month 1 cash flow:
    # Opening cash = 5000. Inflow = 5000.
    # Outflow = 1150 + 3500 + 70 + 1000 (startup) = 5720.0
    # Net cash flow = 5000 - 5720 = -720.0
    # Closing cash = 5000 - 720 = 4280.0
    assert m1.opening_cash == 5000.0
    assert m1.cash_outflows == 5720.0
    assert m1.net_cash_flow == -720.0
    assert m1.closing_cash == 4280.0

    # Month 2 cash flow:
    # No startup costs. Outflow = 1150 + 3500 + 70 = 4720.0
    # Net cash flow = 5000 - 4720 = +280.0
    # Closing cash = 4280 + 280 = 4560.0
    m2 = monthly[1]
    assert m2.opening_cash == 4280.0
    assert m2.cash_outflows == 4720.0
    assert m2.net_cash_flow == 280.0
    assert m2.closing_cash == 4560.0


def test_break_even_negative_contribution_margin():
    """Verify that when COGS exceed price, break-even safely flags unachievable."""
    assumptions = FinancialAssumptions(
        selling_price=10.0,
        variable_cost_per_unit=15.0,  # Costs more than price
        expected_sales_volume=10,
        payment_processing_pct=3.0,
    )
    be = calculate_break_even(assumptions)
    assert be.contribution_margin_per_unit < 0
    assert be.is_break_even_achievable is False
    assert be.break_even_units_per_month is None
    assert be.break_even_revenue_per_month is None
    assert "exceed the selling price" in be.advisory_note


def test_scenario_generation():
    """Verify 3 distinct scenarios are generated with explicit assumption changes."""
    base = FinancialAssumptions(
        selling_price=50.0,
        variable_cost_per_unit=10.0,
        expected_sales_volume=100,
        monthly_growth_rate_pct=10.0,
    )
    scenarios = generate_scenarios(base)
    assert "conservative" in scenarios
    assert "expected" in scenarios
    assert "optimistic" in scenarios

    cons = scenarios["conservative"]
    exp = scenarios["expected"]
    opt = scenarios["optimistic"]

    # Conservative revenue < Expected < Optimistic
    assert cons.summary.total_revenue < exp.summary.total_revenue < opt.summary.total_revenue
    # Conservative sales units < Expected < Optimistic
    assert cons.monthly_projections[0].units_sold < exp.monthly_projections[0].units_sold < opt.monthly_projections[0].units_sold


def test_financial_api_endpoints_disabled(client):
    """Verify that financial planning endpoints are no longer registered on the API router."""
    # 1. Register and login
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "username": "cfo_user",
            "email": "cfo@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "display_name": "CFO User",
            "terms_accepted": True,
            "privacy_acknowledged": True,
        },
    )
    assert reg_resp.status_code == 201

    # 2. Create project
    proj_resp = client.post(
        "/api/projects",
        json={
            "name": "Fintech Platform",
            "idea_description": "Automated billing and finance platform for micro-consultants.",
            "industry": "Fintech",
            "business_stage": "prototype",
        },
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["data"]["id"]

    # 3. Verify POST /financial/calculate is not an active endpoint (returns 404 or 405)
    calc_resp = client.post(
        f"/api/projects/{proj_id}/financial/calculate",
        json={
            "assumptions": {
                "currency": "EUR",
                "selling_price": 80.0,
                "variable_cost_per_unit": 10.0,
                "expected_sales_volume": 60,
                "forecast_months": 12,
            }
        },
    )
    assert calc_resp.status_code in (404, 405)

    # 4. Verify POST /financial is not an active endpoint
    save_resp = client.post(
        f"/api/projects/{proj_id}/financial",
        json={
            "name": "Series A Plan",
            "assumptions": {
                "currency": "EUR",
                "starting_cash": 25000.0,
                "one_time_startup_costs": 5000.0,
                "monthly_fixed_expenses": 2000.0,
                "salaries_costs": 4000.0,
                "marketing_expenditure": 1000.0,
                "selling_price": 120.0,
                "variable_cost_per_unit": 15.0,
                "expected_sales_volume": 80,
                "monthly_growth_rate_pct": 8.0,
                "forecast_months": 12,
            },
        },
    )
    assert save_resp.status_code in (404, 405)

    # 5. Verify GET /financial is not an active endpoint
    get_resp = client.get(f"/api/projects/{proj_id}/financial")
    assert get_resp.status_code in (404, 405)

    # 6. Verify GET /financial/versions is not an active endpoint
    ver_resp = client.get(f"/api/projects/{proj_id}/financial/versions")
    assert ver_resp.status_code in (404, 405)


def test_financial_schema_alias_and_percentage_normalization():
    """Verify that frontend field names and decimal percentages are automatically converted."""
    frontend_raw_dict = {
        "currency": "USD",
        "starting_cash": 20000.0,
        "initial_equipment_costs": 4000.0,
        "monthly_fixed_costs": 1500.0,
        "monthly_salaries": 3500.0,
        "monthly_marketing_budget": 800.0,
        "selling_price": 50.0,
        "variable_cost_per_unit": 10.0,
        "initial_monthly_volume": 100,
        "monthly_growth_rate": 0.12,  # 12% decimal
        "payment_processing_rate": 0.029,  # 2.9% decimal
        "tax_rate": 0.20,  # 20% decimal
        "forecast_months": 12,
    }

    assumptions = FinancialAssumptions.model_validate(frontend_raw_dict)
    assert assumptions.one_time_startup_costs == 4000.0
    assert assumptions.monthly_fixed_expenses == 1500.0
    assert assumptions.salaries_costs == 3500.0
    assert assumptions.marketing_expenditure == 800.0
    assert assumptions.expected_sales_volume == 100
    assert assumptions.monthly_growth_rate_pct == 12.0
    assert assumptions.payment_processing_pct == 2.9
    assert assumptions.tax_rate_pct == 20.0


def test_direct_service_calculation():
    """Verify pure calculation service compute_full_financial_model remains functional."""
    assumptions = FinancialAssumptions(
        currency="USD",
        starting_cash=10000.0,
        selling_price=50.0,
        variable_cost_per_unit=10.0,
        expected_sales_volume=100,
        monthly_growth_rate_pct=5.0,
        forecast_months=12,
    )
    model_data = compute_full_financial_model(assumptions, project_id="proj-123")
    assert model_data.currency == "USD"
    assert len(model_data.monthly_projections) == 12
    assert model_data.summary is not None
    assert model_data.break_even is not None


def test_cogs_excludes_payment_fees():
    """Verify that cogs strictly excludes payment fees when payment processing is represented separately."""
    assumptions = FinancialAssumptions(
        selling_price=100.0,
        variable_cost_per_unit=25.0,
        expected_sales_volume=10,
        payment_processing_pct=3.0,
        forecast_months=3,
    )
    monthly, _ = calculate_monthly_projections(assumptions)
    m1 = monthly[0]
    # Direct variable cost = 10 * 25 = 250.0
    # Payment fee = 1000 * 0.03 = 30.0
    # Total variable cost = 280.0
    assert m1.direct_variable_costs == 250.0
    assert m1.payment_fees == 30.0
    assert m1.total_variable_costs == 280.0
    assert m1.cogs == 250.0
    assert m1.cogs != m1.total_variable_costs


def test_runway_accounts_for_cash_over_time_without_one_time_startup_burn_distortion():
    """Verify runway accounts for projected cash over time and does not treat one-time startup expenses as recurring burn."""
    # Scenario A: Profitable business after Month 1 startup cost
    # Starting cash = 30000. Month 1 startup cost = 10000.
    # Revenue = 10000/mo, operating fixed = 2000, direct var = 1000. Monthly net profit ~ 5600.
    # Month 1 net cash flow is negative due to $10,000 startup cost, but Month 2-12 are strongly positive.
    profitable_assumptions = FinancialAssumptions(
        starting_cash=30000.0,
        one_time_startup_costs=10000.0,
        monthly_fixed_expenses=2000.0,
        marketing_expenditure=500.0,
        salaries_costs=2000.0,
        selling_price=100.0,
        variable_cost_per_unit=10.0,
        expected_sales_volume=100,  # $10,000 monthly revenue
        monthly_growth_rate_pct=0.0,
        forecast_months=12,
    )
    monthly, summary = calculate_monthly_projections(profitable_assumptions)
    # Cash at end of month 1 = 30000 - 5700 (startup - profit) > 20000
    # Cash never depletes; final month is cash flow positive
    assert monthly[0].net_cash_flow < 0  # month 1 was negative because of one-time startup
    assert monthly[1].net_cash_flow > 0  # month 2 is positive
    assert summary.ending_cash_balance > profitable_assumptions.starting_cash
    # Runway must NOT be finite (was ~4 months under buggy formula)
    assert summary.estimated_runway_months is None

    # Scenario B: Consistent monthly burn depleting cash over time
    # Starting cash = 10000. Month 1 startup = 2000.
    # Revenue = 0. Fixed expenses = 1000/month.
    # Month 1 cash outflow = 3000 (2000 startup + 1000 fixed). Closing cash = 7000.
    # Month 2-8 burn = 1000/month. Month 8 closing cash = 0.
    burning_assumptions = FinancialAssumptions(
        starting_cash=10000.0,
        one_time_startup_costs=2000.0,
        monthly_fixed_expenses=1000.0,
        salaries_costs=0.0,
        marketing_expenditure=0.0,
        selling_price=100.0,
        variable_cost_per_unit=10.0,
        expected_sales_volume=0,  # 0 revenue -> pure burn
        monthly_growth_rate_pct=0.0,
        forecast_months=12,
    )
    monthly_burn, summary_burn = calculate_monthly_projections(burning_assumptions)
    # Month 1 closing cash: 7000
    # Month 8 closing cash: 0
    # Under old buggy formula: 10000 / 3000 = 3.3 months!
    # Under correct over-time tracking: exactly 8.0 months
    assert summary_burn.estimated_runway_months == 8.0



