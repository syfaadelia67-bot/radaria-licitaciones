#!/usr/bin/env python3
"""Score a privacy-minimized founder application and produce a repeatable report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FORBIDDEN_PERSONAL_FIELDS = {
    "email", "work_email", "name", "full_name", "phone", "telephone", "address"
}

CAPACITY_POINTS = {
    "Under USD 50k": 5,
    "USD 50k–250k": 10,
    "USD 250k–1m": 15,
    "Above USD 1m": 15,
    "Varies": 10,
}

INTEREST_POINTS = {
    "Free validation report": 5,
    "Provisional USD 10 for 60 days": 10,
    "Research only": 2,
}

FEATURES = {
    "Ranked alerts", "Bid-or-skip brief", "Deadline monitoring",
    "Market intelligence", "Historical awards",
}


def clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def list_of_text(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]
    text = clean_text(value)
    return [text] if text else []


def validate_input(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Application input must be a JSON object")
    personal = sorted(FORBIDDEN_PERSONAL_FIELDS.intersection(payload))
    if personal:
        raise ValueError(
            "Personal contact fields are not accepted by this scoring tool: " + ", ".join(personal)
        )
    required_nonempty = (
        "company", "markets", "products_services", "contract_capacity",
        "discovery_process", "founder_interest",
    )
    missing = [field for field in required_nonempty if not payload.get(field)]
    if "useful_features" not in payload:
        missing.append("useful_features")
    if missing:
        raise ValueError("Missing required non-personal fields: " + ", ".join(missing))
    return payload


def score_application(payload: dict[str, Any]) -> dict[str, Any]:
    payload = validate_input(payload)
    markets = list_of_text(payload.get("markets"))
    products = clean_text(payload.get("products_services"))
    discovery = clean_text(payload.get("discovery_process"))
    features = [item for item in list_of_text(payload.get("useful_features")) if item in FEATURES]
    capacity = clean_text(payload.get("contract_capacity"))
    founder_interest = clean_text(payload.get("founder_interest"))
    opportunity_id = clean_text(payload.get("opportunity_id"))

    dimensions: list[dict[str, Any]] = []

    market_score = 20 if len(markets) >= 2 else 14 if len(markets) == 1 else 0
    dimensions.append({"name": "Market specificity", "score": market_score, "max": 20, "evidence": ", ".join(markets) or "No market supplied"})

    product_word_count = len(products.split())
    product_score = 20 if product_word_count >= 12 else 14 if product_word_count >= 6 else 8
    dimensions.append({"name": "Offering clarity", "score": product_score, "max": 20, "evidence": products})

    procurement_terms = ("tender", "procurement", "bid", "portal", "framework", "licit", "contract")
    procurement_score = 20 if any(term in discovery.lower() for term in procurement_terms) else 12 if len(discovery.split()) >= 8 else 6
    dimensions.append({"name": "Procurement relevance", "score": procurement_score, "max": 20, "evidence": discovery})

    capacity_score = CAPACITY_POINTS.get(capacity, 0)
    dimensions.append({"name": "Contract capacity", "score": capacity_score, "max": 15, "evidence": capacity})

    feature_score = min(15, len(features) * 4)
    dimensions.append({"name": "Product-use fit", "score": feature_score, "max": 15, "evidence": ", ".join(features) or "No recognized feature selected"})

    intent_score = INTEREST_POINTS.get(founder_interest, 0)
    dimensions.append({"name": "Commercial intent", "score": intent_score, "max": 10, "evidence": founder_interest})

    total = sum(item["score"] for item in dimensions)
    if total >= 70:
        band = "Qualified founder candidate"
        next_step = "Deliver a tailored validation report and ask for an explicit founder-plan decision."
    elif total >= 45:
        band = "Discovery candidate"
        next_step = "Deliver a short sample and ask one concrete question about missing fit criteria."
    else:
        band = "Research signal"
        next_step = "Thank the applicant, record the product-learning signal and avoid a payment request."

    strengths = [item["name"] for item in dimensions if item["score"] >= item["max"] * 0.7]
    gaps = [item["name"] for item in dimensions if item["score"] < item["max"] * 0.5]

    return {
        "company": clean_text(payload.get("company")),
        "opportunity_id": opportunity_id or None,
        "score": total,
        "maximum": 100,
        "band": band,
        "dimensions": dimensions,
        "strengths": strengths,
        "gaps": gaps,
        "recommended_next_step": next_step,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# TenderSignal founder validation — {result['company']}",
        "",
        "> This report is a deterministic qualification summary, not procurement, legal or eligibility advice.",
        "",
        f"**Qualification score:** {result['score']}/{result['maximum']}  ",
        f"**Band:** {result['band']}  ",
    ]
    if result.get("opportunity_id"):
        lines.append(f"**Attributed opportunity:** `{result['opportunity_id']}`  ")
    lines.extend(["", "## Evidence by dimension", ""])
    for item in result["dimensions"]:
        lines.append(f"- **{item['name']}: {item['score']}/{item['max']}** — {item['evidence']}")

    lines.extend(["", "## Strengths", ""])
    lines.extend(f"- {item}" for item in result["strengths"])
    if not result["strengths"]:
        lines.append("- No strong dimension identified yet.")

    lines.extend(["", "## Information gaps", ""])
    lines.extend(f"- {item}" for item in result["gaps"])
    if not result["gaps"]:
        lines.append("- No major qualification gap identified.")

    lines.extend([
        "",
        "## Recommended next step",
        "",
        result["recommended_next_step"],
        "",
        "## Commercial boundary",
        "",
        "No payment should be requested until the applicant has received useful output and explicitly agrees to a separate payment step. The provisional founder offer is USD 10 for 60 days and must not be described as scarce unless a real operational limit exists.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Privacy-minimized JSON application")
    parser.add_argument("--output", type=Path, default=Path("founder-validation-report.md"))
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = score_application(payload)
    args.output.write_text(render_markdown(result), encoding="utf-8")
    print(f"Generated {result['band']} report at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
