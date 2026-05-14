# WSU Migration Dashboard Handoff

This file is the recovery and replication guide for the WSU Migration Verification Dashboard workspace.

Use it when:
- a new developer needs to rebuild or run the dashboard
- the workspace must be recreated on another machine
- prompt files need to be kept aligned with the live dashboard
- someone needs enough context to continue this work without prior chat history

## What This Project Is

This workspace contains two connected parts:

1. A Flask dashboard for running audits and viewing results.
2. A Python audit runner that generates CSV, HTML, and XLSX migration reports.

The dashboard is the primary entry point. It collects audit inputs, launches `audit.py`, copies the resulting report artifacts into `reports/`, and serves HTML reports through app routes.

## Current Dashboard Behavior

The current UI is expected to behave as follows:

1. Full-width Audit Configuration panel.
2. Test URL is a dropdown, not a freeform text box.
3. Test URL dropdown options include localhost.
4. Generated Reports appears below the configuration panel.
5. Generated Reports uses two columns in a single row on desktop.
6. Section names are exactly `New Report` and `Previous Report`.
7. `Previous Report` is the narrower column, about 33% width.
8. `Previous Report` remains visible even if no prior report exists yet.
9. The page shows only `Fix On Test Site: Top 10 Priority` on the main result surface.
10. The page does not show summary counts, release readiness, or Queue B on the main dashboard.
11. The Start Audit button behaves as a status button: Ready, Running, Complete, Error.
12. The page stays focused on the current site in the form and does not show a Recent Sites browser.
13. Report history lookup is tolerant of spaces, underscores, hyphens, and case differences between the Site Name field and saved report filenames.
14. Changing or blurring the Site Name field refreshes the latest available report for that same site without requiring a rerun.
15. The UI includes a short duration note explaining that quick runs usually finish in a few minutes while full-site runs can take 10 to 30+ minutes before reports appear.
16. Generated HTML audit reports use clickable legend pills to filter readiness and detailed rows in place.
17. Published report files in `reports/` preserve per-run timestamps so multiple same-day runs remain available in site history.

## Critical Files

Application:
- `app.py`: Flask server, audit execution, report routes, API endpoints
- `utils.py`: report history and CSV parsing
- `config.py`: host, port, reports directory, audit script path
- `audit.py`: core migration audit runner

UI:
- `templates/dashboard.html`: dashboard markup
- `static/dashboard.js`: client behavior
- `static/style.css`: layout and styling

Prompt and instruction sources:
- `Migration_Verification_Prompt.md`
- `Migration_Verification_Prompt_Quick.md`
- `.github/copilot-instructions.md`
- `README.md`

Convenience:
- `start-dashboard.bat`: Windows setup and startup helper
- `bootstrap-dashboard.ps1`: one-command clean-machine bootstrap using a virtual environment
- `requirements.txt`: Python package manifest for both dashboard and audit runner
- `OFFLINE_BACKUP_CHECKLIST.md`: exact zip checklist for offline backup

## Non-Negotiable Sync Rule

When dashboard behavior, layout, controls, labels, report presentation, or setup requirements change, update these files in the same pass:

1. `README.md`
2. `Migration_Verification_Prompt.md`
3. `Migration_Verification_Prompt_Quick.md`
4. `.github/copilot-instructions.md`

Do not update the UI without updating the prompt and runtime docs.

## Full Replication Checklist

### 1. Machine Prerequisites

- Windows machine
- Python 3.10+ recommended
- Internet access for Python package installs and Playwright browser install
- Permission to run local Flask server on `127.0.0.1:5000`

### 2. Clone or Copy Workspace

Copy the entire project folder, including:
- source files
- prompt files
- `reports/`
- any `Audit_*` folders you want to preserve historically

If you only need the app and not historical output, the `Audit_*` folders are optional. The `reports/` directory is the important runtime surface for dashboard history.

### 3. Install Python Dependencies

Run:

```powershell
python -m pip install -r requirements.txt
```

This installs dashboard and audit dependencies, including:
- Flask
- Flask-Cors
- requests
- openpyxl
- playwright

### 4. Install Browser Runtime for Audit Execution

Run once on a new machine:

```powershell
python -m playwright install chromium
```

Without this step, the dashboard can load but `audit.py` will fail when trying to run browser-based checks.

### 5. Start the Dashboard

Option A:

```powershell
python app.py
```

Option B:

```powershell
start-dashboard.bat
```

