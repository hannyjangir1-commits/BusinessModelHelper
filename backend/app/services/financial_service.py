"""Deterministic Python calculation engine and persistence for Financial Projections."""

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.financial_model import FinancialModel
from app.models.project import Project
from app.models.user import User
from app.schemas.financial import (
    BreakEvenMetrics,
    FinancialAssumptions,
    FinancialModelResponse,
    FinancialSaveRequest,
    FinancialSummary,
    MonthlyProjection,
    ScenarioProjection,
)
from app.services.ai.client import GeminiAIClient, MockAIClient
from app.services.project_service import get_user_project_by_id, prune_financial_model_versions


def calculate_break_even(assumptions: FinancialAssumptions) -> BreakEvenMetrics:
    """Calculate deterministic break-even metrics and unit economics."""
    fixed_operating = round(
        assumptions.monthly_fixed_expenses
        + assumptions.marketing_expenditure
        + assumptions.salaries_costs,
        2,
    )
    payment_fee_per_unit = round(
        assumptions.selling_price * (assumptions.payment_processing_pct / 100.0), 2
    )
    contribution_margin_per_unit = round(
        assumptions.selling_price - assumptions.variable_cost_per_unit - payment_fee_per_unit, 2
    )

    if assumptions.selling_price > 0:
        contribution_margin_ratio = round(
            contribution_margin_per_unit / assumptions.selling_price, 4
        )
    else:
        contribution_margin_ratio = 0.0

    if contribution_margin_per_unit > 0:
        break_even_units = math.ceil(fixed_operating / contribution_margin_per_unit)
        break_even_revenue = round(break_even_units * assumptions.selling_price, 2)
        is_achievable = True
        advisory = (
            f"Break-even requires selling {break_even_units:,} units per month "
            f"({assumptions.currency} {break_even_revenue:,.2f}/month revenue) to cover fixed operating burn."
        )
    else:
        break_even_units = None
        break_even_revenue = None
        is_achievable = False
        advisory = (
            f"Direct variable costs ({assumptions.currency} {assumptions.variable_cost_per_unit:.2f}) "
            f"plus payment fees ({assumptions.currency} {payment_fee_per_unit:.2f}) "
            f"equal or exceed the selling price ({assumptions.currency} {assumptions.selling_price:.2f}). "
            f"Unit contribution margin is negative. Increase selling price or renegotiate COGS."
        )

    return BreakEvenMetrics(
        contribution_margin_per_unit=contribution_margin_per_unit,
        contribution_margin_ratio=contribution_margin_ratio,
        monthly_fixed_operating_costs=fixed_operating,
        break_even_units_per_month=break_even_units,
        break_even_revenue_per_month=break_even_revenue,
        is_break_even_achievable=is_achievable,
        advisory_note=advisory,
    )


