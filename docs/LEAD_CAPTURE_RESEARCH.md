# Lead capture provider decision

Decision date: 2026-07-24

## Selected provider: Tally

TenderSignal will use a Tally form as the first external lead-capture destination.

Reasons:

- free forms and submissions under Tally's fair-usage policy;
- free owner email notifications;
- free Google Sheets integration and exportable responses;
- hidden fields for source and campaign attribution;
- European data hosting and GDPR-oriented controls;
- no API key or private secret is required in the public website.

## Required form fields

1. Work email
2. Company name
3. Company website (optional)
4. Preferred procurement markets
5. Service categories / keywords
6. Typical contract capacity
7. Current tender-discovery process
8. Founder offer interest: free validation report / paid founder plan / research only
9. Explicit consent to be contacted about TenderSignal

Hidden fields:

- `source`
- `originPage`
- `offer`
- `opportunityId`

## Privacy and operations

- Collect only fields needed to qualify supplier demand.
- The form must state why the information is collected.
- Do not add contacts to bulk marketing without explicit consent.
- Owner email notifications should be enabled.
- Responses should be connected to an exportable Google Sheet.
- Deletion and unsubscribe requests must be handled from the same inbox receiving lead alerts.
- Do not commit private response data, email addresses, API tokens or account credentials to GitHub.

## Activation

The website reads the public form identifier from `lead-config.js`. Until that identifier is configured, buttons remain honest and no data is collected.

The form identifier is public routing information, not a password or secret.
