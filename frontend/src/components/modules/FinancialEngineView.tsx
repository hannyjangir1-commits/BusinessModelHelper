import React, { useEffect, useState } from 'react';
import {
  ArrowDownRight,
  ArrowUpRight,
  Calculator,
  CheckCircle2,
  DollarSign,
  Layers,
  Percent,
  RefreshCw,
  Save,
  TrendingUp,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  FinancialAssumptions,
  FinancialModelResponse,
  MonthlyProjectionItem,
  SummaryMetrics,
} from '../../types';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import { Alert } from '../ui/Alert';

interface FinancialEngineViewProps {
  projectId: string;
  financialModel: FinancialModelResponse | null;
  onModelSaved: () => void;
}

export const FinancialEngineView: React.FC<FinancialEngineViewProps> = ({
  projectId,
  financialModel,
  onModelSaved,
}) => {
  const [assumptions, setAssumptions] = useState<FinancialAssumptions>({
    currency: 'USD',
    starting_cash: 5000,
    one_time_startup_costs: 1500,
    initial_equipment_costs: 800,
    monthly_fixed_costs: 350,
    variable_cost_per_unit: 12,
    selling_price: 49,
    initial_monthly_volume: 25,
    monthly_growth_rate: 0.12,
    payment_processing_pct: 0.029,
    monthly_marketing_budget: 200,
    monthly_salaries: 0,
    estimated_tax_rate: 0.15,
    forecast_months: 12,
  });

  const [summary, setSummary] = useState<SummaryMetrics | null>(null);
  const [projections, setProjections] = useState<MonthlyProjectionItem[]>([]);
  const [scenarios, setScenarios] = useState<Record<string, any>>({});
  const [activeScenario, setActiveScenario] = useState<'conservative' | 'expected' | 'optimistic'>('expected');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isRecalculating, setIsRecalculating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (financialModel) {
      const a = financialModel.assumptions as any;
      setAssumptions({
        currency: a.currency || 'USD',
        starting_cash: a.starting_cash ?? 5000,
        one_time_startup_costs: a.one_time_startup_costs ?? 1500,
        initial_equipment_costs: a.initial_equipment_costs ?? 0,
        monthly_fixed_costs: a.monthly_fixed_costs ?? a.monthly_fixed_expenses ?? 350,
        variable_cost_per_unit: a.variable_cost_per_unit ?? 12,
        selling_price: a.selling_price ?? 49,
        initial_monthly_volume: a.initial_monthly_volume ?? a.expected_sales_volume ?? 25,
        monthly_growth_rate: a.monthly_growth_rate ?? (a.monthly_growth_rate_pct ? a.monthly_growth_rate_pct / 100 : 0.12),
        payment_processing_pct: a.payment_processing_pct > 0.5 ? a.payment_processing_pct / 100 : (a.payment_processing_pct ?? 0.029),
        monthly_marketing_budget: a.monthly_marketing_budget ?? a.marketing_expenditure ?? 200,
        monthly_salaries: a.monthly_salaries ?? a.salaries_costs ?? 0,
        estimated_tax_rate: a.estimated_tax_rate ?? (a.tax_rate_pct ? a.tax_rate_pct / 100 : 0.15),
        forecast_months: a.forecast_months ?? 12,
      });
      setSummary((financialModel as any).summary_metrics || financialModel.summary);
      setProjections(financialModel.monthly_projections || []);
      setScenarios(financialModel.scenarios || {});
    } else {
      // Trigger initial calculation
      handleRecalculate();
    }
  }, [financialModel]);

  const handleInputChange = (field: keyof FinancialAssumptions, val: any) => {
    setAssumptions((prev) => ({
      ...prev,
      [field]: typeof prev[field] === 'number' ? parseFloat(val) || 0 : val,
    }));
  };

  const handleRecalculate = async () => {
    setIsRecalculating(true);
    setError(null);
    try {
      const res = await api.financial.calculate(projectId, assumptions);
      setSummary((res as any).summary_metrics || res.summary);
      setProjections(res.monthly_projections || []);
      setScenarios(res.scenarios || {});
    } catch (err: any) {
      setError(err?.message || 'Failed to recalculate financial projections.');
    } finally {
      setIsRecalculating(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.financial.save(projectId, assumptions);
      setSuccess('Financial projection model successfully saved and versioned.');
      onModelSaved();
    } catch (err: any) {
      setError(err?.message || 'Failed to save financial model.');
    } finally {
      setIsSaving(false);
    }
  };

  const curr = assumptions.currency;

  return (
    <div className="space-y-6">
      {/* Top Header & Save Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-bold text-slate-900">Deterministic Financial Engine</h2>
              {financialModel && <Badge variant="emerald">Version {financialModel.version}</Badge>}
            </div>
            <p className="text-xs text-slate-500">
              Pure Python mathematical calculations • Zero LLM arithmetic guesswork
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRecalculate}
            isLoading={isRecalculating}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Recalculate
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            isLoading={isSaving}
            leftIcon={<Save className="w-3.5 h-3.5" />}
          >
            Save Model
          </Button>
        </div>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {/* KPI Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-slate-50/50">
            <CardContent className="pt-4 pb-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Break-Even Units</span>
              <div className="text-2xl font-extrabold text-slate-900 mt-1">
                {summary.break_even_units ?? (financialModel?.break_even?.break_even_units_per_month ?? 'N/A')}{' '}
                <span className="text-xs font-normal text-slate-500">units/mo</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Revenue: {curr}{' '}
                {(() => {
                  const val = summary.break_even_revenue ?? financialModel?.break_even?.break_even_revenue_per_month;
                  return typeof val === 'number' ? val.toLocaleString() : (val ?? 'N/A');
                })()}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-50/50">
            <CardContent className="pt-4 pb-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Contribution Margin</span>
              <div className="text-2xl font-extrabold text-emerald-600 mt-1">
                {(((summary.contribution_margin_ratio ?? financialModel?.break_even?.contribution_margin_ratio) || 0) * 100).toFixed(1)}%
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Margin: {curr} {((summary.contribution_margin_per_unit ?? financialModel?.break_even?.contribution_margin_per_unit) || 0).toFixed(2)} / unit
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-50/50">
            <CardContent className="pt-4 pb-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Startup Capital Req</span>
              <div className="text-2xl font-extrabold text-slate-900 mt-1">
                {curr} {((summary.initial_capital_required ?? (summary as any)?.recommended_startup_capital) || 0).toLocaleString()}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Capex + Initial 2-Month Opex
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-50/50">
            <CardContent className="pt-4 pb-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Cash Runway</span>
              <div className="text-2xl font-extrabold text-indigo-600 mt-1">
                {((summary.runway_months ?? (summary as any)?.estimated_runway_months) || 0).toFixed(1)}{' '}
                <span className="text-xs font-normal text-slate-500">months</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Based on starting cash & initial burn
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Assumptions Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center justify-between">
            <span className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-emerald-600" /> Model Assumptions & Unit Economics
            </span>
            <span className="text-xs text-slate-500 font-normal">Adjust values to test sensitivities</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Currency</label>
              <input
                type="text"
                value={assumptions.currency}
                onChange={(e) => handleInputChange('currency', e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Starting Cash ({curr})</label>
              <input
                type="number"
                value={assumptions.starting_cash}
                onChange={(e) => handleInputChange('starting_cash', e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Selling Price ({curr}/unit)</label>
              <input
                type="number"
                value={assumptions.selling_price}
                onChange={(e) => handleInputChange('selling_price', e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Variable Cost ({curr}/unit)</label>
              <input
                type="number"
                value={assumptions.variable_cost_per_unit}
                onChange={(e) => handleInputChange('variable_cost_per_unit', e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Initial Monthly Volume</label>
              <input
                type="number"
                value={assumptions.initial_monthly_volume}
                onChange={(e) => handleInputChange('initial_monthly_volume', e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Monthly Growth Rate (e.g. 0.10)</label>
              <input
                type="number"
                step="0.01"
                value={assumptions.monthly_growth_rate}
                onChange={(e) => handleInputChange('monthly_growth_rate', e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Monthly Fixed Costs ({curr})</label>
              <input
                type="number"
                value={assumptions.monthly_fixed_costs}
                onChange={(e) => handleInputChange('monthly_fixed_costs', e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Monthly Marketing ({curr})</label>
              <input
                type="number"
                value={assumptions.monthly_marketing_budget}
                onChange={(e) => handleInputChange('monthly_marketing_budget', e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scenario Sensitivity Switcher */}
      {scenarios && Object.keys(scenarios).length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-indigo-600" /> Scenario Sensitivity Comparison
              </CardTitle>
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
                {(['conservative', 'expected', 'optimistic'] as const).map((sc) => (
                  <button
                    key={sc}
                    onClick={() => setActiveScenario(sc)}
                    className={`px-3 py-1 rounded text-xs font-semibold capitalize transition-all ${
                      activeScenario === sc
                        ? 'bg-white text-indigo-700 shadow-sm'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {sc}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              {Object.entries(scenarios).map(([name, sc]: [string, any]) => {
                const isSelected = activeScenario === name;
                const growthRate = sc.assumptions?.monthly_growth_rate_pct != null
                  ? sc.assumptions.monthly_growth_rate_pct
                  : (sc.assumptions?.monthly_growth_rate != null
                    ? (sc.assumptions.monthly_growth_rate <= 1 ? sc.assumptions.monthly_growth_rate * 100 : sc.assumptions.monthly_growth_rate)
                    : 0);
                const annualRevenue = sc.summary?.total_revenue ?? sc.summary_metrics?.total_revenue_forecast ?? 0;
                const annualNetProfit = sc.summary?.net_profit ?? sc.summary_metrics?.total_net_profit_forecast ?? 0;
                const breakEven = sc.break_even?.break_even_units_per_month ?? sc.summary_metrics?.break_even_units ?? '—';
                return (
                  <div
                    key={name}
                    className={`border rounded-xl p-4 space-y-2 transition-all ${
                      isSelected ? 'border-indigo-500 bg-indigo-50/20 shadow-sm ring-1 ring-indigo-500' : 'border-slate-200 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold uppercase tracking-wider text-slate-800">{name}</span>
                      <Badge variant={isSelected ? 'indigo' : 'slate'} size="sm">
                        Growth: {Number(growthRate).toFixed(0)}%
                      </Badge>
                    </div>
                    <div className="space-y-1 pt-2 border-t border-slate-100">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Annual Revenue:</span>
                        <span className="font-bold text-slate-900">
                          {curr} {annualRevenue.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Annual Net Profit:</span>
                        <span className={`font-bold ${annualNetProfit >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {curr} {annualNetProfit.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Break-Even Units:</span>
                        <span className="font-medium text-slate-800">{breakEven}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 12-Month Projections Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center justify-between">
            <span>12-Month Cash Flow & Profit Statement</span>
            <span className="text-xs text-slate-500 font-normal">All numbers computed in Python</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 uppercase font-bold text-[10px] bg-slate-50">
                  <th className="py-2.5 px-3 text-left">Month</th>
                  <th className="py-2.5 px-3">Units Sold</th>
                  <th className="py-2.5 px-3">Revenue</th>
                  <th className="py-2.5 px-3">COGS</th>
                  <th className="py-2.5 px-3">Gross Profit</th>
                  <th className="py-2.5 px-3">Operating Exp</th>
                  <th className="py-2.5 px-3">Net Profit</th>
                  <th className="py-2.5 px-3">Closing Cash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {projections.map((p) => (
                  <tr key={p.month} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 font-semibold text-slate-800 text-left">Month {p.month}</td>
                    <td className="py-2.5 px-3 text-slate-600">{p.units_sold.toLocaleString()}</td>
                    <td className="py-2.5 px-3 font-medium text-slate-900">{curr} {p.revenue.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-slate-500">{curr} {(p.cogs ?? p.total_variable_costs ?? 0).toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-emerald-700 font-medium">{curr} {p.gross_profit.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-slate-500">{curr} {p.operating_expenses.toLocaleString()}</td>
                    <td className={`py-2.5 px-3 font-bold ${p.net_profit >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {curr} {p.net_profit.toLocaleString()}
                    </td>
                    <td className={`py-2.5 px-3 font-medium ${p.closing_cash >= 0 ? 'text-slate-900' : 'text-rose-600 font-bold'}`}>
                      {curr} {p.closing_cash.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
