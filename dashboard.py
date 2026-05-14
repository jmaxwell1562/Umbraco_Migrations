#!/usr/bin/env python3
"""
Umbraco Migration Audit Dashboard
Web interface for managing audit configuration and viewing results
"""

import os
import sys
import json
import subprocess
import glob
import re
import shutil
from datetime import datetime
from pathlib import Path
from threading import Thread
from flask import Flask, render_template, request, jsonify, send_file

# Base directory
BASE_DIR = Path(__file__).parent
AUDIT_DIR = BASE_DIR / 'audit.py'
DASHBOARD_DEFAULTS_DIR = BASE_DIR / 'dashboard_defaults'


def ensure_dashboard_files():
    """Restore dashboard assets from defaults if files are missing."""
    required_files = {
        BASE_DIR / 'templates' / 'base.html': DASHBOARD_DEFAULTS_DIR / 'templates' / 'base.html',
        BASE_DIR / 'templates' / 'index.html': DASHBOARD_DEFAULTS_DIR / 'templates' / 'index.html',
        BASE_DIR / 'static' / 'style.css': DASHBOARD_DEFAULTS_DIR / 'static' / 'style.css',
    }

    restored = []
    for target, default_source in required_files.items():
        if target.exists():
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        if default_source.exists():
            shutil.copy2(default_source, target)
            restored.append(target.relative_to(BASE_DIR).as_posix())
        else:
            print(f"[WARN] Missing dashboard default source: {default_source}")

    if restored:
        print(f"[INFO] Restored dashboard files: {', '.join(restored)}")


ensure_dashboard_files()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

# Status tracking for active audits
active_audits = {}


def normalize_site_name(value):
    return (value or '').strip().lower()


def get_running_audits():
    running = []
    for audit_id, audit in active_audits.items():
        if audit.get('status') != 'running':
            continue
        running.append({
            'audit_id': audit_id,
            'site': audit.get('site', ''),
            'started_at': audit.get('started_at', ''),
        })
    return running


def find_latest_file(folder_path, patterns):
    """Return newest file matching one of the provided glob patterns."""
    matches = []
    for pattern in patterns:
        matches.extend(folder_path.glob(pattern))

    files = [path for path in matches if path.exists() and path.is_file()]
    if not files:
        return None

    return max(files, key=lambda path: path.stat().st_mtime)


def get_audit_folders():
    """Get list of all audit result folders, sorted by newest first."""
    audit_pattern = BASE_DIR / 'Audit_*'
    candidates = sorted(glob.glob(str(audit_pattern)), reverse=True)
    folders = [path for path in candidates if Path(path).is_dir()]
    timestamp_pattern = re.compile(r'^\d{8}$')
    time_pattern = re.compile(r'^\d{4}(\d{2})?$')
    
    results = []
    for folder in folders:
        folder_name = Path(folder).name
        # Parse folder name: Audit_SITE_YYYYMMDD_HHMM
        parts = folder_name.split('_')
        if len(parts) >= 4:
            site = '_'.join(parts[1:-2])  # Handle multi-word sites
            date_str = parts[-2]
            time_str = parts[-1]

            if not timestamp_pattern.match(date_str) or not time_pattern.match(time_str):
                continue
            
            # Format readable date/time
            try:
                if len(time_str) == 6:
                    dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                else:
                    dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M")
                readable_time = dt.strftime("%Y-%m-%d %H:%M")
            except:
                readable_time = f"{date_str} {time_str}"
            
            results.append({
                'folder': folder_name,
                'site': site,
                'datetime': readable_time,
                'path': folder
            })
    
    return results


def get_site_report_history(site_name):
    """Return latest and previous HTML report paths for a site."""
    normalized_target = normalize_site_name(site_name)
    if not normalized_target:
        return {'latest': None, 'previous': None}

    latest = None
    previous = None
    for audit in get_audit_folders():
        if normalize_site_name(audit.get('site')) != normalized_target:
            continue

        files = get_audit_report_files(audit['folder'])
        report_path = files.get('report')
        if not report_path:
            continue

        relative = report_path.relative_to(BASE_DIR).as_posix()
        if latest is None:
            latest = relative
        elif previous is None:
            previous = relative
            break

    return {'latest': latest, 'previous': previous}


def get_audit_report_files(audit_folder):
    """Get available report files for an audit."""
    folder_path = BASE_DIR / audit_folder

    primary_report = find_latest_file(folder_path, ['report.html', '*_audit_report_*.html'])
    executive_report = find_latest_file(folder_path, ['*_executive_view_*.html'])

    files = {
        'detail': find_latest_file(folder_path, ['detail.csv', '*_audit_report_*.csv', '_audit_report.csv']),
        'report': primary_report,
        'executive_report': executive_report,
        'readiness': find_latest_file(folder_path, ['readiness.csv', '*_release_readiness_*.csv']),
        'failures': find_latest_file(folder_path, ['failure_clusters.csv', '*_failure_clusters_*.csv']),
        'xlsx': find_latest_file(folder_path, ['*.xlsx'])
    }

    available = {}
    for name, path in files.items():
        if path is not None:
            available[name] = path

    return available


def parse_csv_summary(csv_path):
    """Extract summary stats from detail CSV."""
    if not csv_path.exists():
        return {}
    
    try:
        import csv
        stats = {
            'PASS': 0, 'SOFT PASS': 0, 'REVIEW': 0, 'FAIL': 0,
            'REDIRECT': 0, 'SKIP': 0, 'ERROR': 0
        }
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                status = row.get('status', '').strip()
                if status in stats:
                    stats[status] += 1
        
        return stats
    except Exception as e:
        return {'error': str(e)}


