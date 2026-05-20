# Migration Verification Prompt

## Dashboard Status: BUILD OR REFRESH AUTOMATICALLY

Use this as a single end-to-end prompt: create or refresh the dashboard first, make it runnable, then run or triage the audit in the same pass.

## Expected Single-Prompt Result

Running this prompt once should leave you with all of the following, without requiring follow-up prompt engineering:

1. A runnable local dashboard URL.
2. A WSU-branded dashboard with the current production behavior, including:
   - Source URL textbox
   - Test URL dropdown with Custom URL support
   - Explicit subdomain-to-subpath control
   - Start Audit status button
   - Generated Reports area with `New Report` and `Previous Report`
3. Generated Reports links that expose:
   - HTML audit report
   - Executive preview HTML when present
   - Excel workbook as an openable link
   - No separate CSV button in the dashboard UI
4. Generated HTML reports that include:
   - Section Release Readiness
   - Detailed Rows
   - Clickable legend-pill filtering
5. User-friendly failure handling for common file-lock issues, including guidance to close or rename an open Excel workbook before rerunning the audit.

### Required Agent Behavior
1. If a runnable dashboard host does not exist, scaffold it in the workspace.
2. Install or restore required dependencies for the chosen dashboard host.
3. Start the dashboard locally and confirm the dashboard URL before running or triaging audits.
4. If the dashboard already exists, refresh it in place instead of creating duplicates.

See `.github/copilot-instructions.md` for full details.

---

Use this prompt to run and triage a WSU migration audit in this workspace.

## Goal
1. Build or refresh the audit dashboard automatically.
2. Run audit (or reuse existing report folder).
3. Return a prioritized migration action list.

## Inputs
- Site name: [SITE_NAME]
- Source URL: [SOURCE_URL]
- Test URL (required): [TEST_URL]
- Run mode (optional): [RUN_MODE]
   - quick: pass --max_paths 80 for fast validation
   - full: omit --max_paths for full-site coverage
- Test scope (optional): [TEST_SCOPE]
  - Allowed: single, instance, ask
- Test allowlist (optional): [TEST_ALLOWLIST]
  - Comma-separated labels or full URLs
- Test allowlist file (optional): [TEST_ALLOWLIST_FILE]
  - One label or URL per line, supports blank lines and # comments
- Batch site mappings file (optional): [BATCH_SITE_MAPPINGS_FILE]
   - External file with one site per line using: Site Name | Source URL | Test Path or Full Test URL
   - Use this for U17-style instance batches when multiple sibling sites should run in one pass as separate audits
   - The dashboard repo can ship a reusable example such as `batch-site-mappings.example.txt`; users should maintain their own editable copy outside the form
- Report folder hint (optional): [REPORT_FOLDER_IF_ALREADY_RUN]

## Required Execution Order

### Step 1: Build/refresh dashboard first
Ensure dashboard is usable immediately and crash-safe:

0. Host and startup
   - One prompt must be enough to create or refresh the dashboard and then use it
   - If no runnable dashboard host exists, scaffold the smallest supported host in the current workspace
   - Register required services and routes so the dashboard is reachable by URL
   - Restore or install dependencies required by the dashboard implementation
   - Start the dashboard locally and report the working URL
   - If the workspace already has a runnable dashboard host, update it in place instead of creating a parallel app

1. Branding and style
   - WSU color palette
   - WSU logo in header/brand area
   - Match the WSU Traffic Cop / MarCom visual direction where practical
   - When a target WSU unit site is supplied for visual direction (for example studentaffairs.wsu.edu), align the dashboard shell and header treatment to that site while keeping dashboard behavior intact
   - Keep the branded hero focused on dashboard function; do not add extra marketing or promo-card sections unless explicitly requested
   - Use the WSU header-unit / logo-lockup pattern with cougar head logo in the top-left
   - Preserve the provided WSU SVG/logo markup when available instead of replacing it with a placeholder badge

2. Required controls
   - Audit configuration panel spans full content width
   - Source URL textbox
   - Test URL dropdown with these environments: https://wdev3-testing.asis.wsu.edu/, http://asis-wdev1.ad.wsu.edu/, w2-testing.asis.wsu.edu, w3-testing.asis.wsu.edu, stepone.wsu.edu, dev.cub.wsu.edu, https://u7.dev.urec.wsu.edu/, https://localhost:7019/
   - Test URL dropdown includes a Custom URL option for environments outside the preset list
   - Explicit subdomain question/control: ask whether the source site is a subdomain that should stay rooted under the test URL path
   - When the subdomain control is enabled, preserve the test URL path prefix for all audited pages (for example source subdomain to dev.studentaffairs.wsu.edu/chs)
   - Test URL dropdown must support running against localhost
   - Localhost audits require a local app to be running and listening on port 7019
   - Site name input
   - Optional scope and max paths controls
   - Batch Site Mappings File input for one-click multi-site instance runs
   - Do not require users to build or maintain the batch list in the form; use the external mappings file as the source of truth
   - When a Batch Site Mappings File is supplied, run each listed site as a separate audit in one pass and surface per-site report links instead of comparing one source site against sibling test paths

