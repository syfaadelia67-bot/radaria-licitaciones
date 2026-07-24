# One-time Tally activation

This is the only owner action required to activate real lead capture.

## Create the form

Create a free Tally form named **TenderSignal Founder Application**.

Introductory text:

> TenderSignal ranks verified public-procurement opportunities against a supplier profile. This application helps us determine whether the current data can produce useful matches for your company. Submitting does not create a purchase obligation, and no payment is collected in this form.

Add these required questions:

1. **Work email** — email input
2. **Company name** — short text
3. **Company website** — URL, optional
4. **Which markets do you sell into?** — multi-select
5. **What services or products do you provide?** — long text
6. **Typical contract capacity** — single select: Under USD 50k / USD 50k–250k / USD 250k–1m / Above USD 1m / Varies
7. **How do you currently discover public tenders?** — long text
8. **What would be most useful?** — multi-select: Ranked alerts / Bid-or-skip brief / Deadline monitoring / Market intelligence / Historical awards
9. **Founder interest** — single select: Free validation report / Provisional USD 10 for 60 days / Research only
10. **Contact consent** — required checkbox:

> I agree that TenderSignal may use these responses to assess supplier fit, provide the requested validation and contact me about this application. I understand that I can request deletion or unsubscribe at any time.

Add hidden fields with these exact case-sensitive names:

- `source`
- `originPage`
- `offer`
- `opportunityId`

## Configure operations

1. Publish the form.
2. Enable **Self email notifications**. This is the required alert channel.
3. Treat Tally's **Submissions** dashboard as the primary lead register.
4. Connect **Google Sheets only when the account permits it**. This integration is optional and must never block activation.
5. Enable duplicate prevention and reCAPTCHA if available in form settings.
6. Use this thank-you message:

> Application received. TenderSignal will only contact you about this validation request and any founder-plan interest you selected. No payment has been charged.

### Restricted institutional Google accounts

If Google authorization requires an administrator:

- do not request an exception or share credentials;
- leave Google Sheets disconnected;
- verify each application in Tally's Submissions dashboard;
- use the free self-email notification as the immediate alert;
- export an individual submission as PDF from Tally when a portable record is needed;
- reconsider a spreadsheet connection later using an owner-controlled account only if operational volume justifies it.

This fallback still provides real external lead capture. A spreadsheet is an operational convenience, not a launch requirement.

## Activate the website

The published URL will look like:

`https://tally.so/r/ABC123`

Only the final public identifier (`ABC123` in this example) is needed in `lead-config.js`:

```js
window.TenderSignalLeadConfig = Object.freeze({
  provider: "tally",
  formId: "ABC123",
  enabled: true,
  privacyVersion: "2026-07-24",
});
```

The identifier is public routing information. Never share a password, account session, Google authorization token or private response data.
