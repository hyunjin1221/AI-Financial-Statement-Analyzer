# CODEX.md - Project Working Rules

## Core Rules
- Keep this project free-only: SEC public data + open-source Python + local Ollama.
- Always comply with SEC fair-access practices (explicit User-Agent and reasonable request pacing).
- After every correction, end with: "Update your CODEX.md so you don't make that mistake again."
- Ruthlessly refine this file when mistakes happen so error rate drops over time.

## Notes Workflow
- Maintain `notes/PROJECT_NOTES.md` as the running implementation log.
- After each substantial coding pass, add:
  - What was built
  - What changed
  - Risks / follow-ups
  - Any mistakes and the new rule added

## Engineering Quality
- Keep modules small and testable.
- Prefer deterministic outputs and explicit schemas.
- Add tests for parsing and ratio calculations before expanding scope.

## Mistake Prevention Updates
- Do not set a fixed `Host` header globally in the SEC HTTP session; endpoints span multiple hosts (`data.sec.gov`, `www.sec.gov`, `sec.gov/files`).
- Keep parser extraction thresholds tolerant enough for shorter but valid sections; enforce quality downstream instead of hard-dropping too early.
- Ensure local test config includes package import path (`pytest.ini` with `pythonpath = .`) before adding module-based tests.
- Before relying on unit tests, confirm pytest import path config exists (`pythonpath = .`) so package imports are stable.
- When mapping XBRL facts, always support concept fallbacks and select the latest value deterministically by `end` then `filed`.
- Ratio outputs must include a data-quality status (`ok`, `missing_data`, `unstable_denominator`) rather than only numeric values.
- Keep LLM-dependent features non-blocking in the UI: if Ollama/model is unavailable, show a clear warning and continue rendering all deterministic analytics.
- Enforce structured JSON normalization for LLM outputs before use; never trust raw model text directly.
- Unit-test deterministic LLM helper logic (parse/normalize/merge) without calling external model servers.
- Keep expensive network workflows behind explicit UI toggles (`run_peer`) and bounded scan sizes.
- Any generated narrative summary must include a non-advice disclaimer.
- Update README status and controls whenever a sprint feature is added to avoid stale run instructions.
- For Streamlit apps with repeated SEC lookups, route network calls through cached wrapper functions to keep reruns responsive.
- Any report-export feature must have a deterministic formatter function and a unit test for expected sections.
- Maintain at least one mocked end-to-end integration test for deterministic pipeline flow (no network/LLM dependency).
- Preserve parser source spans (`start`, `end`) and carry them into AI evidence mapping for traceable outputs.
- For peer benchmarking, use bounded thread pools to improve throughput while respecting existing SEC rate limiting.
- Any persisted artifact feature must support listing recent artifacts and must be covered by filesystem-based unit tests.
- Streamlit entrypoints executed from subdirectories must enforce project-root import path (or use a root-level launcher) so `from app...` imports stay stable.