@app.route('/')
def index():
    """Main dashboard page."""
    audits = get_audit_folders()
    return render_template('index.html', audits=audits)


@app.route('/api/audits')
def api_audits():
    """Get list of audits with summary info."""
    audits = get_audit_folders()
    
    enhanced = []
    for audit in audits:
        files = get_audit_report_files(audit['folder'])
        summary = parse_csv_summary(files.get('detail')) if 'detail' in files else {}
        
        enhanced.append({
            **audit,
            'has_report': 'report' in files,
            'has_detail': 'detail' in files,
            'report_path': files['report'].relative_to(BASE_DIR).as_posix() if 'report' in files else None,
            'detail_path': files['detail'].relative_to(BASE_DIR).as_posix() if 'detail' in files else None,
            'summary': summary
        })
    
    return jsonify(enhanced)


@app.route('/api/audit/<audit_folder>')
def api_audit_detail(audit_folder):
    """Get detailed info for a specific audit."""
    files = get_audit_report_files(audit_folder)
    summary = parse_csv_summary(files.get('detail')) if 'detail' in files else {}
    
    return jsonify({
        'folder': audit_folder,
        'files': {k: v.relative_to(BASE_DIR).as_posix() for k, v in files.items()},
        'summary': summary
    })


@app.route('/api/report-history/<site_name>')
def api_report_history(site_name):
    """Get latest and previous report links for a specific site."""
    history = get_site_report_history(site_name)
    return jsonify(history)


@app.route('/api/active-audits')
def api_active_audits():
    """Return running audits for pre-launch safety checks in UI."""
    return jsonify(get_running_audits())


@app.route('/report/<path:filepath>')
def view_report(filepath):
    """Serve HTML report."""
    file_path = BASE_DIR / filepath
    if file_path.exists() and str(file_path).endswith('.html'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Report not found", 404


@app.route('/download/<path:filepath>')
def download_file(filepath):
    """Download CSV or Excel file."""
    file_path = BASE_DIR / filepath
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    return "File not found", 404


@app.route('/api/launch-audit', methods=['POST'])
def launch_audit():
    """Launch a new audit with provided configuration."""
    try:
        data = request.json
        
        source_url = data.get('source_url', '').strip()
        test_url = data.get('test_url', '').strip()
        site_name = data.get('site_name', '').strip()
        scope = data.get('scope', 'single').strip() or 'single'
        max_paths = data.get('max_paths', '')
        test_allowlist = data.get('test_allowlist', '').strip()
        test_allowlist_file = data.get('test_allowlist_file', '').strip()
        force_parallel = bool(data.get('force_parallel', False))
        
        # Validate inputs
        if not source_url or not test_url or not site_name:
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not source_url.startswith(('http://', 'https://')):
            return jsonify({'error': 'Source URL must start with http:// or https://'}), 400
        
        if not test_url.startswith(('http://', 'https://')):
            return jsonify({'error': 'Test URL must start with http:// or https://'}), 400

        if scope not in {'single', 'instance', 'ask'}:
            return jsonify({'error': 'Scope must be single, instance, or ask'}), 400

        running = get_running_audits()
        normalized_site = normalize_site_name(site_name)
        same_site_running = [
            audit for audit in running
            if normalize_site_name(audit.get('site')) == normalized_site
        ]

        if same_site_running:
            return jsonify({
                'error': f'An audit for {site_name} is already running.',
                'code': 'duplicate_site_running',
                'running': running
            }), 409

        if running and not force_parallel:
            return jsonify({
                'error': 'Another audit is currently running. Launching another may slow both runs.',
                'code': 'parallel_running',
                'running': running
            }), 409
        
        # Build command
        cmd = [
            sys.executable,
            str(AUDIT_DIR),
            '--site', site_name,
            '--source', source_url,
            '--test_url', test_url,
            '--test_scope', scope
        ]
        
        if max_paths:
            try:
                cmd.extend(['--max_paths', str(int(max_paths))])
            except ValueError:
                pass

        if test_allowlist:
            cmd.extend(['--test_allowlist', test_allowlist])

        if test_allowlist_file:
            cmd.extend(['--test_allowlist_file', test_allowlist_file])
        
        # Generate audit ID
        audit_id = f"{site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        active_audits[audit_id] = {
            'status': 'running',
            'cmd': cmd,
            'site': site_name,
            'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Run audit in background thread
        def run_audit():
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=BASE_DIR
                )
                active_audits[audit_id]['status'] = 'completed' if result.returncode == 0 else 'failed'
                active_audits[audit_id]['output'] = result.stdout
                active_audits[audit_id]['error'] = result.stderr
            except Exception as e:
                active_audits[audit_id]['status'] = 'failed'
                active_audits[audit_id]['error'] = str(e)
        
        thread = Thread(target=run_audit, daemon=True)
        thread.start()
        
        return jsonify({'audit_id': audit_id, 'status': 'started'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/audit-status/<audit_id>')
def audit_status(audit_id):
    """Check status of running audit."""
    if audit_id in active_audits:
        return jsonify(active_audits[audit_id])
    return jsonify({'status': 'unknown'}), 404


@app.template_filter('filesizeformat')
def filesizeformat(bytes):
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024.0
    return f"{bytes:.1f}TB"


if __name__ == '__main__':
    print("Starting Umbraco Migration Audit Dashboard...")
    print("Open browser to: http://localhost:5000")
    app.run(debug=True, port=5000)
