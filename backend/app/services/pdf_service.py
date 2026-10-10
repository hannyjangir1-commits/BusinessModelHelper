"""Professional PDF generation service using ReportLab."""

import io
from datetime import datetime, timezone
from typing import Optional
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
