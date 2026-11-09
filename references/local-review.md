# Local binary and Simulator workflow

## Inventory without changing the app

Set `SKILL_DIR` to this installed skill directory and `REVIEW_DIR` to a new absolute output directory. Use project instructions if building from source; first inspect available schemes/targets without choosing a different product. Do not install dependencies, sign into Apple, alter entitlements, or upgrade the project just to make a review possible.

```sh
xcode-select -p
xcrun --find simctl
xcrun simctl list runtimes --json
xcrun simctl list devicetypes --json
xcrun simctl list devices available --json
python3 "$SKILL_DIR/scripts/inspect_binary.py" \
  --app "/absolute/path/MyApp.app" --out "$REVIEW_DIR/static.json"
```

The inspector also accepts `.ipa` and `.xcarchive`. It never launches, installs, signs, or uploads the app. It reports selected Info.plist metadata, nested-bundle metadata, privacy manifests, localized permission strings where readable, executable hash, platform/architecture tool output, and errors. It does not perform Apple's validation or inspect every API. IPA inspection reads selected members without extracting the archive into the workspace; it cannot validate the intact IPA's signature. Review signature/entitlements of an available intact bundle with local tools when needed.

Verify:

- Identity: bundle ID, display/version/build, executable hash, source archive hash if applicable, intended submission artifact, and any companion simulator build.
- Compatibility: Mach-O platform, host/runtime architecture, deployment target, supported device families, extensions and capabilities. `arm64` alone says nothing about simulator compatibility. Old binaries may lack `LC_BUILD_VERSION`; use legacy load commands plus platform metadata and mark ambiguous cases unverified.
- Relevant configuration: permission descriptions and localization, privacy manifests in app and dependencies, transport exceptions, background modes, URL handlers, encryption declaration, icon references, and entitlements. Check only signals relevant to actual app features.
- Do not treat a missing app-level privacy manifest as automatically disallowed; establish the applicable API/SDK requirement. Missing file names or strings do not establish absence of statically linked SDKs or behavior. Simulator signing is not distribution signing.

Device-only IPA or archive: complete static/listing review and request a simulator-targeted `.app` (or supplied source). Do not decrypt, re-sign, change platform flags, or repackage a device app to fake compatibility. TestFlight-installed and encrypted builds can limit static inspection; record that.

## Dedicated device

Choose an available runtime and compatible device type from the actual JSON results. Start with the primary supported phone; add a supported tablet, minimum OS, other locales, or additional platforms when their listing claims or risk justify testing. Unavailable runtimes and hardware-only features become coverage gaps.

```sh
REVIEW_SIM_UDID=$(xcrun simctl create "Pass Me Apple" "$DEVICE_TYPE_ID" "$RUNTIME_ID")
printf '%s\n' "$REVIEW_SIM_UDID" > "$REVIEW_DIR/owned-simulator-udid.txt"
xcrun simctl boot "$REVIEW_SIM_UDID"
xcrun simctl bootstatus "$REVIEW_SIM_UDID" -b
open -a Simulator --args -CurrentDeviceUDID "$REVIEW_SIM_UDID"
xcrun simctl install "$REVIEW_SIM_UDID" "$SIM_APP_PATH"
xcrun simctl launch "$REVIEW_SIM_UDID" "$BUNDLE_ID"
```

Check each command result before continuing; record the UDID immediately after successful creation. Run slow boot/build operations asynchronously through the execution tool so progress remains visible. Do not use `booted`, `erase all`, or delete pre-existing devices. Keep local output private and avoid putting passwords/tokens into commands or reports.

## Interact and collect evidence

Use available computer-use tools for the **Simulator** app and obey their documented APIs. Existing XCUITest or another already configured local driver is also appropriate. Discover actual controls from UI state before interacting. If no interaction mechanism is available, record that limitation; installation and launch are only smoke checks. Do not invent `simctl tap` or imply a screenshot proves a journey was completed.

```sh
xcrun simctl io "$REVIEW_SIM_UDID" screenshot "$REVIEW_DIR/01-first-launch.png"
```

Verify that the app has reached the intended visible state before treating a screenshot as evidence; a successful launch can return while the home screen or a system overlay is still displayed. Use unique evidence names per flow and state. Capture the entry route, actions, expected result, actual result, build/device/runtime, locale, account type (redacted), storefront assumptions, and timestamps. Use screenshots before and after the failure; retain relevant app logs or crash reports. Collect app-scoped diagnostics around reproduction, not unrelated host logs. Redact secrets and personal data before including excerpts in a shareable report.

Exercise appropriate paths:

1. Fresh install → first launch → onboarding → primary promised task. Observe placeholders, blocked content, unexpected web wrappers, or crashes.
2. Sign-up/login/logout, guest access where present, reviewer credentials, password recovery, error handling, and account deletion discovery/confirmation. Follow the current exception rules rather than assuming every login needs an Apple button.
3. Permissions at point of use: allow and deny, dismiss, relaunch; compare the actual prompt to binary purpose strings and listing declarations. Do not grant every permission in advance and then claim prompt behavior was tested.
4. Purchase/paywall: inspect products, displayed billing terms, eligibility, cancellation, restore, already-owned state, and sandbox failure paths. Identify real versus test purchasing before any transaction; geographic storefront behavior needs storefront evidence, not merely simulator language/region.
5. Claimed features, paid tiers, privacy/support links, reporting/blocking/moderation where applicable, and relevant device/locale variants. Compare actual screens to supplied screenshots and preview timestamps.
6. Recovery: app relaunch, background/foreground, empty/error states, and network failure when safely controllable per-app. Do not disconnect the host network as a shortcut. Accessibility labels require tests matching each claimed feature; a visual glance cannot verify VoiceOver.

Use a disposable test account for deletion or content mutation; otherwise inspect safely and mark the final action unverified. A local UI may write to a production backend. Simulated StoreKit success does not prove Connect products or production receipt validation; emulator behavior does not prove push, hardware, performance, payment provisioning, or App Store acceptance.

If a flow fails, reproduce once when practical and classify app behavior versus test environment failure. Do not keep retrying purchases, authentication, or destructive actions indefinitely. Keep unresolved access/hardware limitations visible rather than repairing or changing the app during a review.

## Finish

After evidence is saved, shut down and delete only the exact review-created UDID, unless the user wants it retained:

```sh
xcrun simctl shutdown "$REVIEW_SIM_UDID"
xcrun simctl delete "$REVIEW_SIM_UDID"
```

If a command fails, inspect its error; do not broaden the cleanup target. Preserve reports and evidence. Record simulator cleanup or retention in the report.