Option C:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap-dashboard.ps1
```

Open:

```text
http://localhost:5000
```

### 6. Verify Startup

Confirm:
- the dashboard loads
- the WSU header renders
- Test URL is a dropdown
- localhost appears in the dropdown
- Generated Reports shows `New Report` and `Previous Report`

## Required Test URL Dropdown Options

The Test URL dropdown currently includes:

1. `https://wdev3-testing.asis.wsu.edu/`
2. `http://asis-wdev1.ad.wsu.edu/`
3. `w2-testing.asis.wsu.edu`
4. `w3-testing.asis.wsu.edu`
5. `stepone.wsu.edu`
6. `dev.cub.wsu.edu`
7. `https://u7.dev.urec.wsu.edu/`
8. `https://localhost:7019/`

The backend normalizes bare hosts into absolute URLs and accepts localhost runs.
For localhost audits to work, a local app must be running and listening on port `7019`.
The audit runner ignores local HTTPS certificate errors for localhost browser checks.

## How Audit Execution Works

1. The dashboard posts to `POST /api/audit/run`.
2. `app.py` launches `audit.py` with:
   - `--site`
   - `--source`
   - `--test_url`
   - optional `--max_paths 80` for quick mode
   - optional scope and allowlist flags
3. `audit.py` writes output into an `Audit_<SITE>_<TIMESTAMP>` folder.
4. `app.py` parses stdout for the generated folder.
5. `app.py` copies `.csv`, `.html`, and `.xlsx` artifacts from that folder into `reports/`.
6. The dashboard reads report history from `reports/` and matches site names tolerantly across spaces, underscores, hyphens, and case.
7. HTML reports are served through `/reports/<filename>`.
8. Full-site runs now have a longer dashboard-side wait window than the old 10-minute limit so they are less likely to be aborted mid-run.
9. Generated HTML audit reports include client-side legend filters for status, readiness, and release impact.
10. Published report artifacts in `reports/` include the run timestamp when available so latest and previous same-day runs can coexist.

## Report Files the Dashboard Expects

For each run, the dashboard expects these dated files when present:

- `{site}_audit_report_{YYYYMMDD}.csv`
- `{site}_failure_clusters_{YYYYMMDD}.csv`
- `{site}_release_readiness_{YYYYMMDD}.csv`
- `{site}_audit_report_{YYYYMMDD}.html`
- `{site}_executive_view_{YYYYMMDD}.html`
- `{site}_audit_report_{YYYYMMDD}.xlsx`

## Recovery After Crash or Machine Loss

If the environment is lost:

1. Restore the project folder.
2. Restore `reports/` if you want existing dashboard history.
3. Restore any important `Audit_*` folders if you want raw original run folders.
4. Run `python -m pip install -r requirements.txt`.
5. Run `python -m playwright install chromium`.
6. Run `python app.py`.
7. Open the dashboard and confirm the latest site loads.

If `reports/` is missing but `Audit_*` folders exist, reports can be recopied manually into `reports/`.

## Recommended Backup Surface

At minimum, back up:

1. `app.py`
2. `utils.py`
3. `config.py`
4. `audit.py`
5. `templates/dashboard.html`
6. `static/dashboard.js`
7. `static/style.css`
8. `Migration_Verification_Prompt.md`
9. `Migration_Verification_Prompt_Quick.md`
10. `.github/copilot-instructions.md`
11. `README.md`
12. `requirements.txt`
13. `start-dashboard.bat`
14. `bootstrap-dashboard.ps1`
15. `OFFLINE_BACKUP_CHECKLIST.md`
16. `reports/`

## Known Operational Notes

- `requirements.txt` must include audit dependencies, not just Flask dependencies.
- Playwright requires Chromium installation separately.
- The dashboard history view is driven by files copied into `reports/`, not only by the raw `Audit_*` folders.
- The dashboard can reload the latest report for the current site when the Site Name field changes or loses focus; it does not auto-load a different site's report on page load.
- Full-site runs can legitimately take 10 to 30+ minutes before final report artifacts appear.
- The previous report card may have a placeholder state if there is no earlier run yet.
- Route-based links are required for HTML reports; do not switch them to `file://` links.
- If an audit stops during preflight and produces no report folder or artifacts, the dashboard should surface an error rather than silently reusing stale data.

## Suggested Smoke Test on a New Machine

1. Start the dashboard.
2. Confirm the Test URL dropdown renders with localhost.
3. Submit an audit using an existing report folder to validate the request path without waiting for a long run.
4. Open the latest HTML report from `New Report`.
5. Confirm changing or blurring the Site Name field reloads the current site's report history without requiring a rerun.

## If Someone Else Has To Continue This Work

Tell them to read these files first, in order:

1. `BUS_FACTOR_HANDOFF.md`
2. `README.md`
3. `OFFLINE_BACKUP_CHECKLIST.md`
4. `Migration_Verification_Prompt.md`
5. `.github/copilot-instructions.md`
6. `app.py`
7. `templates/dashboard.html`
8. `static/dashboard.js`
9. `static/style.css`

That is enough context to continue safely.