3. Post-run links
   - Generated Reports section appears below the audit configuration panel
   - Generated Reports must render as two columns in a single row on desktop
   - Use the exact section names shown in the UI: New Report and Previous Report
   - Previous Report should occupy about 33% width on desktop, with New Report taking the remaining width
   - New Report shows the latest generated HTML audit report for the selected site (primary viewable report)
   - New Report also exposes the executive preview link when the executive HTML artifact exists for that run
   - New Report also exposes an Excel workbook link that users can open directly; do not require a separate CSV button in the dashboard UI
   - If a report file is locked by Excel or another app, show a plain-English message telling the user to close or rename the open workbook before rerunning the audit
   - Only show the New Report link after that report has completed
   - Previous Report shows the prior HTML audit report for the same site and exposes the prior executive preview when available
   - Previous Report includes a link plus brief improvement-vs-previous stats
   - Published report files in reports/ must preserve per-run timestamps so multiple runs on the same day remain available as latest and previous history
   - Links must be clickable from the dashboard via app routes (for example /reports/<filename>), not local-only file:// links
   - Report history lookup must tolerate spaces, underscores, hyphens, and case differences between the Site Name input and saved report filenames
   - Keep post-run links hidden until a run is complete and report history exists for the selected site
   - Show only the latest audit results for the site currently being run or selected in the form
   - When the Site Name field changes or loses focus, the dashboard should refresh the latest available report for that same site without requiring a rerun
   - Do not show a Recent Sites browsing section on the page
   - Generated HTML audit reports should treat the status/readiness legend pills as clickable filters for the report tables
   - Generated HTML audit reports must include a Section Release Readiness table and a Detailed Rows table that preserve section-based triage

4. Run button behavior
   - Start Audit button must behave as a status button (Ready, Running, Complete, Error)
   - Show running indicator while audit is in progress
   - Show a short notice that quick runs usually finish in a few minutes and full-site runs can take 10 to 30+ minutes before reports appear
   - Return to Ready after completion/failure state is shown
   - Full-site dashboard runs must allow substantially longer than the old 10-minute limit so long audits are not aborted mid-run by the Flask wrapper
   - If audit preflight stops before report generation, show an error state and do not imply stale previous results are new output
   - Treat a run as successful only when fresh HTML, CSV, and XLSX artifacts were generated and published for the selected site
   - Full and quick audits must use sitemap-backed path discovery when a sitemap is available, including non-default sitemap endpoints such as /sitemap, with source-link crawling as fallback instead of auditing only the root path

5. Recovery behavior
   - Update existing dashboard files in place (no duplicates)
   - If files are missing after crash, auto-restore on startup and continue
   - Avoid stale frontend assets after dashboard updates; ensure refreshed pages pick up the newest JS/CSS automatically
   - Disable caching for the dashboard page and report-history refresh calls so site changes show fresh state immediately
   - When dashboard behavior, layout, controls, or labels change, update this prompt, the quick prompt, and .github/copilot-instructions.md in the same pass
   - Keep an offline backup checklist file that names the exact files and folders to zip
   - Keep a one-command bootstrap script for clean-machine setup using a virtual environment and full dependency installation

6. Verification
   - Dashboard route loads
   - Form submission launches audit
   - Run button visibly changes state during lifecycle
   - The UI shows a short duration notice for quick vs full runs
   - New Report and Previous Report render from history in the Generated Reports section
   - Generated HTML audit reports support clickable legend-pill filtering for detail and readiness rows
   - Last completed run metadata includes the run time, not just the date
   - Generated Reports uses a single-row two-column layout on desktop, with a 33% Previous Report column, and stacks cleanly on mobile
   - The page shows the latest audit only for the current site and does not auto-load a different site on page load
   - Existing reports for the current site can be reloaded from the Site Name field even when the report filenames use underscores or other separators
   - Top-left WSU logo/header lockup renders correctly
   - Test URL dropdown includes the predefined environments, supports a Custom URL option, and successfully accepts localhost selections
   - Localhost browser checks ignore local HTTPS certificate errors while still requiring the localhost app to be reachable
   - If no report folder or report artifacts are generated, the dashboard returns an error instead of reusing stale results
   - Full-site audits are not cut off by the previous 10-minute dashboard timeout when they are still producing output
   - Full-site runs do not collapse to a single root-path audit when the source site exposes sitemap or crawlable internal links
   - Fix On Test Site section shows only the top 10 priority items
   - Summary counts, release readiness, and Queue B are not shown on the dashboard page

