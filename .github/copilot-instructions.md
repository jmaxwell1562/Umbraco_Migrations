# WSU Migration Verification Dashboard - Copilot Instructions

## Dashboard Status: BUILD OR REFRESH AUTOMATICALLY

The interactive audit dashboard should be created or refreshed automatically as part of the prompt workflow, then started locally before audit or triage work continues.

## Prompt Intent

One prompt should be enough to:
1. scaffold or refresh the dashboard,
2. make it runnable in the current workspace,
3. start it locally and return the working dashboard URL in the final output,
4. run or triage the audit results.

The expected single-prompt result is the current dashboard behavior, not a partial scaffold. That includes the explicit subdomain-to-subpath control, `New Report` and `Previous Report`, HTML and executive preview links, an openable Excel workbook link, no separate CSV button in the dashboard UI, section-based HTML report output, and a plain-English file-lock message when an Excel workbook is open.

## Dashboard Features

The dashboard provides:

1. **Form Controls**
   - Full-width audit configuration panel
   - Site Name input
   - Source URL textbox
   - Test URL dropdown (required)
   - Test URL dropdown options: https://wdev3-testing.asis.wsu.edu/, http://asis-wdev1.ad.wsu.edu/, w2-testing.asis.wsu.edu, w3-testing.asis.wsu.edu, stepone.wsu.edu, dev.cub.wsu.edu, https://u7.dev.urec.wsu.edu/, https://localhost:7019/
   - Test URL dropdown includes a Custom URL option for environments outside the preset list
   - Explicit subdomain question/control for source-subdomain to test-subpath migrations
   - When enabled, preserve the test URL path prefix for all audited pages instead of flattening to host root
   - Test URL dropdown must support localhost runs
   - Localhost audits require a local app to be listening on port 7019
   - Optional scope and max paths controls
   - Optional test allowlist textarea
   - Batch Site Mappings File input for one-pass multi-site instance audits
   - The external mappings file is the source of truth for multi-site batches; do not require users to maintain the list in the form
   - Reuse existing report folder option

2. **Interactive Results Display**
   - Live progress bar during audit execution
   - Start Audit button behaves as a status button: Ready, Running, Complete, Error
   - A short duration notice explains that quick runs usually finish in a few minutes while full-site runs can take 10 to 30+ minutes before reports appear
   - Preflight-stopped audits surface an error instead of implying stale results are new
   - A run is only successful when fresh HTML, CSV, and XLSX artifacts were generated and published for the selected site
   - Path discovery must use sitemap-backed discovery when available, including non-default sitemap endpoints such as /sitemap, with source-link crawling fallback instead of reducing audits to the root path only
   - Prioritized Queue A only, limited to top 10 fix-on-test priorities
   - Show only the latest audit for the current site in the form
   - When a Batch Site Mappings File is supplied, run each mapping as a separate audit in one pass and surface per-site report links instead of comparing one source site against sibling test paths

3. **Report Management**
   - Generated Reports section positioned below configuration
   - Generated Reports uses two columns in a single row on desktop
   - Use the exact UI section names: New Report and Previous Report
   - Previous Report occupies about 33% width on desktop, with New Report taking the remaining width
   - New Report shows the latest generated HTML audit report and only appears after the new report completes
   - New Report also exposes the executive preview link when the executive HTML artifact exists for that run
   - New Report also exposes an Excel workbook link that users can open directly; do not surface a separate CSV button in the dashboard UI
   - If a report file is locked by Excel or another app, the UI should tell the user to close or rename the open workbook before rerunning the audit
   - Previous Report shows the prior HTML audit report with brief improvement-vs-previous stats and exposes the prior executive preview when available
   - Route-based report links served from app routes such as `/reports/<filename>`
   - Report history lookup must tolerate spaces, underscores, hyphens, and case differences between the Site Name input and saved report filenames
   - Full report history per site
   - Published report files in `reports/` preserve per-run timestamps so same-day runs do not overwrite previous history
   - Changing or blurring the Site Name field refreshes the latest available report for that same site without requiring a rerun
   - Generated HTML audit reports use clickable legend pills as client-side filters for detail and readiness tables
   - Generated HTML audit reports must preserve section-based triage with a Section Release Readiness table and a Detailed Rows table
   - Last completed run metadata includes the run time, not just the date
   - Do not render a Recent Sites browsing section on the page
   - Post-run links hidden until complete
   - Automatic recovery after crash with file auto-restore

