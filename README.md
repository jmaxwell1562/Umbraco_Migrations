# WSU Migration Verification Audit Dashboard

An interactive dashboard for managing WSU site migrations, running audits, and triaging migration gaps.

For full recovery, replication, and handoff instructions, see `BUS_FACTOR_HANDOFF.md`.
For offline archiving, see `OFFLINE_BACKUP_CHECKLIST.md`.

## Features

- **Interactive Dashboard**: User-friendly interface to configure and run migration audits
- **Real-time Progress**: Live progress tracking during audit execution
- **Report Generation**: Automatic HTML, CSV, and XLSX report generation
- **Triage Queues**: Automated categorization of issues into Queue A (migration gaps) and Queue B (source/API issues)
- **Generated Reports Layout**: A single-row two-column report area with a wider New Report section and a narrower Previous Report section
- **Report History**: Track previous audits and compare the New Report against the Previous Report
- **WSU Branding**: Styled with WSU colors and logo

## Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Navigate to the workspace directory:
```bash
cd c:\Users\jill.maxwell\Documents\Umbraco_Migrations
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the dashboard server:
```bash
python app.py
```

4. Open your browser to:
```
http://localhost:5000
```

### One-Command Clean Machine Setup

For a new machine, you can bootstrap a local virtual environment, install all dependencies, install Playwright Chromium, and start the dashboard with:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap-dashboard.ps1
```

To set everything up without launching the dashboard immediately:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap-dashboard.ps1 -SkipStart
```

## Usage

### Running an Audit

1. **Fill in the form:**
   - **Site Name**: Identifier for the site (e.g., `about-urec`)
   - **Source URL**: Original site URL
   - **Test URL** *(required)*: Choose from the predefined test environments dropdown
   - **Localhost Option**: `https://localhost:7019/` is available in the dropdown for local test runs
   - **Localhost Requirement**: A local app must actually be running and listening on port `7019` before a localhost audit can succeed
   - **Run Mode**: `quick` (80 paths max) or `full` (entire site)
   - **Test Scope**: `single`, `instance`, or `ask`
   - **Test Allowlist**: Optional comma-separated paths to focus on

2. **Click "Start Audit"**

   Full-site runs can take 10 to 30+ minutes before reports appear. Quick runs usually finish much sooner.

3. **View Results:**
   - **Generated Reports** shown below the form in a single desktop row with two columns
   - **New Report**: latest HTML audit report, shown only after the new run completes
   - **Previous Report**: prior HTML audit report plus brief improvement stats when history exists
   - **Fix On Test Site: Top 10 Priority** queue for the highest-priority migration gaps

### Using Existing Reports

If you've already run an audit and want to skip the run:

1. Enter the **Use Existing Report Folder** path
2. The dashboard will triage that report instead

### Report History

The dashboard automatically tracks report history for the site currently being run or selected in the form. In the Generated Reports area, New Report and Previous Report are shown as two columns in a single row on desktop and stack on mobile. The page does not show a Recent Sites browsing section. Report lookup is tolerant of spaces, underscores, hyphens, and case differences between the Site Name field and the saved report filenames, and changing or blurring the Site Name field reloads the latest available report for that same site without requiring a rerun.

## Project Structure

```
├── app.py                 # Flask backend server
├── config.py              # Configuration settings
├── utils.py               # Report parsing and utilities
├── requirements.txt       # Python dependencies
├── templates/
│   └── dashboard.html     # Main dashboard UI
├── static/
│   ├── style.css          # Styling (WSU branding)
│   └── dashboard.js       # Frontend logic
├── reports/               # Generated audit reports
└── README.md              # This file
```

## API Endpoints

### Core Endpoints

- `GET /` - Dashboard HTML
- `GET /api/health` - Health check
- `GET /api/sites` - List all sites with report history
- `POST /api/audit/run` - Start a new audit run
- `GET /api/reports/<site_name>` - Get latest report for site
- `GET /api/reports/<site_name>/<date>/queues` - Get Queue A and B
- `GET /api/readiness/<site_name>/<date>` - Get release readiness summary

