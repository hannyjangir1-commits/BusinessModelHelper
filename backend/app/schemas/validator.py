"""Pydantic v2 schemas for AI Business Idea Validator."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ProblemSolutionFit(BaseModel):
    """Assessment of problem definition, urgency, and current alternatives."""

    problem_statement: str = Field(..., description="Refined, objective definition of the problem")
    who_experiences_it: str = Field(..., description="Specific demographics or user groups impacted")
    frequency_and_severity: str = Field(..., description="How frequently and severely this friction occurs")
    existing_alternatives: List[str] = Field(default_factory=list, description="Workarounds and competitors currently used")
    supporting_evidence: List[str] = Field(default_factory=list, description="Observed facts or data points supporting the problem")
    missing_evidence: List[str] = Field(default_factory=list, description="Critical unknowns requiring field verification")


class TargetCustomerClarity(BaseModel):
    """Analysis of buyer vs user dynamics, barriers, and pain points."""

    primary_segment: str = Field(..., description="The single beachhead customer group with highest urgency")
    secondary_segments: List[str] = Field(default_factory=list, description="Expansion or adjacent target audiences")
    buyer_vs_end_user: str = Field(..., description="Distinction between who authorizes payment and who uses daily")
    customer_pain_points: List[str] = Field(default_factory=list, description="Core emotional, financial, or operational frustrations")
    adoption_barriers: List[str] = Field(default_factory=list, description="Switching costs, habits, or organizational inertia")
    unvalidated_assumptions: List[str] = Field(default_factory=list, description="Assumptions about customer willingness to adopt")


class ValuePropositionAssessment(BaseModel):
    """Evaluation of proposed differentiation, value driver, and dependencies."""

    core_benefit: str = Field(..., description="The single primary benefit delivered to customers")
    differentiation_hypotheses: List[str] = Field(default_factory=list, description="Why this solution beats existing alternatives")
    potential_weaknesses: List[str] = Field(default_factory=list, description="Vulnerabilities or reasons customers might hesitate")
    critical_dependencies: List[str] = Field(default_factory=list, description="Key technical, operational, or partner dependencies")
    key_evidence_needed: List[str] = Field(default_factory=list, description="Proof points required to establish credibility")


class SWOTAnalysis(BaseModel):
    """Comprehensive 4-quadrant SWOT analysis."""

    strengths: List[str] = Field(..., min_length=2, description="Internal advantages and unique capabilities")
    weaknesses: List[str] = Field(..., min_length=2, description="Internal limitations, missing resources, or execution gaps")
    opportunities: List[str] = Field(..., min_length=2, description="External favorable market trends, shifts, or unserved niches")
    threats: List[str] = Field(..., min_length=2, description="External competitive, technological, or regulatory hazards")


class BusinessRiskItem(BaseModel):
    """Detailed risk profile with qualitative likelihood, impact, and mitigation."""

    category: str = Field(..., description="Market, Customer Adoption, Financial, Operational, Technology, Competition, Regulatory")
    description: str = Field(..., description="Specific hazard or vulnerability")
    why_it_matters: str = Field(..., description="Consequences if this risk materializes")
    likelihood: str = Field(..., description="Qualitative estimate: Low, Medium, High")
    impact: str = Field(..., description="Qualitative estimate: Low, Medium, High")
    supporting_info: str = Field(..., description="Contextual indicators supporting this assessment")
    suggested_mitigation: str = Field(..., description="Specific strategic safeguard to de-risk")
    recommended_next_action: str = Field(..., description="Immediate concrete action for the founder")


class ValidationExperiment(BaseModel):
    """Actionable pre-launch experiment to test assumptions."""

    experiment_name: str = Field(..., description="Descriptive name of test")
    experiment_type: str = Field(..., description="Customer Interviews, Landing Page, Prototype, Willingness to Pay, Pilot")
    hypothesis: str = Field(..., description="Specific testable statement (If we..., then X% will...)")
    target_audience: str = Field(..., description="Who to recruit for this experiment")
    procedure: str = Field(..., description="Step-by-step test execution method")
    estimated_duration: str = Field(..., description="Time required (e.g., 1-2 weeks)")
    estimated_cost: str = Field(..., description="Realistic budget required (e.g., $0 - $100)")
    success_criteria: str = Field(..., description="Measurable threshold to validate the hypothesis")
    interpretation_guidance: str = Field(..., description="How to act if results are positive vs negative")


class CustomerInterviewQuestion(BaseModel):
    """Neutral, non-leading discovery question."""

    question_text: str = Field(..., description="Exact phrasing to ask potential customers")
    focus_category: str = Field(..., description="Past Behavior, Current Friction, Existing Workaround, Budget Authority")
    rationale: str = Field(..., description="Why this question reveals genuine intent rather than polite praise")


class ValidationSummary(BaseModel):
    """Executive conclusions and overall qualitative readiness."""

    strongest_supporting_evidence: str = Field(..., description="Most compelling reason this business could succeed")
    largest_uncertainties: List[str] = Field(default_factory=list, description="Top unanswered questions")
    highest_priority_risks: List[str] = Field(default_factory=list, description="Risks requiring immediate attention")
    most_useful_next_experiment: str = Field(..., description="The single highest-leverage test to run next")
    unverified_assumptions: List[str] = Field(default_factory=list, description="Critical assumptions still pending proof")
    qualitative_readiness_assessment: str = Field(
        ...,
        description="Reasoned evaluation of current readiness (e.g., Discovery Stage, Pre-Validation, Ready for MVP)",
    )


class ValidationReportData(BaseModel):
    """Complete structured output for the AI Business Idea Validator."""

    overview: str = Field(..., description="Executive summary of the validation findings")
    problem_solution_fit: ProblemSolutionFit
    target_customer_clarity: TargetCustomerClarity
    value_proposition_assessment: ValuePropositionAssessment
    swot_analysis: SWOTAnalysis
    business_risks: List[BusinessRiskItem] = Field(..., min_length=3)
    validation_experiments: List[ValidationExperiment] = Field(..., min_length=2)
    interview_questions: List[CustomerInterviewQuestion] = Field(..., min_length=3)
    summary: ValidationSummary


class ValidationUpdateRequest(BaseModel):
    """Payload for updating or refining validation report content."""

    content: ValidationReportData
