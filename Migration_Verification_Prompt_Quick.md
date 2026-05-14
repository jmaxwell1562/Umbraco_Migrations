# Migration Verification Prompt (Quick Run)

## Dashboard Status

The audit dashboard should be built or refreshed automatically before running or triaging the audit.

Use this for a fast migration check with actionable output.

## Inputs
- Site name: [SITE_NAME]
- Source URL: [SOURCE_URL]
- Test URL: [TEST_URL]
- Run mode (optional): [RUN_MODE] = quick | full (default quick)
- Test scope (optional): [TEST_SCOPE] = single | instance | ask
- Test allowlist (optional): [TEST_ALLOWLIST]
- Test allowlist file (optional): [TEST_ALLOWLIST_FILE]
- Existing report folder (optional): [REPORT_FOLDER_IF_ALREADY_RUN]

## Instructions
1. Build/refresh dashboard first. Must include:
   - Auto-restore missing dashboard files on startup
   - WSU styling and logo
   - WSU Traffic Cop / MarCom-inspired shell where practical
   - WSU header-unit / logo-lockup pattern with cougar head logo in the top-left
   - Preserve provided WSU SVG/logo markup when available instead of replacing it with a placeholder badge
   - Full-width audit configuration panel
   - Source URL input
   - Test URL dropdown with predefined environments including https://localhost:7019/
   - Test URL dropdown must support localhost runs
   - Localhost audits require a local app to be running on port 7019
   - Generated Reports section below configuration
   - Generated Reports must render as two columns in a single row on desktop
   - Use the exact section names shown in the UI: New Report and Previous Report
   - Previous Report should occupy about 33% width on desktop, with New Report taking the remaining width
   - New Report link (primary view) appears only after the new report is complete
   - Previous Report shows the prior report for the same site with brief improvement-vs-previous stats
   - Route-based report links (for example /reports/<filename>), not file:// links
   - Report history lookup must tolerate spaces, underscores, hyphens, and case differences between the Site Name input and saved report filenames
   - Keep post-run links hidden until run completion/report history exists
   - Show only the latest audit for the current site in the form
   - Changing or blurring the Site Name field should refresh the latest available report for that same site without requiring a rerun
   - Do not render a Recent Sites section
   - Start Audit button behaves as a status button: Ready, Running, Complete, Error
   - Preflight-stopped audits must surface an error instead of implying stale results are new
   - Frontend asset refresh should not be blocked by stale JS/CSS cache
   - Keep an offline backup checklist that names the exact files and folders to zip
   - Keep a one-command bootstrap script for clean-machine setup using a virtual environment
2. Verify dashboard behavior:
   - Route loads
   - Form launches audit
   - The page does not auto-load a different site's audit on page load
   - Top-left WSU logo/header lockup renders correctly
   - Test URL dropdown includes the predefined environments and accepts localhost
   - Localhost browser checks ignore local HTTPS certificate errors while still requiring the localhost app to be reachable
   - New Report and Previous Report render from history
   - Existing reports for the current site can be reloaded even when report filenames use underscores or other separators
   - Generated Reports uses a single-row two-column layout on desktop and stacks on mobile
   - If no report folder or report artifacts are generated, the dashboard returns an error instead of reusing stale results
   - Fix On Test Site list shows only top 10 priority items
   - Summary counts, release readiness, and Queue B are not shown in the dashboard page
3. If [REPORT_FOLDER_IF_ALREADY_RUN] exists, triage from it (skip full rerun).
4. Else run audit.py with inputs.
5. If [RUN_MODE]=full, omit --max_paths. Otherwise pass --max_paths 80.
6. Pass optional flags when set:
   - --test_scope
   - --test_allowlist
   - --test_allowlist_file
7. Locate latest outputs:
   - Main CSV
   - Release readiness CSV
   - Accessible HTML audit report (primary viewable)
   - Executive HTML (secondary)
   - XLSX workbook
8. Triage only FAIL and REVIEW rows.
9. Treat REDIRECT rows as already classified and exclude from top fix priority.
10. Return two queues:
   - Queue A: Fix on test site
   - Queue B: Source/shared issues, APIs, or redirects
11. Prioritize FAIL first, then REVIEW by lowest score.
12. Include summary counts:
   - PASS, SOFT PASS, REVIEW, FAIL, REDIRECT
   - GO, CONDITIONAL GO, NO GO

## Output Format
- Dashboard update summary (updated files + confirmed UI elements including Test URL dropdown, New Report, and Previous Report + confirmed WSU logo/header lockup)
- Summary counts
- Readiness snapshot
- Queue A (numbered)
- Queue B (numbered)
- Next 3 actions

## Constraints
- Actually build or refresh the dashboard automatically before audit/triage; do not stop at describing the requirements.
- Keep Migration_Verification_Prompt.md, Migration_Verification_Prompt_Quick.md, and .github/copilot-instructions.md synchronized whenever the dashboard behavior changes.
- Keep README.md, BUS_FACTOR_HANDOFF.md, OFFLINE_BACKUP_CHECKLIST.md, and bootstrap-dashboard.ps1 aligned with the current setup and recovery workflow.
- Keep response concise.
- Do not pause for unnecessary confirmation.
- If commands run long, use async/no short timeout.
- For whole-site audits, do not constrain to section-only paths when [TEST_URL] includes a section path; use host-root joining unless the test path matches the source site slug.
- Main CSV detail columns: path, source_url, test_url, score, status, note, root_cause.
- Section grouping is shown as subheads in HTML/XLSX detail views.