## Report Output

Generated reports are stored in the `reports/` directory with the following naming convention:

- **Main CSV**: `{site}_audit_report_{YYYYMMDD}.csv`
- **Clusters CSV**: `{site}_failure_clusters_{YYYYMMDD}.csv`
- **Readiness CSV**: `{site}_release_readiness_{YYYYMMDD}.csv`
- **HTML Report**: `{site}_audit_report_{YYYYMMDD}.html`
- **Executive HTML**: `{site}_executive_view_{YYYYMMDD}.html`
- **Excel**: `{site}_audit_report_{YYYYMMDD}.xlsx`

## CSV Report Format

### Main Audit Report

| Column | Description |
|--------|-------------|
| path | Page path |
| source_url | Original URL |
| test_url | Test environment URL |
| score | Similarity score (0-1) |
| status | PASS, SOFT PASS, REVIEW, FAIL, or REDIRECT |
| note | Issue description |
| root_cause | Root cause classification |

### Release Readiness Report

| Column | Description |
|--------|-------------|
| section | Site section |
| status | GO, CONDITIONAL GO, or NO GO |
| reason | Status reason |

## Queue Classification

### Queue A: Fix on Test Site (Migration Gaps)
- Items with root causes related to migration, mapping, URL issues
- Direct action required on test environment

### Queue B: Source/Shared Instability
- Items related to source APIs, shared services, redirects
- Requires coordination with source team or infrastructure

## Customization

### WSU Branding Colors

Edit `config.py` to change colors:

```python
WSU_PRIMARY_COLOR = '#981E32'      # Crimson
WSU_SECONDARY_COLOR = '#003C71'    # Navy
WSU_ACCENT_COLOR = '#D4AF37'       # Gold
```

### Configuration

Edit `config.py` to change:
- Server host/port
- Report directory location
- Timeout settings
- Audit script location

## Development

## Documentation Synchronization

- When dashboard behavior, layout, controls, labels, or report presentation changes, update this README, Migration_Verification_Prompt.md, Migration_Verification_Prompt_Quick.md, and .github/copilot-instructions.md in the same pass.

### Running in Development Mode

The dashboard is configured to run in development/debug mode by default. To disable:

Edit `config.py`:
```python
DEBUG = False
```

### Extending the Dashboard

To add custom report parsing:

1. Add parsing function to `utils.py`
2. Create API endpoint in `app.py`
3. Add UI elements in `templates/dashboard.html`
4. Add JavaScript handlers in `static/dashboard.js`

## Troubleshooting

### Reports Not Appearing

- Verify `reports/` directory exists
- Check audit script output for errors
- Ensure report filenames match expected pattern
- Confirm the Site Name field is set to the intended site and then tab or click away to refresh that site's latest report

### Localhost Audit Fails

- Confirm your local app is running on `https://localhost:7019/`
- Confirm something is actually listening on port `7019`
- Localhost HTTPS certificate errors are ignored by the audit runner, but the local site still must be reachable
- If audit preflight fails before report generation, the dashboard returns an error instead of silently continuing to show stale report output

### Audit Timeout

- Use "Quick" run mode for faster validation
- Set `TEST_ALLOWLIST` to limit scope
- The dashboard now allows longer waits for full runs than the old 10-minute limit, but very large sites may still take a substantial amount of time

### Port Already in Use

Change port in `config.py`:
```python
PORT = 5001  # or another available port
```

## Future Enhancements

- [ ] User authentication
- [ ] Custom report templates
- [ ] Scheduled audits
- [ ] Email notifications
- [ ] Report comparison tool
- [ ] Dashboard persistence
- [ ] Redirect classification export
- [ ] Advanced filtering and search

## Support

For issues or questions, refer to the Migration Verification Prompt documentation or contact the WSU IT team.