4. **WSU Branding**
   - WSU Crimson (#981E32) and Navy (#003C71) colors
   - WSU top-left cougar logo/header lockup
   - When the user points to a specific WSU unit site for visual direction, align the dashboard shell and header treatment to that site where practical
   - Keep the hero focused on dashboard function; avoid extra marketing or promo-card sections unless the user explicitly asks for them
   - WSU header-unit / logo-lockup pattern when provided
   - Traffic Cop / MarCom-inspired shell where practical
   - Preserve provided SVG/logo markup instead of replacing it with a placeholder badge

## File Structure

```
├── app.py                 # Flask backend
├── config.py              # Configuration
├── utils.py               # Report parsing utilities
├── audit.py               # Audit script (or external)
├── requirements.txt       # Python dependencies
├── templates/
│   └── dashboard.html     # Main UI
├── static/
│   ├── style.css          # Styling
│   └── dashboard.js       # Frontend logic
├── reports/               # Generated reports
└── README.md              # Full documentation
```

## API Endpoints

### Working Endpoints

- `GET /` - Dashboard home
- `GET /api/health` - Server health check
- `GET /api/sites` - List sites with history
- `POST /api/audit/run` - Run new audit
- `GET /api/reports/<site_name>` - Get latest report
- `GET /api/reports/<site_name>/<date>/queues` - Get Queue A & B
- `GET /api/readiness/<site_name>/<date>` - Get readiness summary

## Report Output Format

### Files Generated

Each audit generates:
- `{site}_audit_report_{YYYYMMDD}.csv` or `{site}_audit_report_{YYYYMMDD_HHMMSS}.csv` - Main results
- `{site}_failure_clusters_{YYYYMMDD}.csv` or `{site}_failure_clusters_{YYYYMMDD_HHMMSS}.csv` - Failure groupings
- `{site}_release_readiness_{YYYYMMDD}.csv` or `{site}_release_readiness_{YYYYMMDD_HHMMSS}.csv` - Readiness status
- `{site}_audit_report_{YYYYMMDD}.html` or `{site}_audit_report_{YYYYMMDD_HHMMSS}.html` - Interactive HTML report
- `{site}_executive_view_{YYYYMMDD}.html` or `{site}_executive_view_{YYYYMMDD_HHMMSS}.html` - Executive summary
- `{site}_audit_report_{YYYYMMDD}.xlsx` or `{site}_audit_report_{YYYYMMDD_HHMMSS}.xlsx` - Excel export

### Triage Logic

**Queue A: Fix on Test Site (Migration Gaps)**
- Root causes: migration, mapping, redirect, URL issues
- Sorted: FAIL first, then REVIEW by lowest score
- Action: Direct fix on test environment

**Queue B: Source/Shared Instability**
- Root causes: API issues, source system, shared services
- Action: Coordinate with source team

**Readiness Flags**
- GO: Section ready for release
- CONDITIONAL GO: Ready with conditions
- NO GO: Blockers prevent release
- Release readiness CSV rows use: section, test_site, total_pages, blocker_count, non_blocker_count, systemic_cluster_count, readiness_score, readiness_label, go_no_go, summary_reason

## Configuration

Edit `config.py` to customize:

```python
DEBUG = True              # Development mode
HOST = '127.0.0.1'       # Server host
PORT = 5000              # Server port
REPORTS_DIR = '...'      # Report storage location
AUDIT_SCRIPT = '...'     # Audit script path

# WSU Branding
WSU_PRIMARY_COLOR = '#981E32'
WSU_SECONDARY_COLOR = '#003C71'
WSU_ACCENT_COLOR = '#D4AF37'
```

## Execution Instructions

### For Users Running Audits

1. Open dashboard at `http://localhost:5000`
2. Fill in required fields (Site Name, Test URL)
3. Optionally fill Source URL, Run Mode, Scope
4. Click "Start Audit"
5. Monitor progress bar
6. View generated reports and queues
7. Follow recommended actions

### For Agents Refreshing the Dashboard

1. Actually build or refresh the dashboard automatically before audit or triage work; do not stop at describing requirements.
2. If no runnable dashboard host exists, scaffold the smallest supported host in the current workspace and make it reachable by a local URL.
3. Restore or install required dependencies, build the dashboard host, and start it locally before continuing.
4. Update existing dashboard files in place instead of creating duplicate variants.
5. When dashboard behavior, layout, controls, labels, startup flow, or report presentation changes, update Migration_Verification_Prompt.md and Migration_Verification_Prompt_Quick.md in the same change.
6. Keep README.md, BUS_FACTOR_HANDOFF.md, OFFLINE_BACKUP_CHECKLIST.md, and bootstrap-dashboard.ps1 aligned with the current setup and recovery workflow.
7. Preserve the WSU header-unit/logo-lockup markup and cougar logo when provided.
8. Ensure latest and previous HTML reports are clickable through app routes rather than local-only `file://` links.
9. Do not auto-load a different site's report into the page on startup; keep the page focused on the current site in the form.
10. Ensure report history lookup works even when the Site Name input and saved filenames differ by spaces, underscores, hyphens, or case.
11. Ensure changing or blurring the Site Name field refreshes the latest available report for that same site without requiring a rerun.
12. Ensure long full-site runs are not aborted by the old 10-minute dashboard timeout while they are still producing output.
13. If the audit stops before generating a report folder or report artifacts, return an error instead of silently leaving stale report data in place.
14. Ensure refreshed pages pick up new JS/CSS automatically and are not blocked by stale asset cache.
15. Disable caching for the dashboard page and report-history refresh responses so changing the Site Name field shows current state immediately.
16. Keep the dashboard result surface intentionally narrow: no summary counts, release readiness, or Queue B panels on the main page.
17. Keep the Generated Reports layout intentional: a single-row two-column desktop layout using the labels New Report and Previous Report, with a narrower Previous Report column that collapses to one column on mobile.

### For Administrators

1. Verify reports are generated correctly
2. Check `reports/` directory for output files
3. Monitor `http://localhost:5000/api/health` for server status
4. Check Flask console for errors/logs
5. Adjust timeout in `app.py` if needed (default: 600s = 10 min)

## Important Notes

- Dashboard automatically builds on first run
- Report links show after audit completes
- Previous report links appear when history exists
- Existing reports for the current site can be reloaded from the Site Name field without rerunning the audit
- Site/report history matching is tolerant of spaces, underscores, hyphens, and case differences
- Published report history may use YYYYMMDD or YYYYMMDD_HHMMSS format
- Crash recovery auto-restores missing files
- Reports sorted: FAIL before REVIEW, by similarity score

## Troubleshooting

### Dashboard won't start
```bash
# Check port is available
netstat -ano | findstr :5000

# Try different port in config.py
PORT = 5001
```

### Reports not appearing
- Check `reports/` directory exists
- Verify audit script runs successfully
- Check Flask console for errors
- Confirm the Site Name field matches the intended site and then tab or click away to trigger a refresh for that site

### Audit times out
- Use "Quick" mode (80 paths max)
- Set Test Allowlist to limit scope
- Increase timeout in `app.py` if needed

## Next Steps from Prompt Template

When using Migration_Verification_Prompt.md:

1. ✓ Dashboard is built (Step 1: COMPLETE)
2. → Use form to run audit (Step 2: USER ACTION)
3. → Dashboard auto-triages results (Step 3: AUTOMATIC)

The quick prompt should enforce the same dashboard behavior and branding requirements as the full prompt.

The prompt can now be used as-is - just fill in the placeholders:
- [SITE_NAME]
- [SOURCE_URL]  
- [TEST_URL]
- Optional: [RUN_MODE], [TEST_SCOPE], [TEST_ALLOWLIST], [TEST_ALLOWLIST_FILE], [REPORT_FOLDER_IF_ALREADY_RUN]

## Maintenance

- Clear old reports from `reports/` directory periodically
- Monitor disk space for large CSV files
- Check error logs in console
- Update `audit.py` to match your actual audit script
- Backup report files regularly

## Support

Refer to README.md for full documentation and API details.
