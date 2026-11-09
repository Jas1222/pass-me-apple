# Evidence, tests, and report format

## Submission cross-checks

These are investigation prompts, not a substitute for the retrieved rules. Select exact current clauses and exceptions before labeling a defect.

| Evidence pair | What to investigate |
|---|---|
| Listing identity ↔ binary | Same product, bundle, version, supported device families, locales, icon, and proposed release? Are public-listing assets from an older version? |
| Description/promotional text/what's new ↔ observed flows | Can the reviewer reach and reproduce each material promise? Are access, pricing and hardware conditions disclosed consistently? |
| Name/subtitle/keywords/categories ↔ current Connect reference | Correct field length/unit, category fit, unsupported claims, trademarks or irrelevant terms? Review every supplied locale. |
| Screenshots/previews/creative assets ↔ UI and specifications | Are supplied files technically suitable for the exact asset type/device? Compare actual content, paid states, overlays, image dimensions, preview duration/audio, and locale. Apply current rules for that asset type rather than assuming all assets are screenshots. |
| Privacy declaration/policy ↔ permissions/manifests/observed flows | Do collection purposes, third parties, accounts, retention, and tracking statements agree? What would require network, backend, or SDK-owner evidence? |
| Age questionnaire/category ↔ content and features | Compare selected answers to content, communications, web access, advertising, user-generated/AI content, and safeguards. Do not derive the final rating from the app icon or an old age-band table. |
| Paywalls/products ↔ business model and listing | Is the user buying digital access, a physical service, enterprise access, or another scoped case? Compare actual storefront and entitlement eligibility with the current payment rules before raising a finding. |
| Review notes/demo access ↔ app reachability | Can a reviewer access gated features and reproduce them with the supplied instructions? Are special hardware, backend, OTP, geography, and paid-state dependencies explained? |
| Accessibility declarations ↔ feature-specific tests | Can each claimed capability actually be demonstrated on the platforms declared? Read the linked Apple criteria for those capabilities. |
| Regulated claims/rights/export/regional declarations ↔ supplied documents | What proof is supplied and which declarations remain unavailable? Avoid inferring licenses, legal compliance, copyright ownership, or encryption exemptions from the binary alone. |

Create a claim table for material promises: `Listing field or asset | Claim | Runtime/static evidence | Consistent / Inconsistent / Not verified | Finding ID`. Visually inspect supplied images and videos with available media tools; file existence, OCR, or image dimensions alone do not establish truthfulness. Label any unsupported media format as unreviewed.

## Risk and certainty

- **High:** observed submission blocker or strong evidence of a material conflict with an applicable rule. A high-impact potential risk can also be High, but its unresolved condition must remain explicit.
- **Medium:** meaningful ambiguity, incomplete substantiation, inconsistent metadata, or functional concern likely to need clarification or correction.
- **Low:** limited submission concern; separate optional improvements under Recommendations.

Confidence is **High**, **Medium**, or **Low**, based on reproducibility, rule specificity, and evidence quality. Severity is not confidence or a numeric rejection probability. "Potential risk" is not a confirmed violation; "not verified" is not a pass. Avoid duplicate findings when several artifacts point to one root issue; preserve all relevant citations/evidence under the same finding.

## Local report and HTML dashboard

Use `index.html` as the primary deliverable, generated from the local Markdown report and CSV using `scripts/render_dashboard.py` as described in SKILL.md. Preserve the readable source report and raw coverage alongside it. Scale length to the evidence. A useful report contains:

1. **Readiness and scope.** Fix before submission / Further evidence needed / No material risks found in tested scope. Identify app version/build, artifact hashes, simulator companion differences, platform/runtime/devices, storefronts, locales, submission date, source retrieval date, and whether all intended inputs were available. Include important limitations immediately.
2. **Prioritized findings.** Compact table: ID, type, priority, confidence, affected surface, rule, short action. Detail material findings below.
3. **Claim cross-check.** The material listing claims and the app evidence that supports, contradicts, or leaves them unverified.
4. **Coverage and missing evidence.** Link detailed clause coverage; summarize tests completed, issue/risk counts, applicable clauses not verified, and defensible not-applicable decisions. Record the actual number reviewed, not simply the number of downloaded anchors.
5. **Fix and retest plan.** Concrete changes or evidence requests; provide proposed listing/review-note edits when helpful, conditional on verified app behavior. Do not rewrite the listing to conceal behavior or suggest a reviewer-only path.
6. **Provenance.** Evidence index, policy source manifest, retrieval failures/offline cache dates, test environment, and cleanup status. Clearly state that this is a mock review, not Apple's decision.

Each detailed finding should include:

```text
ID / title:
Type: Observed issue | Potential risk | Evidence gap | Recommendation
Priority / confidence:
Surface and evidence: exact listing field/locale, asset/frame, screenshot,
  plist key, log excerpt, or observed UI path; use absolute local links.
Reproduction: prerequisites, actions, observed result.
Applicable rule: verified clause ID, official URL, checked date, storefront
  and platform scope; explain any exception and why it does or does not apply.
Review concern: connect evidence to rule without claiming Apple's decision.
Fix: smallest concrete app, configuration, declaration, or listing change.
Retest: observable condition that would resolve the concern.
Open condition: missing evidence or alternate explanation, if any.
```

For evidence gaps or recommendations with no established rule violation, explicitly say so; do not invent a rule to populate the template. Never copy credentials into the report. A suggested reviewer message must be marked **Simulated reviewer note**, not represented as correspondence from Apple.

Detailed coverage columns:

```text
Clause or Connect requirement | Current source URL | Applicability + reason |
Status | Evidence/test IDs | Finding IDs | Limitation or next check
```

Statuses: **Issue**, **Risk**, **Checked**, **Not verified**, **Not applicable**. Give each numbered guideline a disposition and include applicable embedded subclauses. For grouped tests, retain traceability to each covered requirement. Download success, an existing manifest, or absence of a visible problem cannot by itself justify Checked.
