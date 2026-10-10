"""AI pipeline evaluation suite measuring schema pass rate, completeness, and consistency."""

import json
import os
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import get_settings
from app.models.project import Project
from app.services.ai.business_rules import evaluate_bmc_rules, evaluate_tech_stack_rules
from app.services.ai.client import GeminiAIClient, MockAIClient
from app.services.ai.prompts import build_bmc_prompt, build_tech_stack_prompt
from app.services.ai.validation import validate_bmc_response, validate_tech_stack_response


def run_evaluation():
    settings = get_settings()
    test_cases_path = Path(__file__).parent / "test_cases.json"

    with open(test_cases_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"==================================================")
    print(f"AI Business Architect — AI Evaluation Suite")
    print(f"Total Test Cases: {len(test_cases)}")
    print(f"==================================================")

    # Use live Gemini client if key is configured, unless --mock is specified
    force_mock = "--mock" in sys.argv or os.environ.get("USE_MOCK_EVAL", "").lower() in ("1", "true")
    has_api_key = bool(settings.gemini_api_key and settings.gemini_api_key.strip())
    if has_api_key and not force_mock:
        print(f"Executing with LIVE Gemini API (Model: {settings.gemini_model})")
        client = GeminiAIClient()
    else:
        print("Executing with MockAIClient for reproducible evaluation.")
        client = MockAIClient()

    results = []
    total_evaluations = 0
    passed_schemas = 0
    total_latency_ms = 0

    for idx, tc in enumerate(test_cases, 1):
        case_id = tc["id"]
        print(f"\n[{idx}/{len(test_cases)}] Evaluating: {tc['name']} ({tc['industry']})")

        dummy_project = Project(
            name=tc["name"],
            industry=tc["industry"],
            idea_description=tc["idea_description"],
            business_stage=tc.get("business_stage", "idea"),
            target_market=tc.get("target_market"),
            target_audience=tc.get("target_audience"),
            budget_amount=tc.get("budget_amount"),
            budget_currency=tc.get("budget_currency", "USD"),
            team_size=tc.get("team_size"),
            technical_preferences=tc.get("technical_preferences"),
            constraints=tc.get("constraints"),
        )

        case_result = {
            "case_id": case_id,
            "name": tc["name"],
            "industry": tc["industry"],
            "bmc": {},
            "tech_stack": {},
        }

        # 1. Evaluate Business Model Canvas
        total_evaluations += 1
        sys_prompt, user_prompt = build_bmc_prompt(dummy_project)
        t0 = time.perf_counter()
        bmc_passed = False
        try:
            raw_text, lat, in_tok, out_tok = client.generate(sys_prompt, user_prompt)
            bmc_data = validate_bmc_response(raw_text)
            _, warnings = evaluate_bmc_rules(bmc_data, dummy_project)
            elapsed = int((time.perf_counter() - t0) * 1000)
            total_latency_ms += elapsed

            bmc_passed = True
            passed_schemas += 1
            case_result["bmc"] = {
                "status": "PASS",
                "blocks_present": 9,
                "latency_ms": elapsed,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "warnings_count": len(warnings),
                "warnings": warnings,
            }
            print(f"  [PASS] BMC (9/9 blocks, {elapsed}ms, {len(warnings)} advisories)")
        except Exception as e:
            case_result["bmc"] = {"status": "FAIL", "error": str(e)}
            print(f"  [FAIL] BMC ({str(e)})")

        # 2. Evaluate Technology Stack
        total_evaluations += 1
        sys_prompt, user_prompt = build_tech_stack_prompt(dummy_project)
        t0 = time.perf_counter()
        tech_passed = False
        try:
            raw_text, lat, in_tok, out_tok = client.generate(sys_prompt, user_prompt)
            tech_data = validate_tech_stack_response(raw_text)
            _, warnings = evaluate_tech_stack_rules(tech_data, dummy_project)
            elapsed = int((time.perf_counter() - t0) * 1000)
            total_latency_ms += elapsed

            tech_passed = True
            passed_schemas += 1
            case_result["tech_stack"] = {
                "status": "PASS",
                "categories_present": 5,
                "latency_ms": elapsed,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "warnings_count": len(warnings),
                "warnings": warnings,
            }
            print(f"  [PASS] Tech Stack (5/5 categories, {elapsed}ms, {len(warnings)} advisories)")
        except Exception as e:
            case_result["tech_stack"] = {"status": "FAIL", "error": str(e)}
            print(f"  [FAIL] Tech Stack ({str(e)})")

        # 3. Evaluate Idea Validator
        total_evaluations += 1
        from app.services.ai.validator_pipeline import build_validator_prompt, validate_validator_response
        sys_prompt, user_prompt = build_validator_prompt(dummy_project)
        t0 = time.perf_counter()
        val_passed = False
        try:
            raw_text, lat, in_tok, out_tok = client.generate(sys_prompt, user_prompt)
            val_data = validate_validator_response(raw_text)
            elapsed = int((time.perf_counter() - t0) * 1000)
            total_latency_ms += elapsed

            val_passed = True
            passed_schemas += 1
            case_result["validator"] = {
                "status": "PASS",
                "swot_present": True,
                "risks_count": len(val_data.business_risks),
                "experiments_count": len(val_data.validation_experiments),
                "latency_ms": elapsed,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
            }
            print(f"  [PASS] Validator (SWOT + {len(val_data.business_risks)} risks + {len(val_data.validation_experiments)} experiments, {elapsed}ms)")
        except Exception as e:
            case_result["validator"] = {"status": "FAIL", "error": str(e)}
            print(f"  [FAIL] Validator ({str(e)})")

        results.append(case_result)

    pass_rate = (passed_schemas / total_evaluations) * 100 if total_evaluations else 0
    avg_latency = (total_latency_ms / passed_schemas) if passed_schemas else 0

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_test_cases": len(test_cases),
        "total_module_runs": total_evaluations,
        "schema_pass_rate_percentage": round(pass_rate, 2),
        "average_latency_ms": round(avg_latency, 2),
        "execution_mode": "LIVE_GEMINI" if has_api_key else "MOCK_DETERMINISTIC",
        "detailed_results": results,
    }

    report_path = Path(__file__).parent / "evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n==================================================")
    print(f"Evaluation Summary:")
    print(f"Schema Pass Rate: {pass_rate:.1f}% ({passed_schemas}/{total_evaluations})")
    print(f"Average Latency: {avg_latency:.1f} ms")
    print(f"Report saved to: {report_path}")
    print(f"==================================================")

    return 0 if pass_rate == 100.0 else 1


if __name__ == "__main__":
    sys.exit(run_evaluation())
