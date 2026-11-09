# Pass Me Apple

A Codex skill for a local mock Apple App Store review. Review an app binary or source build in Simulator together with its proposed store listing, using freshly retrieved Apple guidelines.

## What you get

- A local HTML dashboard with findings, evidence links, and searchable guideline coverage.
- A Markdown report and CSV coverage table.
- Prioritized submission risks, concrete fixes, and explicit unverified areas.
- An independent slate-and-teal dashboard palette.

## Install

Clone this repository into your Codex skills directory:

```sh
git clone https://github.com/Jas1222/pass-me-apple.git ~/.codex/skills/pass-me-apple
```

If that directory already exists, update the existing installation rather than cloning over it. Restart or reload Codex if needed to discover the skill.

## Use

Invoke `$pass-me-apple` and provide your local app project/binary and store listing materials. See [SKILL.md](SKILL.md) for the complete workflow and [submission template](assets/submission-template.md) for optional intake.

Local iOS execution requires macOS, Xcode and a compatible installed Simulator runtime. Helpers use Python 3.9+ and curl; native UI interaction requires available automation. Unsupported builds or unavailable interactions are reported as evidence gaps.

The dashboard opens directly from disk without a server or external assets. Keep the review folder together so evidence links work.

This is a mock review, not Apple approval or certification. App inspection artifacts remain local; current public Apple policy pages are fetched over HTTPS. The workflow does not submit an app or make real purchases.
