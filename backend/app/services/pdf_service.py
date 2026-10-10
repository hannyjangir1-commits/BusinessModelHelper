"""Professional PDF generation service using ReportLab."""

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.blueprint import Blueprint
from app.models.project import Project


class NumberedCanvas:
    """Canvas that performs two passes to render accurate total page count on footer."""
    # Using ReportLab standard flow with SimpleDocTemplate onFirstPage and onLaterPages callback
    pass


def _header_footer(canvas, doc):
    """Draw clean header line and page numbers."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))

    # Top header (pages > 1)
    if doc.page > 1:
        canvas.drawString(54, letter[1] - 36, "AI Business Architect — Business Blueprint")
        canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
        canvas.setLineWidth(0.5)
        canvas.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

    # Bottom footer
    page_text = f"Page {doc.page}"
    canvas.drawRightString(letter[0] - 54, 36, page_text)
    canvas.drawString(54, 36, "Confidential — Generated with AI Business Architect")
    canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
    canvas.setLineWidth(0.5)
    canvas.line(54, 48, letter[0] - 54, 48)

    canvas.restoreState()


def generate_project_blueprint_pdf(
    project: Project,
    bmc_blueprint: Optional[Blueprint] = None,
    tech_blueprint: Optional[Blueprint] = None,
    validator_report: Optional[Any] = None,
    financial_model: Optional[Any] = None,
    research_report: Optional[Any] = None,
    roadmap_tasks: Optional[List[Any]] = None,
) -> bytes:
    """Generate a publication-grade PDF report from project details and saved blueprints."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    brand_color = colors.HexColor("#312e81")  # Indigo 900
    accent_color = colors.HexColor("#4f46e5")  # Indigo 600
    text_color = colors.HexColor("#0f172a")  # Slate 900
    subtext_color = colors.HexColor("#475569")  # Slate 600

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=brand_color,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=subtext_color,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=brand_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
    )

    meta_label = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
    )

    meta_val = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748b"),
    )

    elements = []

    # Header / Brand
    elements.append(Paragraph("AI BUSINESS ARCHITECT", subtitle_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"Executive Blueprint: {project.name}", title_style))
    elements.append(Spacer(1, 4))
    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")
    elements.append(Paragraph(f"Generated on {now_str}", subtitle_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceAfter=14))

    # Project Overview Table
    elements.append(Paragraph("1. Executive Summary & Context", h1_style))
    meta_data = [
        [Paragraph("Industry / Domain", meta_label), Paragraph(project.industry, meta_val),
         Paragraph("Business Stage", meta_label), Paragraph(project.business_stage.capitalize(), meta_val)],
        [Paragraph("Target Market", meta_label), Paragraph(project.target_market or "General", meta_val),
         Paragraph("Target Audience", meta_label), Paragraph(project.target_audience or "Broad", meta_val)],
        [Paragraph("Estimated Budget", meta_label),
         Paragraph(f"{project.budget_amount:,.2f} {project.budget_currency}" if project.budget_amount else "Bootstrapped", meta_val),
         Paragraph("Team Size", meta_label), Paragraph(project.team_size or "Solo Founder", meta_val)],
    ]
    t_meta = Table(meta_data, colWidths=[110, 140, 110, 144])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Business Idea Description", h2_style))
    elements.append(Paragraph(project.idea_description, body_style))
    elements.append(Spacer(1, 14))

    # Business Model Canvas Section
    if bmc_blueprint and bmc_blueprint.content_json:
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=12))
        elements.append(Paragraph(f"2. Business Model Canvas (Version {bmc_blueprint.version})", h1_style))
        bmc_data = bmc_blueprint.content_json

        if "overview" in bmc_data:
            elements.append(Paragraph(f"<b>Overview:</b> {bmc_data['overview']}", body_style))
            elements.append(Spacer(1, 4))
        if "key_strategic_focus" in bmc_data:
            elements.append(Paragraph(f"<b>Core Strategic Focus:</b> {bmc_data['key_strategic_focus']}", body_style))
            elements.append(Spacer(1, 10))

        blocks_order = [
            ("customer_segments", "Customer Segments"),
            ("value_propositions", "Value Propositions"),
            ("channels", "Channels"),
            ("customer_relationships", "Customer Relationships"),
            ("revenue_streams", "Revenue Streams"),
            ("key_resources", "Key Resources"),
            ("key_activities", "Key Activities"),
            ("key_partnerships", "Key Partnerships"),
            ("cost_structure", "Cost Structure"),
        ]

        for block_key, fallback_title in blocks_order:
            block = bmc_data.get(block_key, {})
            if isinstance(block, dict):
                title = block.get("block_title", fallback_title)
                summary = block.get("summary", "")
                recs = block.get("recommendations", [])
                rationale = block.get("rationale", "")
                assumptions = block.get("assumptions", [])
                experiments = block.get("validation_experiments", [])

                block_elements = [
                    Paragraph(title, h2_style),
                    Paragraph(f"<b>Summary:</b> {summary}", body_style),
                    Spacer(1, 3),
                ]

                if recs:
                    rec_text = "<br/>".join([f"• {r}" for r in recs])
                    block_elements.append(Paragraph(f"<b>Recommendations:</b><br/>{rec_text}", body_style))
                    block_elements.append(Spacer(1, 3))

                if rationale:
                    block_elements.append(Paragraph(f"<b>Rationale:</b> {rationale}", body_style))
                    block_elements.append(Spacer(1, 3))

                if assumptions:
                    assump_text = "<br/>".join([f"• {a}" for a in assumptions])
                    block_elements.append(Paragraph(f"<b>Key Assumptions:</b><br/>{assump_text}", body_style))
                    block_elements.append(Spacer(1, 3))

                if experiments:
                    exp_text = "<br/>".join([f"• {e}" for e in experiments])
                    block_elements.append(Paragraph(f"<b>Validation Experiments:</b><br/>{exp_text}", body_style))

                block_elements.append(Spacer(1, 8))
                elements.append(KeepTogether(block_elements))

    # Technology Stack Recommendation Section
    if tech_blueprint and tech_blueprint.content_json:
        elements.append(PageBreak())
        elements.append(Paragraph(f"3. Technology Stack Recommendation (Version {tech_blueprint.version})", h1_style))
        tech_data = tech_blueprint.content_json

        if "architecture_summary" in tech_data:
            elements.append(Paragraph(f"<b>Architecture Philosophy:</b> {tech_data['architecture_summary']}", body_style))
            elements.append(Spacer(1, 4))
        if "estimated_monthly_infrastructure_total" in tech_data:
            elements.append(Paragraph(f"<b>Estimated Launch Infrastructure Cost:</b> {tech_data['estimated_monthly_infrastructure_total']}", body_style))
            elements.append(Spacer(1, 10))

        cat_order = [
            ("frontend", "Frontend"),
            ("backend", "Backend"),
            ("database", "Database"),
            ("hosting_infrastructure", "Hosting & Infrastructure"),
            ("third_party_services", "Third-Party Services"),
        ]

        for cat_key, fallback_title in cat_order:
            cat = tech_data.get(cat_key, {})
            if isinstance(cat, dict):
                tech = cat.get("technology", "N/A")
                purpose = cat.get("purpose", "")
                reason = cat.get("reason", "")
                cost = cat.get("estimated_cost", "Estimate required")
                alts = cat.get("alternatives", [])
                tradeoffs = cat.get("tradeoffs", [])
                notes = cat.get("verification_notes", "")

                cat_elements = [
                    Paragraph(f"{fallback_title}: {tech}", h2_style),
                    Paragraph(f"<b>Role:</b> {purpose}", body_style),
                    Spacer(1, 2),
                    Paragraph(f"<b>Rationale:</b> {reason}", body_style),
                    Spacer(1, 2),
                    Paragraph(f"<b>Estimated Cost:</b> {cost}", body_style),
                    Spacer(1, 2),
                ]

                if alts:
                    cat_elements.append(Paragraph(f"<b>Alternatives Considered:</b> {', '.join(alts)}", body_style))
                    cat_elements.append(Spacer(1, 2))

                if tradeoffs:
                    t_text = "<br/>".join([f"• {t}" for t in tradeoffs])
                    cat_elements.append(Paragraph(f"<b>Trade-offs & Operational Considerations:</b><br/>{t_text}", body_style))
                    cat_elements.append(Spacer(1, 2))

                if notes:
                    cat_elements.append(Paragraph(f"<i>Pricing Verification:</i> {notes}", callout_style))

                cat_elements.append(Spacer(1, 8))
                elements.append(KeepTogether(cat_elements))

    # =========================================================================
    # 4. AI Business Idea Validator Section
    # =========================================================================
    val_data = getattr(validator_report, "content_json", None) or getattr(validator_report, "report_json", None) if validator_report else None
    if val_data:
        elements.append(PageBreak())
        val_ver = getattr(validator_report, "version", 1)
        elements.append(Paragraph(f"4. AI Idea Validation & Risk Interrogation (Version {val_ver})", h1_style))

        if "overview" in val_data:
            elements.append(Paragraph(f"<b>Validation Synthesis:</b> {val_data['overview']}", body_style))
            elements.append(Spacer(1, 6))

        # Problem-Solution Fit
        ps_fit = val_data.get("problem_solution_fit", {})
        if ps_fit:
            elements.append(Paragraph("Problem–Solution Fit", h2_style))
            elements.append(Paragraph(f"<b>Problem Statement:</b> {ps_fit.get('problem_statement', 'N/A')}", body_style))
            elements.append(Paragraph(f"<b>Who Experiences It:</b> {ps_fit.get('who_experiences_it', 'N/A')}", body_style))
            elements.append(Paragraph(f"<b>Severity & Frequency:</b> {ps_fit.get('frequency_and_severity', 'N/A')}", body_style))
            elements.append(Spacer(1, 6))

        # SWOT Analysis Table
        swot = val_data.get("swot_analysis", {})
        if swot:
            elements.append(Paragraph("SWOT Strategic Matrix", h2_style))
            s_text = "<br/>".join([f"• {x}" for x in swot.get("strengths", [])]) or "None noted"
            w_text = "<br/>".join([f"• {x}" for x in swot.get("weaknesses", [])]) or "None noted"
            o_text = "<br/>".join([f"• {x}" for x in swot.get("opportunities", [])]) or "None noted"
            t_text = "<br/>".join([f"• {x}" for x in swot.get("threats", [])]) or "None noted"

            swot_table_data = [
                [Paragraph("<b>STRENGTHS (Internal)</b>", meta_label), Paragraph("<b>WEAKNESSES (Internal)</b>", meta_label)],
                [Paragraph(s_text, body_style), Paragraph(w_text, body_style)],
                [Paragraph("<b>OPPORTUNITIES (External)</b>", meta_label), Paragraph("<b>THREATS (External)</b>", meta_label)],
                [Paragraph(o_text, body_style), Paragraph(t_text, body_style)],
            ]
            swot_table = Table(swot_table_data, colWidths=[252, 252])
            swot_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#f8fafc")),
                ("BACKGROUND", (0, 2), (1, 2), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(swot_table)
            elements.append(Spacer(1, 8))

        # Business Risks
        risks = val_data.get("business_risks", [])
        if risks:
            elements.append(Paragraph("Identified Business Risks & Mitigations", h2_style))
            risk_rows = [
                [
                    Paragraph("<b>Risk & Category</b>", meta_label),
                    Paragraph("<b>Severity</b>", meta_label),
                    Paragraph("<b>Suggested Mitigation & Action</b>", meta_label),
                ]
            ]
            for r in risks[:5]:
                cat = r.get("category", "General")
                desc = r.get("description", "")
                lik = r.get("likelihood", "Med")
                imp = r.get("impact", "Med")
                mit = r.get("suggested_mitigation", "")
                act = r.get("recommended_next_action", "")
                risk_rows.append([
                    Paragraph(f"<b>[{cat}]</b><br/>{desc}", body_style),
                    Paragraph(f"L: {lik}<br/>I: {imp}", body_style),
                    Paragraph(f"{mit}<br/><i>Next:</i> {act}", body_style),
                ])
            risk_table = Table(risk_rows, colWidths=[180, 64, 260])
            risk_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(risk_table)
            elements.append(Spacer(1, 8))

        # Validation Experiments
        experiments = val_data.get("validation_experiments", [])
        if experiments:
            elements.append(Paragraph("Actionable Validation Experiments", h2_style))
            for exp in experiments[:3]:
                name = exp.get("experiment_name", "Experiment")
                hypo = exp.get("hypothesis", "")
                proc = exp.get("procedure", "")
                crit = exp.get("success_criteria", "")
                dur = exp.get("estimated_duration", "1 week")
                elements.append(Paragraph(f"<b>• {name}</b> ({dur})<br/><b>Hypothesis:</b> {hypo}<br/><b>Procedure:</b> {proc}<br/><b>Success Criteria:</b> {crit}", body_style))
                elements.append(Spacer(1, 3))

    # =========================================================================
    # 5. Financial Projections Engine Section
    # =========================================================================
    if financial_model and getattr(financial_model, "projections_json", None):
        elements.append(PageBreak())
        fin_ver = getattr(financial_model, "version", 1)
        elements.append(Paragraph(f"5. Financial Projections & Scenario Engine (Version {fin_ver})", h1_style))

        proj = financial_model.projections_json
        summ = proj.get("summary_metrics", {})
        curr = financial_model.currency or "USD"

        # KPI Summary cards table
        kpi_data = [
            [
                Paragraph("<b>Break-Even Units</b>", meta_label),
                Paragraph("<b>Break-Even Revenue</b>", meta_label),
                Paragraph("<b>Startup Capital Req</b>", meta_label),
                Paragraph("<b>Cash Runway</b>", meta_label),
            ],
            [
                Paragraph(f"{summ.get('break_even_units', 'N/A')} units", h2_style),
                Paragraph(f"{curr} {summ.get('break_even_revenue', 0.0):,.0f}", h2_style),
                Paragraph(f"{curr} {summ.get('initial_capital_required', 0.0):,.0f}", h2_style),
                Paragraph(f"{summ.get('runway_months', 0.0):.1f} mos", h2_style),
            ],
        ]
        kpi_table = Table(kpi_data, colWidths=[126, 126, 126, 126])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 10))

        # Monthly Forecast Table
        monthly = proj.get("monthly_projections", [])
        if monthly:
            elements.append(Paragraph("12-Month Projections (Deterministic Python Calculations)", h2_style))
            forecast_rows = [
                [
                    Paragraph("<b>Mo</b>", meta_label),
                    Paragraph("<b>Units</b>", meta_label),
                    Paragraph("<b>Revenue</b>", meta_label),
                    Paragraph("<b>COGS</b>", meta_label),
                    Paragraph("<b>Gross Profit</b>", meta_label),
                    Paragraph("<b>Operating Exp</b>", meta_label),
                    Paragraph("<b>Net Profit</b>", meta_label),
                    Paragraph("<b>Closing Cash</b>", meta_label),
                ]
            ]
            for m in monthly[:12]:
                mo_num = m.get("month", 0)
                u = m.get("units_sold", 0)
                rev = m.get("revenue", 0.0)
                cogs = m.get("cogs", 0.0)
                gp = m.get("gross_profit", 0.0)
                opex = m.get("operating_expenses", 0.0)
                np = m.get("net_profit", 0.0)
                cc = m.get("closing_cash", 0.0)
                forecast_rows.append([
                    Paragraph(f"M{mo_num}", body_style),
                    Paragraph(f"{u:,}", body_style),
                    Paragraph(f"{rev:,.0f}", body_style),
                    Paragraph(f"{cogs:,.0f}", body_style),
                    Paragraph(f"{gp:,.0f}", body_style),
                    Paragraph(f"{opex:,.0f}", body_style),
                    Paragraph(f"{np:,.0f}", body_style),
                    Paragraph(f"{cc:,.0f}", body_style),
                ])
            forecast_table = Table(forecast_rows, colWidths=[28, 48, 68, 62, 68, 76, 76, 78])
            forecast_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(forecast_table)
            elements.append(Spacer(1, 8))

        # Scenario Comparisons
        scenarios = financial_model.scenarios_json
        if scenarios:
            elements.append(Paragraph("Scenario Comparison (Sensitivity Modeling)", h2_style))
            scen_rows = [
                [
                    Paragraph("<b>Scenario</b>", meta_label),
                    Paragraph("<b>Monthly Growth</b>", meta_label),
                    Paragraph("<b>Annual Revenue</b>", meta_label),
                    Paragraph("<b>Annual Net Profit</b>", meta_label),
                    Paragraph("<b>Breakeven Units</b>", meta_label),
                ]
            ]
            for sc_name in ["conservative", "expected", "optimistic"]:
                sc = scenarios.get(sc_name, {})
                if sc:
                    sc_summ = sc.get("summary_metrics", {})
                    sc_assump = sc.get("assumptions", {})
                    scen_rows.append([
                        Paragraph(f"<b>{sc_name.capitalize()}</b>", body_style),
                        Paragraph(f"{sc_assump.get('monthly_growth_rate', 0.0) * 100:.1f}%", body_style),
                        Paragraph(f"{curr} {sc_summ.get('total_revenue_forecast', 0.0):,.0f}", body_style),
                        Paragraph(f"{curr} {sc_summ.get('total_net_profit_forecast', 0.0):,.0f}", body_style),
                        Paragraph(f"{sc_summ.get('break_even_units', 'N/A')}", body_style),
                    ])
            scen_table = Table(scen_rows, colWidths=[104, 95, 105, 105, 95])
            scen_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(scen_table)
            elements.append(Spacer(1, 8))

    # =========================================================================
    # 6. Market & Competitor Intelligence Section
    # =========================================================================
    r_data = getattr(research_report, "content_json", None) or getattr(research_report, "report_json", None) if research_report else None
    if r_data:
        elements.append(PageBreak())
        res_ver = getattr(research_report, "version", 1)
        elements.append(Paragraph(f"6. Market & Competitor Intelligence (Version {res_ver})", h1_style))

        if "executive_summary" in r_data:
            elements.append(Paragraph(f"<b>Executive Market Overview:</b> {r_data['executive_summary']}", body_style))
            elements.append(Spacer(1, 6))

        # Trends
        trends = r_data.get("market_trends", [])
        if trends:
            elements.append(Paragraph("Key Industry Trends & Signals", h2_style))
            for tr in trends[:3]:
                title = tr.get("trend_title", "Trend")
                desc = tr.get("description", "")
                imp = tr.get("implications_for_founder", "")
                elements.append(Paragraph(f"<b>• {title}:</b> {desc}<br/><i>Implication:</i> {imp}", body_style))
                elements.append(Spacer(1, 3))
            elements.append(Spacer(1, 6))

        # Competitors Table
        competitors = r_data.get("competitors", [])
        if competitors:
            elements.append(Paragraph("Competitor Benchmark Matrix", h2_style))
            comp_rows = [
                [
                    Paragraph("<b>Competitor</b>", meta_label),
                    Paragraph("<b>Pricing</b>", meta_label),
                    Paragraph("<b>Key Features</b>", meta_label),
                    Paragraph("<b>Differentiator</b>", meta_label),
                ]
            ]
            for c in competitors[:5]:
                c_name = c.get("name", "Competitor")
                c_site = c.get("website", "")
                c_price = c.get("estimated_pricing", "Unknown")
                c_feats = ", ".join(c.get("key_features", [])[:3])
                c_diff = ", ".join(c.get("differentiators", [])[:2])
                comp_rows.append([
                    Paragraph(f"<b>{c_name}</b><br/><i>{c_site}</i>", body_style),
                    Paragraph(c_price, body_style),
                    Paragraph(c_feats or "N/A", body_style),
                    Paragraph(c_diff or "N/A", body_style),
                ])
            comp_table = Table(comp_rows, colWidths=[120, 94, 150, 140])
            comp_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(comp_table)
            elements.append(Spacer(1, 8))

    # =========================================================================
    # 7. Actionable Execution Roadmap Section
    # =========================================================================
    if roadmap_tasks:
        elements.append(PageBreak())
        elements.append(Paragraph("7. Actionable Execution Roadmap (30-60-90 Day)", h1_style))
        elements.append(Paragraph("Phased operational milestones to guide MVP buildout, founder validation, and distribution sprints.", body_style))
        elements.append(Spacer(1, 6))

        task_rows = [
            [
                Paragraph("<b>Key</b>", meta_label),
                Paragraph("<b>Phase</b>", meta_label),
                Paragraph("<b>Task Title & Scope</b>", meta_label),
                Paragraph("<b>Priority</b>", meta_label),
                Paragraph("<b>Status</b>", meta_label),
                Paragraph("<b>Deliverable</b>", meta_label),
            ]
        ]
        for t in roadmap_tasks[:12]:
            t_key = getattr(t, "task_key", "TSK")
            t_m = getattr(t, "milestone", "30-day")
            t_tit = getattr(t, "title", "Task")
            t_prio = getattr(t, "priority", "medium")
            t_stat = getattr(t, "status", "pending")
            t_del = getattr(t, "deliverable", "")
            task_rows.append([
                Paragraph(t_key, body_style),
                Paragraph(t_m, body_style),
                Paragraph(f"<b>{t_tit}</b>", body_style),
                Paragraph(t_prio.capitalize(), body_style),
                Paragraph(t_stat.capitalize(), body_style),
                Paragraph(t_del or "N/A", body_style),
            ])
        task_table = Table(task_rows, colWidths=[45, 52, 175, 48, 52, 132])
        task_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(task_table)
        elements.append(Spacer(1, 8))

    # Legal Disclaimer at the end
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=8))
    disclaimer_text = (
        "<b>Important Notice:</b> This document was generated using AI Business Architect for preliminary planning "
        "and architectural exploratory purposes only. Recommendations, cost estimates, and business models do not "
        "constitute certified financial, legal, tax, or investment advice. Market pricing and vendor terms must be "
        "independently verified prior to commercial commitments."
    )
    elements.append(Paragraph(disclaimer_text, callout_style))

    # Build document with header and footer
    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
