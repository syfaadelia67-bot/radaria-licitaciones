# Founder application qualification and report operations

## Purpose

Convert a real Tally application into a consistent validation response without paid AI/API dependencies and without storing contact details in GitHub.

## Privacy boundary

Never copy the applicant's email address, personal name, phone number, postal address or private message into the repository or the scoring input. The scoring file should contain only business-profile information needed to assess product fit.

The tool rejects common personal-contact fields by design.

## Workflow

1. Open the application in Tally.
2. Confirm explicit contact consent.
3. Copy only non-personal business fields into a temporary local JSON file based on `templates/founder-application.example.json`.
4. Run:

   ```bash
   python scripts/score_founder_application.py application.json --output report.md
   ```

5. Review the evidence and correct any transcription error. Do not manually inflate the score.
6. Add a short, human-written opportunity analysis only after checking the official notice.
7. Send useful output before making a payment request.
8. Delete the temporary local JSON and generated report when the operational record is no longer needed, subject to the applicant's consent and deletion requests.

## Qualification bands

- **70–100: Qualified founder candidate.** Deliver a tailored report and request an explicit decision about the provisional founder plan.
- **45–69: Discovery candidate.** Deliver a useful sample and ask one concrete missing-fit question.
- **0–44: Research signal.** Thank the applicant and record product learning; do not request payment.

## Scoring dimensions

- Market specificity: 20 points.
- Offering clarity: 20 points.
- Procurement relevance: 20 points.
- Contract capacity: 15 points.
- Product-use fit: 15 points.
- Commercial intent: 10 points.

The score qualifies the application for product validation. It does not determine eligibility for any procurement procedure and must not be presented as bid advice.

## Payment boundary

The provisional offer is USD 10 for 60 days. Payment must be a separate, explicit step after useful output has been delivered and the prospect confirms they want to buy. Do not collect payment-card information in Tally, email, GitHub or the report generator.
