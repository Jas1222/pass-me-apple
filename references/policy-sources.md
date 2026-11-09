# Policy sources and freshness

The canonical policy is [Apple's complete App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/). The registry in [apple-sources.json](apple-sources.json) includes that document, listing specifications, privacy and age-rating references, submission help, and conditional supporting documents. URLs were seeded on 2026-11-09; that date is **not** a policy verification date for a later review.

## Retrieval

Run from any directory, using the installed skill's actual path:

```sh
python3 "$SKILL_DIR/scripts/collect_sources.py" --out "$REVIEW_DIR/policy"
```

This fetches the full guidelines and all `core` sources, writing HTML/text snapshots, links, a manifest with SHA-256 and UTC retrieval timestamps, and an unreviewed clause inventory. The helpers require Python 3.9 or newer; source retrieval also requires curl and preserves TLS verification. A nonzero exit means one or more selected sources were not verified; inspect `manifest.json` and repair the relevant gap using browsing rather than treating a partial download as current policy.

Select additional registered sources by ID, repeatably, or fetch the complete registry:

```sh
python3 "$SKILL_DIR/scripts/collect_sources.py" --out "$REVIEW_DIR/policy-extra" --include account-deletion --include subscriptions
python3 "$SKILL_DIR/scripts/collect_sources.py" --out "$REVIEW_DIR/policy-all" --all
```

Use a fresh output directory for each fetch. `--all` means all **registered sources**, not every document on Apple's website. The complete guideline document is always selected. The helper extracts visible HTML; JavaScript-only documentation, login pages, unusual markup, or missing clause anchors require manual/browser verification. Inspect the body and source links, not just the successful HTTP status.

## Select supporting rules

| Context | Sources and follow-up |
|---|---|
| Every submission | Full guidelines; upcoming requirements; app information; platform version information; required/localizable properties; screenshot/preview/creative-asset specs; age ratings; app privacy; submission overview |
| Permissions, analytics, ads, AI providers, or embedded SDKs | Privacy details, tracking guidance, SDK requirements; follow the linked current privacy manifest and required-reason API documentation |
| Account creation or login | Account deletion support; exact current login guideline and its exceptions; relevant authentication developer documentation |
| Purchases or subscriptions | Subscription and IAP references; follow current guideline links for storefront-specific purchase methods, entitlement agreements, and eligibility |
| Accessibility claims | Accessibility label overview and the linked criteria for every claimed feature/platform |
| Encryption, regulated services, children, UGC/AI, gaming, financial/medical claims | Exact corresponding guideline clauses; current linked Apple support, entitlement, declaration, and documentation requirements |
| EU/other regional distribution | Region-specific support from the guideline/support pages; trader and other applicable submission declarations; do not infer legal eligibility from Simulator |
| Custom product pages, In-App Events, App Clips, extensions, other platforms | Follow official links from the full guideline and Connect help to the feature's submission reference |

Use the current page hierarchy and links if Apple moves an endpoint. Additional sources belong in the review's provenance manifest with title, canonical URL, retrieval time, effective date if stated, and the finding/check they support. Do not change the installed registry during an ordinary review just to save per-app evidence.

## Coverage and interpretation

Read the full guideline, including its introduction, submission prerequisites, five chapters, embedded lists, footnotes, regional exceptions, and linked requirements relevant to the app. Keep an entry for each numbered clause in `guideline-coverage-seed.json`; add rows for requirements without their own anchors. Start with all entries unreviewed. Explicitly classify applicability before selecting tests. Aggregate rows in a reader-facing summary only if the detailed coverage retains their individual dispositions.

Read Connect reference tables to obtain current field constraints and media specifications; do not freeze character limits, image dimensions, age bands, SDK deadlines, or storefront payment rules into this skill. Count the submitted fields using the documented unit; do not assume bytes, Unicode code points, and displayed characters are interchangeable.

Rule text and observed behavior are separate evidence. A source hash records the bytes retrieved; it does not show that every rule was evaluated. Check updated pages for new clauses, changed exceptions, and future effective dates. Distinguish binding submission requirements from design/marketing advice. Prefer the more specific applicable current Apple documentation, explain any unresolved conflict, and avoid asserting that a general UX suggestion is mandatory.
