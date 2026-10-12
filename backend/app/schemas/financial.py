"""Pydantic v2 schemas for Financial Projection Engine."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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

    @model_validator(mode="before")
    @classmethod
    def normalize_assumptions(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        d = dict(data)

        # 1. Field name aliases
        if "monthly_fixed_costs" in d and "monthly_fixed_expenses" not in d:
            d["monthly_fixed_expenses"] = d["monthly_fixed_costs"]
        if "monthly_marketing_budget" in d and "marketing_expenditure" not in d:
            d["marketing_expenditure"] = d["monthly_marketing_budget"]
        if "monthly_salaries" in d and "salaries_costs" not in d:
            d["salaries_costs"] = d["monthly_salaries"]
        if "initial_monthly_volume" in d and "expected_sales_volume" not in d:
            d["expected_sales_volume"] = d["initial_monthly_volume"]

        # If equipment was supplied as an additional field alongside startup capex
        if "initial_equipment_costs" in d and "one_time_startup_costs" not in d:
            d["one_time_startup_costs"] = float(d["initial_equipment_costs"] or 0)

        # 2. Fractional percentage conversions (e.g. 0.12 -> 12.0%, 0.029 -> 2.9%, 0.15 -> 15.0%)
        if "monthly_growth_rate" in d and "monthly_growth_rate_pct" not in d:
            val = float(d["monthly_growth_rate"] or 0)
            if -1.0 <= val <= 2.0 and val != 0:
                d["monthly_growth_rate_pct"] = round(val * 100.0, 2)
            else:
                d["monthly_growth_rate_pct"] = val
        elif "monthly_growth_rate_pct" in d:
            val = float(d["monthly_growth_rate_pct"] or 0)
            if 0 < abs(val) <= 1.0:
                d["monthly_growth_rate_pct"] = round(val * 100.0, 2)

        # Payment processing fee
        if "payment_processing_rate" in d and "payment_processing_pct" not in d:
            val = float(d["payment_processing_rate"] or 0)
            if 0 < val <= 0.20:
                d["payment_processing_pct"] = round(val * 100.0, 2)
            else:
                d["payment_processing_pct"] = val
        elif "payment_processing_pct" in d:
            val = float(d["payment_processing_pct"] or 0)
            if 0 < val <= 0.20:
                d["payment_processing_pct"] = round(val * 100.0, 2)

        # Tax rate
        if ("tax_rate" in d or "estimated_tax_rate" in d) and "tax_rate_pct" not in d:
            raw_tax = d.get("tax_rate", d.get("estimated_tax_rate"))
            val = float(raw_tax or 0)
            if 0 < val <= 1.0:
                d["tax_rate_pct"] = round(val * 100.0, 2)
            else:
                d["tax_rate_pct"] = val
        elif "tax_rate_pct" in d:
            val = float(d["tax_rate_pct"] or 0)
            if 0 < val <= 1.0:
                d["tax_rate_pct"] = round(val * 100.0, 2)

        return d


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

    # Frontend convenience alias
    cogs: Optional[float] = None

    @model_validator(mode="after")
    def populate_cogs(self) -> "MonthlyProjection":
        if self.cogs is None:
            self.cogs = self.direct_variable_costs
        return self


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

    # Frontend compatibility aliases
    initial_capital_required: Optional[float] = None
    runway_months: Optional[float] = None
    total_revenue_forecast: Optional[float] = None
    total_gross_profit_forecast: Optional[float] = None
    total_operating_expenses_forecast: Optional[float] = None
    total_net_profit_forecast: Optional[float] = None
    break_even_units: Optional[Any] = None
    break_even_revenue: Optional[Any] = None
    contribution_margin_per_unit: Optional[float] = None
    contribution_margin_ratio: Optional[float] = None

    @model_validator(mode="after")
    def populate_summary_aliases(self) -> "FinancialSummary":
        if self.initial_capital_required is None:
            self.initial_capital_required = self.recommended_startup_capital
        if self.runway_months is None:
            self.runway_months = self.estimated_runway_months
        if self.total_revenue_forecast is None:
            self.total_revenue_forecast = self.total_revenue
        if self.total_gross_profit_forecast is None:
            self.total_gross_profit_forecast = self.total_gross_profit
        if self.total_net_profit_forecast is None:
            self.total_net_profit_forecast = self.total_net_profit
        return self


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

    # Frontend convenience alias
    summary_metrics: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def populate_response_aliases(self) -> "FinancialModelResponse":
        if self.summary:
            if self.break_even:
                self.summary.break_even_units = self.break_even.break_even_units_per_month or "N/A"
                self.summary.break_even_revenue = self.break_even.break_even_revenue_per_month or "N/A"
                self.summary.contribution_margin_per_unit = self.break_even.contribution_margin_per_unit
                self.summary.contribution_margin_ratio = self.break_even.contribution_margin_ratio
            if self.summary_metrics is None:
                self.summary_metrics = self.summary.model_dump()
        return self


class FinancialRecalculateRequest(BaseModel):
    """Payload to test or preview calculations without persisting."""

    assumptions: FinancialAssumptions
    include_scenarios: bool = True

    @model_validator(mode="before")
    @classmethod
    def normalize_calc_request(cls, data: Any) -> Any:
        if isinstance(data, dict) and "assumptions" not in data:
            return {"assumptions": data, "include_scenarios": True}
        return data


class FinancialSaveRequest(BaseModel):
    """Payload to save or update financial model."""

    name: str = "Base Financial Plan"
    assumptions: FinancialAssumptions

    @model_validator(mode="before")
    @classmethod
    def normalize_save_request(cls, data: Any) -> Any:
        if isinstance(data, dict) and "assumptions" not in data:
            name = data.get("name", "Base Financial Plan")
            return {"name": name, "assumptions": data}
        return data
