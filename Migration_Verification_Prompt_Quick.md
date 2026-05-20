# Migration Verification Prompt (Quick Run)

## Dashboard Status

The audit dashboard should be built or refreshed automatically, made runnable, and started locally before running or triaging the audit.

Use this for a fast migration check with actionable output.

## Expected Single-Prompt Result

One run of this prompt should produce a runnable dashboard with the current UI behavior already in place: Custom Test URL support, explicit subdomain-to-subpath control, `New Report` and `Previous Report`, HTML plus executive preview links, an openable Excel workbook link, no separate CSV button, section-based HTML report output, and a user-friendly message when an open Excel workbook locks a report file.

## Inputs
- Site name: [SITE_NAME]
- Source URL: [SOURCE_URL]
- Test URL: [TEST_URL]
- Run mode (optional): [RUN_MODE] = quick | full (default quick)
- Test scope (optional): [TEST_SCOPE] = single | instance | ask
- Test allowlist (optional): [TEST_ALLOWLIST]
- Test allowlist file (optional): [TEST_ALLOWLIST_FILE]
- Batch site mappings file (optional): [BATCH_SITE_MAPPINGS_FILE]
   - Use an external mappings file as the reusable source of truth instead of maintaining the batch list in the form
- Existing report folder (optional): [REPORT_FOLDER_IF_ALREADY_RUN]

## Instructions
1. Build/refresh dashboard first. Must include:
   - One prompt must be enough to scaffold or refresh the dashboard and then use it
   - If no runnable dashboard host exists, scaffold the smallest supported host in the current workspace
   - Restore or install required dependencies for that host
   - Start the dashboard locally and confirm the working URL
   - If a runnable dashboard already exists, update it in place instead of creating a duplicate app
   - Auto-restore missing dashboard files on startup
   - WSU styling and logo
   - WSU Traffic Cop / MarCom-inspired shell where practical
   - When a target WSU unit site is supplied for visual direction (for example studentaffairs.wsu.edu), align the shell and header treatment to that site while keeping dashboard behavior intact
   - Keep the hero focused on dashboard function; do not add extra marketing or promo-card sections unless explicitly requested
   - WSU header-unit / logo-lockup pattern with cougar head logo in the top-left
   - Preserve provided WSU SVG/logo markup when available instead of replacing it with a placeholder badge
   - Full-width audit configuration panel
   - Source URL input
   - Test URL dropdown with predefined environments including https://localhost:7019/
   - Test URL dropdown includes a Custom URL option for environments outside the preset list
   - Explicit subdomain question/control for cases where the source site is a subdomain but the test site is rooted under a path such as /chs
   - When enabled, preserve the test URL path prefix for all audited pages instead of dropping to host root
   - Test URL dropdown must support localhost runs
   - Localhost audits require a local app to be running on port 7019
   - Generated Reports section below configuration
   - Batch Site Mappings File input for U17-style one-pass multi-site runs
   - Do not require users to build or maintain the batch list in the form
   - Generated Reports must render as two columns in a single row on desktop
   - Use the exact section names shown in the UI: New Report and Previous Report
   - Previous Report should occupy about 33% width on desktop, with New Report taking the remaining width
   - New Report link (primary view) appears only after the new report is complete
   - New Report also exposes the executive preview link when the executive HTML artifact exists for that run
   - New Report also exposes an Excel workbook link that users can open directly; omit a separate CSV button from the dashboard UI
   - If a workbook is open and locks a report file, the dashboard should show a plain-English message telling the user to close or rename the open Excel file before rerunning the audit
   - Previous Report shows the prior report for the same site with brief improvement-vs-previous stats and exposes the prior executive preview when available
   - Published report files in reports/ must preserve per-run timestamps so multiple runs on the same day remain available as latest and previous history
   - Route-based report links (for example /reports/<filename>), not file:// links
   - Report history lookup must tolerate spaces, underscores, hyphens, and case differences between the Site Name input and saved report filenames
   - Keep post-run links hidden until run completion/report history exists
   - Show only the latest audit for the current site in the form
   - Changing or blurring the Site Name field should refresh the latest available report for that same site without requiring a rerun
   - Do not render a Recent Sites section
   - Generated HTML audit reports should treat the status/readiness legend pills as clickable filters for the report tables
   - Generated HTML audit reports must include a Section Release Readiness table and a Detailed Rows table that preserve section-based triage
   - When a Batch Site Mappings File is supplied, run each listed site as a separate audit in one pass and return per-site report links instead of treating sibling test paths as alternate targets for the same source site
   - Start Audit button behaves as a status button: Ready, Running, Complete, Error
   - Show a short notice that quick runs usually finish in a few minutes and full-site runs can take 10 to 30+ minutes before reports appear
   - Full-site dashboard runs must allow substantially longer than the old 10-minute limit so long audits are not aborted mid-run by the Flask wrapper
   - Preflight-stopped audits must surface an error instead of implying stale results are new
   - Treat a run as successful only when fresh HTML, CSV, and XLSX artifacts were generated and published for the selected site
   - Audits must use sitemap-backed path discovery when a sitemap is available, including non-default sitemap endpoints such as /sitemap, with source-link crawling as fallback instead of only auditing the root path
   - Frontend asset refresh should not be blocked by stale JS/CSS cache
   - Disable caching for dashboard and report-history refresh responses so site changes show current state immediately
   - Keep an offline backup checklist that names the exact files and folders to zip
   - Keep a one-command bootstrap script for clean-machine setup using a virtual environment
