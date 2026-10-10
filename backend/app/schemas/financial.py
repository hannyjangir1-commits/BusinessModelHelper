"""Pydantic v2 schemas for Financial Projection Engine."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class FinancialAssumptions(BaseModel):
    """User-supplied financial parameters and operational assumptions."""

    currency: str = Field(default="USD", description="Currency symbol/code (e.g. USD, EUR, INR, GBP)")
    starting_cash: float = Field(default=10000.0, ge=0, description="Available starting capital")
    one_time_startup_costs: float = Field(default=3000.0, ge=0, description="One-off equipment, legal, setup expenses")

    # Recurring Monthly Expenses
    monthly_fixed_expenses: float = Field(default=1500.0, ge=0, description="Rent, software subscriptions, hosting, admin")
    marketing_expenditure: float = Field(default=800.0, ge=0, description="Monthly ad spend, SEO, content, customer acquisition")
    salaries_costs: float = Field(default=2500.0, ge=0, description="Monthly team payroll, founder stipend, contractors")

    # Unit Economics
    selling_price: float = Field(default=50.0, gt=0, description="Average revenue per sale / customer per month")
    variable_cost_per_unit: float = Field(default=12.0, ge=0, description="Direct cost of goods/services per sale")
    expected_sales_volume: int = Field(default=100, ge=0, description="Initial monthly units sold or paying customers")
    monthly_growth_rate_pct: float = Field(default=5.0, ge=-50.0, le=200.0, description="Expected month-over-month growth percentage")

    # Fees & Taxes
    payment_processing_pct: float = Field(default=2.9, ge=0, le=20.0, description="Credit card/payment gateway fee percentage")
    tax_rate_pct: float = Field(default=15.0, ge=0, le=50.0, description="Estimated effective corporate income tax rate percentage")

    # Timeline
    forecast_months: int = Field(default=12, ge=3, le=60, description="Number of projection months (default 12)")

    @field_validator("selling_price")
    @classmethod
    def validate_selling_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Selling price must be strictly greater than 0.")
        return round(v, 2)


class MonthlyProjection(BaseModel):
    """Calculated financial figures for a single forecast month."""

    month: int
    units_sold: int
    revenue: float
    direct_variable_costs: float
    payment_fees: float
    total_variable_costs: float
    gross_profit: float
    operating_expenses: float
    operating_profit: float
    tax_expense: float
    net_profit: float
    opening_cash: float
    cash_inflows: float
    cash_outflows: float
    net_cash_flow: float
    closing_cash: float


class BreakEvenMetrics(BaseModel):
    """Break-even analysis outputs."""

    contribution_margin_per_unit: float
    contribution_margin_ratio: float
    monthly_fixed_operating_costs: float
    break_even_units_per_month: Optional[int] = None
    break_even_revenue_per_month: Optional[float] = None
    is_break_even_achievable: bool = True
    advisory_note: str


class FinancialSummary(BaseModel):
    """High-level summary indicators across the forecast horizon."""

    total_revenue: float
    total_gross_profit: float
    total_operating_profit: float
    total_net_profit: float
    ending_cash_balance: float
    minimum_cash_balance: float
    recommended_startup_capital: float
    estimated_runway_months: Optional[float] = None
    is_profitable_by_end: bool
    break_even_month: Optional[int] = None


class ScenarioProjection(BaseModel):
    """Full projection set for a specific scenario (Conservative, Expected, Optimistic)."""

    scenario_name: str
    description: str
    multiplier_summary: Dict[str, str]
    summary: FinancialSummary
    break_even: BreakEvenMetrics
    monthly_projections: List[MonthlyProjection]


class FinancialModelResponse(BaseModel):
    """API response for a saved or calculated financial model."""

    id: Optional[str] = None
    project_id: str
    version: int = 1
    name: str = "Base Financial Plan"
    currency: str = "USD"
    forecast_months: int = 12
    assumptions: FinancialAssumptions
    summary: FinancialSummary
    break_even: BreakEvenMetrics
    monthly_projections: List[MonthlyProjection]
    scenarios: Optional[Dict[str, ScenarioProjection]] = None
    ai_advisory: Optional[str] = None


class FinancialRecalculateRequest(BaseModel):
    """Payload to test or preview calculations without persisting."""

    assumptions: FinancialAssumptions
    include_scenarios: bool = True


class FinancialSaveRequest(BaseModel):
    """Payload to save or update financial model."""

    name: str = "Base Financial Plan"
    assumptions: FinancialAssumptions