def calculate_monthly_projections(
    assumptions: FinancialAssumptions,
) -> Tuple[List[MonthlyProjection], FinancialSummary]:
    """Generate monthly figures using strict deterministic formulas."""
    monthly_rows: List[MonthlyProjection] = []
    current_cash = round(assumptions.starting_cash, 2)
    min_cash = current_cash
    break_even_month: Optional[int] = None

    tot_rev = 0.0
    tot_gross = 0.0
    tot_op_profit = 0.0
    tot_net_profit = 0.0

    fixed_operating = round(
        assumptions.monthly_fixed_expenses
        + assumptions.marketing_expenditure
        + assumptions.salaries_costs,
        2,
    )

    for m in range(1, assumptions.forecast_months + 1):
        # Month-over-month compounded unit growth
        growth_factor = (1.0 + (assumptions.monthly_growth_rate_pct / 100.0)) ** (m - 1)
        units_sold = max(0, int(round(assumptions.expected_sales_volume * growth_factor)))

        revenue = round(units_sold * assumptions.selling_price, 2)
        direct_var = round(units_sold * assumptions.variable_cost_per_unit, 2)
        payment_fees = round(revenue * (assumptions.payment_processing_pct / 100.0), 2)
        total_var = round(direct_var + payment_fees, 2)

        gross_profit = round(revenue - total_var, 2)
        operating_profit = round(gross_profit - fixed_operating, 2)

        # Tax is only levied on positive operating profits
        if operating_profit > 0 and assumptions.tax_rate_pct > 0:
            tax_expense = round(operating_profit * (assumptions.tax_rate_pct / 100.0), 2)
        else:
            tax_expense = 0.0

        net_profit = round(operating_profit - tax_expense, 2)

        if break_even_month is None and net_profit > 0:
            break_even_month = m

        opening_cash = current_cash
        cash_inflows = revenue

        # In month 1, include initial startup costs as an outflow
        if m == 1:
            cash_outflows = round(total_var + fixed_operating + tax_expense + assumptions.one_time_startup_costs, 2)
        else:
            cash_outflows = round(total_var + fixed_operating + tax_expense, 2)

        net_cash_flow = round(cash_inflows - cash_outflows, 2)
        closing_cash = round(opening_cash + net_cash_flow, 2)
        current_cash = closing_cash

        if closing_cash < min_cash:
            min_cash = closing_cash

        tot_rev += revenue
        tot_gross += gross_profit
        tot_op_profit += operating_profit
        tot_net_profit += net_profit

        monthly_rows.append(
            MonthlyProjection(
                month=m,
                units_sold=units_sold,
                revenue=revenue,
                direct_variable_costs=direct_var,
                payment_fees=payment_fees,
                total_variable_costs=total_var,
                cogs=direct_var,
                gross_profit=gross_profit,
                operating_expenses=fixed_operating,
                operating_profit=operating_profit,
                tax_expense=tax_expense,
                net_profit=net_profit,
                opening_cash=opening_cash,
                cash_inflows=cash_inflows,
                cash_outflows=cash_outflows,
                net_cash_flow=net_cash_flow,
                closing_cash=closing_cash,
            )
        )

    # Runway calculation accounting for projected cash balances over time.
    # Must NOT treat one-time first-month startup expenses as recurring monthly burn.
    estimated_runway = None
    for row in monthly_rows:
        if row.closing_cash <= 0:
            if row.opening_cash <= 0:
                estimated_runway = float(max(0, row.month - 1))
            else:
                monthly_burn = abs(row.net_cash_flow)
                if monthly_burn > 0:
                    fraction = row.opening_cash / monthly_burn
                    estimated_runway = round((row.month - 1) + fraction, 1)
                else:
                    estimated_runway = float(row.month - 1)
            break

    # If cash is never depleted during the forecast horizon:
    # If the business is still burning cash in the final forecast month, extrapolate based on ending recurring burn.
    # If the business is cash-flow positive or break-even, runway is None (self-sustaining).
    if estimated_runway is None and len(monthly_rows) > 0:
        last_row = monthly_rows[-1]
        if last_row.net_cash_flow < 0 and last_row.closing_cash > 0:
            ending_burn = abs(last_row.net_cash_flow)
            extra_months = last_row.closing_cash / ending_burn
            estimated_runway = round(len(monthly_rows) + extra_months, 1)

    # Capital requirement calculation
    if min_cash < 0:
        cash_deficit = abs(min_cash)
        recommended_capital = round(assumptions.one_time_startup_costs + cash_deficit + (fixed_operating * 2.0), 2)
    else:
        recommended_capital = round(assumptions.one_time_startup_costs + (fixed_operating * 2.5), 2)

    summary = FinancialSummary(
        total_revenue=round(tot_rev, 2),
        total_gross_profit=round(tot_gross, 2),
        total_operating_profit=round(tot_op_profit, 2),
        total_net_profit=round(tot_net_profit, 2),
        ending_cash_balance=round(current_cash, 2),
        minimum_cash_balance=round(min_cash, 2),
        recommended_startup_capital=recommended_capital,
        estimated_runway_months=estimated_runway,
        is_profitable_by_end=monthly_rows[-1].net_profit > 0,
        break_even_month=break_even_month,
    )

    return monthly_rows, summary