2. Verify dashboard behavior:
   - Route loads
   - Form launches audit
   - The UI shows a short duration notice for quick vs full runs
   - The page does not auto-load a different site's audit on page load
   - Top-left WSU logo/header lockup renders correctly
   - Test URL dropdown includes the predefined environments, accepts localhost, and supports a Custom URL option
   - Localhost browser checks ignore local HTTPS certificate errors while still requiring the localhost app to be reachable
   - New Report and Previous Report render from history
   - Generated HTML audit reports support clickable legend-pill filtering for detail and readiness rows
   - Last completed run metadata includes the run time, not just the date
   - Existing reports for the current site can be reloaded even when report filenames use underscores or other separators
   - Generated Reports uses a single-row two-column layout on desktop and stacks on mobile
   - If no report folder or report artifacts are generated, the dashboard returns an error instead of reusing stale results
   - Full-site audits are not cut off by the previous 10-minute dashboard timeout when they are still producing output
   - Full and quick runs do not collapse to a single root-path audit when the source site exposes sitemap or crawlable internal links
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
   - Release readiness CSV should contain section rows with columns: section, test_site, total_pages, blocker_count, non_blocker_count, systemic_cluster_count, readiness_score, readiness_label, go_no_go, summary_reason
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
- Dashboard URL (working local dashboard URL)
- Dashboard update summary (updated files + confirmed UI elements including Test URL dropdown, New Report, and Previous Report + confirmed WSU logo/header lockup)
- Summary counts
- Readiness snapshot
- Queue A (numbered)
- Queue B (numbered)
- Next 3 actions

## Constraints
- Actually build or refresh the dashboard automatically before audit/triage; do not stop at describing the requirements.
- End with a runnable local dashboard URL unless the environment is genuinely blocked.
- Keep Migration_Verification_Prompt.md, Migration_Verification_Prompt_Quick.md, and .github/copilot-instructions.md synchronized whenever the dashboard behavior changes.
- Keep README.md, BUS_FACTOR_HANDOFF.md, OFFLINE_BACKUP_CHECKLIST.md, and bootstrap-dashboard.ps1 aligned with the current setup and recovery workflow.
- Keep response concise.
- Do not pause for unnecessary confirmation.
- If commands run long, use async/no short timeout.
- For whole-site audits, do not constrain to section-only paths when [TEST_URL] includes a section path; use host-root joining unless the test path matches the source site slug.
- Main CSV detail columns: path, source_url, test_url, score, status, note, root_cause.
- Section grouping is shown as subheads in HTML/XLSX detail views.