### Step 2: Run audit with provided values
1. If [REPORT_FOLDER_IF_ALREADY_RUN] is provided, skip full rerun and triage from that folder.
2. Else run audit.py with provided values.
3. If [RUN_MODE]=quick, pass --max_paths 80. If [RUN_MODE]=full (or omitted), do not pass --max_paths.
4. If [TEST_SCOPE] is set, pass --test_scope.
5. If [TEST_ALLOWLIST] is set, pass --test_allowlist.
6. If [TEST_ALLOWLIST_FILE] is set, pass --test_allowlist_file.
7. If preflight target validation blocks execution and report folder is available, continue triage from that folder.

### Step 3: Collect outputs and triage
Identify the generated folder and these outputs:
- Main CSV: [SITE_NAME]_audit_report_[YYYYMMDD].csv
- Cluster CSV: [SITE_NAME]_failure_clusters_[YYYYMMDD].csv
- Readiness CSV: [SITE_NAME]_release_readiness_[YYYYMMDD].csv
- Accessible HTML audit report (primary viewable): [SITE_NAME]_audit_report_[YYYYMMDD].html
- Executive HTML (secondary): [SITE_NAME]_executive_view_[YYYYMMDD].html
- XLSX: [SITE_NAME]_audit_report_[YYYYMMDD].xlsx

Triage rules:
1. Use dated main CSV as primary report.
2. Extract FAIL and REVIEW rows.
3. Treat REDIRECT as already-classified redirect outcome and exclude from primary fix priority.
4. Return two queues:
   - Queue A: Fix on test site (migration gaps)
   - Queue B: Source/shared instability, APIs, or redirect handling
5. Priority order:
   - FAIL before REVIEW
   - Within REVIEW, lowest similarity score first
6. Include summary counts:
   - PASS, SOFT PASS, REVIEW, FAIL, REDIRECT
7. Include readiness highlights:
   - GO, CONDITIONAL GO, NO GO counts
   - NO GO sections with blocker reasons
   - Section readiness rows with columns: section, test_site, total_pages, blocker_count, non_blocker_count, systemic_cluster_count, readiness_score, readiness_label, go_no_go, summary_reason
8. Save useful intermediate files (for example redirect classification CSV) and return full paths.

## Final Output Format (exact order)
1. Dashboard URL
   - Working local dashboard URL
2. Dashboard update summary
   - Files created or updated
   - Confirmed UI elements: source textbox, Test URL dropdown, New Report section, Previous Report section
   - Confirmed branding elements: WSU top-left logo/header lockup and Traffic Cop-inspired shell
3. Summary counts
4. Dated primary report path
5. Release readiness summary
6. NO GO sections
7. Queue A list
8. Queue B list
9. Recommended next 3 actions

The prompt is successful only if one run produces that result surface directly, rather than requiring a second prompt to restore missing controls, links, report sections, or user guidance.

## Rules
- On prompt execution, do not stop after describing the dashboard requirements; actually build or refresh the dashboard automatically before running or triaging the audit.
- On prompt execution, the dashboard must end in a runnable state with a confirmed local URL unless the environment is genuinely blocked.
- Keep Migration_Verification_Prompt.md, Migration_Verification_Prompt_Quick.md, and .github/copilot-instructions.md synchronized with the current dashboard behavior.
- If command stalls, rerun async or without short timeout.
- Do not ask for unnecessary confirmations between steps.
- Keep output concise and actionable.
- Always include dated report filenames with full paths.
- Do not ask user for [YYYYMMDD]; use generated filenames.
- For whole-site audits, do not constrain to a section path when [TEST_URL] includes a section-like path (for example /about-urec); normalize to host-root path joining unless the path matches the source site slug.
- If the source is a subdomain that migrated under a test-site path, ask and preserve that test URL path prefix instead of normalizing to host root.
- Main CSV detail columns: path, source_url, test_url, score, status, note, root_cause.
- Section grouping is in HTML/XLSX subheads; not a main CSV detail column.

## Reuse
Change only placeholders between sites:
[SITE_NAME], [SOURCE_URL], [TEST_URL], optional [RUN_MODE], [TEST_SCOPE], [TEST_ALLOWLIST], [TEST_ALLOWLIST_FILE], [BATCH_SITE_MAPPINGS_FILE], [REPORT_FOLDER_IF_ALREADY_RUN].