def generate_scenarios(
    baseline: FinancialAssumptions,
) -> Dict[str, ScenarioProjection]:
    """Generate 3 distinct explicit scenarios: Conservative, Expected, Optimistic."""
    # 1. Expected (Baseline)
    exp_rows, exp_sum = calculate_monthly_projections(baseline)
    exp_be = calculate_break_even(baseline)
    expected_scenario = ScenarioProjection(
        scenario_name="Expected (Base Plan)",
        description="Core planning baseline based on current realistic market expectations.",
        multiplier_summary={
            "Sales Volume": f"{baseline.expected_sales_volume:,} units/mo",
            "Growth Rate": f"{baseline.monthly_growth_rate_pct}% / month",
            "Selling Price": f"{baseline.currency} {baseline.selling_price:.2f}",
            "Marketing Spend": f"{baseline.currency} {baseline.marketing_expenditure:.2f}/mo",
        },
        summary=exp_sum,
        break_even=exp_be,
        monthly_projections=exp_rows,
    )

    # 2. Conservative (25% lower sales, 50% slower growth, 20% higher marketing CAC, 15% higher COGS)
    cons_assumptions = baseline.model_copy()
    cons_assumptions.expected_sales_volume = max(1, int(round(baseline.expected_sales_volume * 0.75)))
    cons_assumptions.monthly_growth_rate_pct = round(baseline.monthly_growth_rate_pct * 0.5, 2)
    cons_assumptions.marketing_expenditure = round(baseline.marketing_expenditure * 1.20, 2)
    cons_assumptions.variable_cost_per_unit = round(baseline.variable_cost_per_unit * 1.15, 2)

    cons_rows, cons_sum = calculate_monthly_projections(cons_assumptions)
    cons_be = calculate_break_even(cons_assumptions)
    conservative_scenario = ScenarioProjection(
        scenario_name="Conservative (Downside Buffer)",
        description="Stressed scenario with slower customer acquisition, lower initial volume, and higher acquisition costs.",
        multiplier_summary={
            "Sales Volume": f"-25% ({cons_assumptions.expected_sales_volume:,} units/mo)",
            "Growth Rate": f"-50% ({cons_assumptions.monthly_growth_rate_pct}% / mo)",
            "Variable COGS": f"+15% ({baseline.currency} {cons_assumptions.variable_cost_per_unit:.2f})",
            "Marketing Spend": f"+20% ({baseline.currency} {cons_assumptions.marketing_expenditure:.2f}/mo)",
        },
        summary=cons_sum,
        break_even=cons_be,
        monthly_projections=cons_rows,
    )

    # 3. Optimistic (35% higher sales, 40% faster growth, 10% premium pricing, improved CAC efficiency)
    opt_assumptions = baseline.model_copy()
    opt_assumptions.expected_sales_volume = max(1, int(round(baseline.expected_sales_volume * 1.35)))
    opt_assumptions.monthly_growth_rate_pct = round(baseline.monthly_growth_rate_pct * 1.40, 2)
    opt_assumptions.selling_price = round(baseline.selling_price * 1.10, 2)
    opt_assumptions.marketing_expenditure = round(baseline.marketing_expenditure * 0.90, 2)

    opt_rows, opt_sum = calculate_monthly_projections(opt_assumptions)
    opt_be = calculate_break_even(opt_assumptions)
    optimistic_scenario = ScenarioProjection(
        scenario_name="Optimistic (Accelerated Growth)",
        description="Upside scenario with viral word-of-mouth, premium pricing tolerance, and efficient marketing.",
        multiplier_summary={
            "Sales Volume": f"+35% ({opt_assumptions.expected_sales_volume:,} units/mo)",
            "Growth Rate": f"+40% ({opt_assumptions.monthly_growth_rate_pct}% / mo)",
            "Selling Price": f"+10% ({baseline.currency} {opt_assumptions.selling_price:.2f})",
            "Marketing CAC": f"-10% ({baseline.currency} {opt_assumptions.marketing_expenditure:.2f}/mo)",
        },
        summary=opt_sum,
        break_even=opt_be,
        monthly_projections=opt_rows,
    )

    return {
        "conservative": conservative_scenario,
        "expected": expected_scenario,
        "optimistic": optimistic_scenario,
    }


def compute_full_financial_model(
    assumptions: FinancialAssumptions,
    project_id: str,
    name: str = "Base Financial Plan",
    version: int = 1,
    model_id: Optional[str] = None,
) -> FinancialModelResponse:
    """Calculate full financial model with projections, break-even, and scenarios."""
    monthly_projections, summary = calculate_monthly_projections(assumptions)
    break_even = calculate_break_even(assumptions)
    scenarios = generate_scenarios(assumptions)

    return FinancialModelResponse(
        id=model_id,
        project_id=project_id,
        version=version,
        name=name,
        currency=assumptions.currency,
        forecast_months=assumptions.forecast_months,
        assumptions=assumptions,
        summary=summary,
        break_even=break_even,
        monthly_projections=monthly_projections,
        scenarios=scenarios,
    )


def save_or_update_financial_model(
    db: Session,
    user: User,
    project_id: str,
    save_request: FinancialSaveRequest,
) -> FinancialModelResponse:
    """Persist financial assumptions and deterministic projections to PostgreSQL."""
    project = get_user_project_by_id(db, user, project_id)

    # Determine next version
    latest_ver = db.execute(
        select(func.coalesce(func.max(FinancialModel.version), 0)).where(
            FinancialModel.project_id == project.id
        )
    ).scalar_one()
    new_version = latest_ver + 1

    computed = compute_full_financial_model(
        assumptions=save_request.assumptions,
        project_id=project.id,
        name=save_request.name,
        version=new_version,
    )

    db_model = FinancialModel(
        project_id=project.id,
        user_id=user.id,
        name=save_request.name,
        version=new_version,
        currency=save_request.assumptions.currency,
        forecast_months=save_request.assumptions.forecast_months,
        assumptions_json=save_request.assumptions.model_dump(),
        projections_json={
            "summary": computed.summary.model_dump(),
            "break_even": computed.break_even.model_dump(),
            "monthly_projections": [m.model_dump() for m in computed.monthly_projections],
        },
        scenarios_json={k: v.model_dump() for k, v in computed.scenarios.items()} if computed.scenarios else None,
    )
    db.add(db_model)
    db.flush()
    prune_financial_model_versions(db, project.id)
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_model)

    computed.id = db_model.id
    return computed


