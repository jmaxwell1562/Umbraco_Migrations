# Offline Backup Checklist

Use this checklist when creating a zip or offline copy of the WSU Migration Verification Dashboard workspace.

## Recommended Zip Name

Use a dated filename such as:

```text
Umbraco_Migrations_backup_YYYYMMDD.zip
```

## Zip These Exact Files and Folders

Application and runtime:
- `app.py`
- `audit.py`
- `utils.py`
- `config.py`
- `requirements.txt`
- `start-dashboard.bat`
- `bootstrap-dashboard.ps1`

UI:
- `templates/`
- `static/`

Prompts and instructions:
- `Migration_Verification_Prompt.md`
- `Migration_Verification_Prompt_Quick.md`
- `.github/copilot-instructions.md`
- `README.md`
- `BUS_FACTOR_HANDOFF.md`
- `OFFLINE_BACKUP_CHECKLIST.md`

Historical outputs you likely want:
- `reports/`
- important `Audit_*` folders you want to preserve

Optional but useful inputs and reference files:
- `paths.txt`
- `paths_dining.txt`
- `paths_cougarcard.txt`
- `SApaths.txt`
- `SIpaths.txt`
- `test_sites_allowlist_example.txt`
- `masterURLList.xlsx`

## Usually Exclude These

Do not rely on these for recovery:
- `__pycache__/`
- local virtual environments such as `.venv-1/`
- temporary logs you do not care about

They can be recreated.

## Minimum Recovery Zip

If you need the smallest viable backup, include at least:

1. `app.py`
2. `audit.py`
3. `utils.py`
4. `config.py`
5. `templates/`
6. `static/`
7. `requirements.txt`
8. `bootstrap-dashboard.ps1`
9. `Migration_Verification_Prompt.md`
10. `Migration_Verification_Prompt_Quick.md`
11. `.github/copilot-instructions.md`
12. `README.md`
13. `BUS_FACTOR_HANDOFF.md`
14. `reports/`

## Before You Zip

Confirm:

1. `reports/` contains the latest HTML and CSV files you care about.
2. Prompt files reflect the current dashboard behavior.
3. Backup docs mention that report lookup tolerates spaces, underscores, hyphens, and case differences in site names.
4. Backup docs mention that changing or blurring the Site Name field reloads the current site's latest report without requiring a rerun.
5. `requirements.txt` includes both dashboard and audit dependencies.
6. `bootstrap-dashboard.ps1` exists.
7. `BUS_FACTOR_HANDOFF.md` exists.

## After You Zip

Store the archive in at least one additional location:

1. local external drive, or
2. cloud storage, or
3. shared team storage

If possible, also export the latest HTML reports separately for non-technical readers.