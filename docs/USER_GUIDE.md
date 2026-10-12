# AI Business Architect — End User Guide

Welcome to **AI Business Architect**! This guide walks you through transforming your raw business concept into a structured, investor-ready blueprint.

---

## 1. Creating Your Account
1. Open the application homepage.
2. Click **Start building** or **Register**.
3. Choose a unique username and enter your email address.
4. Create a strong password (minimum 8 characters, containing at least one letter and one number).
5. Review and accept the **Terms and Conditions** and acknowledge the **Privacy Policy**.
6. Click **Create Account & Get Started**. You are automatically signed in to your dashboard.

---

## 2. Creating a Business Project
1. From the Dashboard, click **New Project** or **Create Project**.
2. Follow the 4-step Guided Intake Wizard:
   - **Step 1: Project Identity**: Name your project, select an industry, and write a detailed description of the problem and proposed solution.
   - **Step 2: Target Audience & Market**: Specify your current business stage (Idea, Validation, Prototype, MVP, Growth), target geographic market, and ideal customer profile.
   - **Step 3: Capital & Constraints**: Enter your estimated budget (or leave blank if bootstrapped), team composition, and technical preferences.
   - **Step 4: Review & Submit**: Review the summary and click **Create Project Workspace**.

---

## 3. Generating the Business Model Canvas
1. In your project workspace, select the **Business Model Canvas** tab.
2. Click **Generate Canvas**.
3. The platform invokes Google Gemini to generate all 9 standard canvas blocks:
   - Customer Segments
   - Value Propositions
   - Channels
   - Customer Relationships
   - Revenue Streams
   - Key Resources
   - Key Activities
   - Key Partnerships
   - Cost Structure
4. Click the edit icon on any block to modify summaries, recommendations, assumptions, risks, or validation experiments, then click **Save Changes**.
5. To generate a fresh perspective, click **Regenerate Canvas**. Your previous versions are preserved in the **Active Version** dropdown.

---

## 4. Generating the Technology Stack Recommendation
1. Select the **Technology Stack** tab.
2. Click **Generate Tech Stack**.
3. The architecture engine provides tailored recommendations across 5 categories:
   - Frontend
   - Backend
   - Database
   - Hosting & Infrastructure
   - Third-Party Services
4. Review rationale, trade-offs, estimated monthly costs, scalability milestones, and security safeguards.
5. Click edit on any category to adjust frameworks or libraries to match your team's skills.

---

## 5. Validating Your Venture with the AI Idea Validator
1. Select the **Idea Validator** tab in your project workspace.
2. Click **Generate Validation Report**.
3. Review the comprehensive strategic evaluation:
   - **Problem–Solution Fit**: Objective analysis of problem friction, who experiences it, and existing workarounds.
   - **Target Customer Clarity**: Separation of economic buyers from daily users, adoption barriers, and unvalidated behavioral assumptions.
   - **Value Proposition Assessment**: Core benefit hypotheses, differentiation drivers, and critical technical/partner dependencies.
   - **SWOT Analysis**: 4-quadrant breakdown of internal advantages, operational vulnerabilities, market opportunities, and competitive hazards.
   - **Business Risk Matrix**: Categorized risks (Customer Adoption, Market, Tech, Regulatory, Financial) with likelihood, impact, and concrete mitigations.
   - **Lean Validation Experiments**: Pragmatic, low-cost tests (Interviews, Landing Pages, Concierge Pilots) with explicit hypotheses and measurable success metrics.
   - **Customer Interview Script**: Neutral, non-leading discovery questions focused on past behavior (Mom-Test style) rather than speculative validation.
4. Click **Edit Report** to refine notes, hypotheses, or experiments, then click **Save Refinements**. Historical runs are saved under the version selector.

---

## 6. Live Market and Competitor Research
1. Select the **Market Research** tab in your project workspace.
2. Click **Run Market Research**.
3. The platform executes live external web research backed by automated SSRF protection:
   - **Competitor Profiles**: Identified direct and indirect competitors with positioning, pricing models, key features, and perceived strengths/weaknesses.
   - **Verified Source Citations**: Every competitor insight and market trend includes clickable source links with access timestamps and evidence notes.
   - **Market Trends & Dynamics**: Macro industry shifts and their strategic implications for your venture.
   - **Comparison Matrix**: Side-by-side feature and pricing comparison between your planned solution and incumbents.
4. If internet connectivity or external search engines are unavailable, a clear notice is shown and existing data is preserved without generating fake URLs or synthetic citations.
5. Click **Edit Research** to customize competitor notes or add proprietary findings.

---

## 7. Managing Your Phased Execution Roadmap
1. Select the **Execution Roadmap** tab in your project workspace.
2. Click **Generate Roadmap** to produce an intelligent 30-day, 60-day, and 90-day milestone plan:
   - **30-Day Milestone (Customer Validation & Research)**: High-priority customer discovery, competitor testing, and lean experiment execution.
   - **60-Day Milestone (MVP Prototype & Pilot)**: Core prototype development, early user onboarding, and core loop testing.
   - **90-Day Milestone (Launch Prep & Scale)**: Public release, analytics tracking, retention optimization, and feedback loops.
3. Track Progress:
   - View visual completion bars showing percentage of tasks completed per milestone.
   - Filter tasks by status: `Not Started`, `In Progress`, `Completed`, or `Blocked`.
   - Update task status directly from the card dropdown.
4. Customize Tasks:
   - Click **Add Task** to create custom deliverables, specify estimated effort days, and declare task dependencies.
   - Circular dependencies are automatically prevented by the backend's DAG cycle detection engine.
   - Edit or delete tasks as your priorities evolve.

---

## 8. Strategic Guidance with Business Blueprint Copilot
1. Open the **Blueprint Copilot** panel in your project workspace.
2. The Copilot is an AI advisor operating exclusively on your current project's blueprints, validation findings, and roadmap:
   - **Ask Strategic Questions**: Select "Ask a Question" to ask questions like *"What are my biggest risks before launching an MVP?"* or *"How should I price this for solo creators?"* Copilot returns reasoned, contextual advice without altering your saved blueprints.
   - **Propose Block Edits**: Select "Propose an Edit", choose a target module (e.g., Business Model Canvas) and section (e.g., Value Proposition), and describe your intended update.
3. Safe Diff Previews:
   - Copilot returns a visual before-and-after comparison showing previous content alongside proposed content and strategic reasoning.
   - **Accept Proposal**: Clicking Accept immediately applies the edit to the project blueprint and creates an audit record.
   - **Reject Proposal**: Clicking Reject dismisses the suggestion; your saved blueprint remains completely untouched.
4. Click **Revision History** to review past copilot proposals and decisions.

---

## 9. Exporting Your Blueprint to PDF
1. From the project header, click **Export PDF Blueprint**.
2. A professional, publication-ready multi-page PDF document is generated and downloaded to your computer.
3. The document includes executive summaries, the complete 9-block canvas, full technology recommendations, idea validation findings, competitor intelligence, and active roadmap milestones suitable for co-founders, advisors, or grant applications.

---

## 10. Profile & Security Management
1. Click your name in the top navigation bar and select **Profile & Settings**.
2. Update your display name, bio, country, or preferred currency.
3. Change your password in the **Change Security Password** section (Argon2id re-hashing automatically revokes other active sessions).
4. To permanently purge your account and all associated projects, navigate to the **Danger Zone**, enter your password, type **DELETE**, and confirm.