def get_financial_model(
    db: Session,
    user: User,
    project_id: str,
    version: Optional[int] = None,
) -> FinancialModelResponse:
    """Retrieve saved financial model for project."""
    project = get_user_project_by_id(db, user, project_id)

    query = select(FinancialModel).where(FinancialModel.project_id == project.id)
    if version is not None:
        query = query.where(FinancialModel.version == version)
    else:
        query = query.order_by(desc(FinancialModel.version))

    db_model = db.execute(query).scalars().first()
    if not db_model:
        raise NotFoundError("No financial model found for this project.")

    assumptions = FinancialAssumptions.model_validate(db_model.assumptions_json)
    computed = compute_full_financial_model(
        assumptions=assumptions,
        project_id=project.id,
        name=db_model.name,
        version=db_model.version,
        model_id=db_model.id,
    )
    return computed


def list_financial_model_versions(
    db: Session,
    user: User,
    project_id: str,
) -> List[Dict[str, Any]]:
    """List all saved financial model versions for the project."""
    project = get_user_project_by_id(db, user, project_id)

    models = db.execute(
        select(FinancialModel)
        .where(FinancialModel.project_id == project.id)
        .order_by(desc(FinancialModel.version))
    ).scalars().all()

    return [
        {
            "id": m.id,
            "version": m.version,
            "name": m.name,
            "currency": m.currency,
            "forecast_months": m.forecast_months,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }
        for m in models
    ]


def delete_financial_model(
    db: Session,
    user: User,
    project_id: str,
    model_id: str,
) -> None:
    """Delete a specific financial model by ID."""
    project = get_user_project_by_id(db, user, project_id)

    db_model = db.execute(
        select(FinancialModel).where(
            FinancialModel.id == model_id,
            FinancialModel.project_id == project.id,
        )
    ).scalars().first()

    if not db_model:
        raise NotFoundError("Financial model not found.")

    db.delete(db_model)
    db.commit()


def generate_financial_ai_advisory(
    project: Project,
    model: FinancialModelResponse,
    client: Optional[Any] = None,
) -> str:
    """Generate executive AI advisory commentary grounded in the deterministic Python calculations."""
    ai_client = client or GeminiAIClient()

    system_instruction = (
        "You are an expert Chief Financial Officer (CFO) and startup financial advisor. "
        "Analyze the provided deterministic financial projections. "
        "Provide a concise, practical, 3-paragraph executive briefing highlighting: "
        "1) Cash runway, working capital vulnerabilities, and burn rate sustainability. "
        "2) Unit economics, margin strengths, and pricing sensitivity. "
        "3) Key risks and 3 specific financial experiments to validate prior to launch. "
        "DO NOT re-calculate or alter any numbers. Quote the provided numbers accurately. "
        "Include a clear disclaimer that this is planning advice, not certified accounting or tax opinion."
    )

    user_prompt = f"""
Business Name: {project.name}
Industry: {project.industry}
Currency: {model.currency}
Selling Price: {model.assumptions.selling_price}
Variable Cost / Unit: {model.assumptions.variable_cost_per_unit}
Monthly Fixed Expenses: {model.assumptions.monthly_fixed_expenses}
Marketing Spend: {model.assumptions.marketing_expenditure}
Salaries: {model.assumptions.salaries_costs}
Starting Cash: {model.assumptions.starting_cash}

Calculated Metrics (Computed deterministically by Python):
- Total 12-Month Revenue: {model.summary.total_revenue}
- Total Net Profit: {model.summary.total_net_profit}
- Ending Cash Balance: {model.summary.ending_cash_balance}
- Minimum Cash Balance: {model.summary.minimum_cash_balance}
- Recommended Initial Capital: {model.summary.recommended_startup_capital}
- Estimated Runway: {model.summary.estimated_runway_months or 'Profitable / Self-sustaining'}
- Contribution Margin / Unit: {model.break_even.contribution_margin_per_unit}
- Break-Even Units / Month: {model.break_even.break_even_units_per_month or 'Unachievable at current unit costs'}
- Break-Even Month: {model.summary.break_even_month or 'Not achieved within horizon'}

Please provide your CFO analysis and recommended strategic financial actions.
"""

    try:
        raw_text, _, _, _ = ai_client.generate(system_instruction, user_prompt)
        return raw_text.strip()
    except Exception as e:
        return (
            f"Advisory generation unavailable ({str(e)}). "
            f"Note: Break-even is {model.break_even.advisory_note}"
        )
