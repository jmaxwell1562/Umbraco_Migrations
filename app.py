"""Flask application for Migration Audit Dashboard."""
import os
import json
import re
import sys
import shutil
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from config import DEBUG, HOST, PORT, REPORTS_DIR, AUDIT_SCRIPT, WSU_PRIMARY_COLOR
from utils import (
    find_report_files, parse_audit_csv, parse_readiness_csv,
    get_report_history, format_file_size
)

app = Flask(__name__)
CORS(app)
app.config['DEBUG'] = DEBUG
app.config['JSON_SORT_KEYS'] = False


def _normalize_url(value):
    """Ensure dropdown host values are submitted as absolute URLs."""
    value = (value or '').strip()
    if not value:
        return ''
    if re.match(r'^https?://', value, flags=re.IGNORECASE):
        return value
    return f'https://{value.lstrip('/')}'


def _asset_version(filename):
    """Use static file mtime to invalidate stale browser cache."""
    static_path = os.path.join(app.static_folder, filename)
    try:
        return int(os.path.getmtime(static_path))
    except OSError:
        return int(datetime.now().timestamp())


def _report_url_from_path(file_path):
    """Build a web URL for files inside REPORTS_DIR."""
    if not file_path:
        return None
    abs_reports = os.path.abspath(REPORTS_DIR)
    abs_file = os.path.abspath(file_path)
    if not abs_file.startswith(abs_reports + os.sep):
        return None
    return f"/reports/{os.path.basename(abs_file)}"


def _build_improvement_summary(latest_counts, previous_counts):
    """Summarize positive movement from previous to latest report."""
    improvements = []
    if not latest_counts or not previous_counts:
        return improvements

    comparisons = [
        ('FAIL', 'fewer FAIL items', True),
        ('REVIEW', 'fewer REVIEW items', True),
        ('PASS', 'more PASS items', False),
        ('SOFT PASS', 'more SOFT PASS items', False),
    ]

    for key, label, lower_is_better in comparisons:
        latest_value = latest_counts.get(key, 0)
        previous_value = previous_counts.get(key, 0)
        delta = previous_value - latest_value if lower_is_better else latest_value - previous_value
        if delta > 0:
            improvements.append({
                'label': label,
                'delta': delta,
            })

    return improvements


@app.route('/')
def index():
    """Serve the dashboard."""
    return render_template(
        'dashboard.html',
        style_version=_asset_version('style.css'),
        script_version=_asset_version('dashboard.js'),
    )


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/reports/<path:filename>')
def serve_report(filename):
    """Serve generated report artifacts from REPORTS_DIR."""
    abs_target = os.path.abspath(os.path.join(REPORTS_DIR, filename))
    abs_reports = os.path.abspath(REPORTS_DIR)
    if not abs_target.startswith(abs_reports + os.sep):
        abort(404)
    if not os.path.exists(abs_target):
        abort(404)
    return send_from_directory(REPORTS_DIR, filename)


@app.route('/api/sites', methods=['GET'])
def get_sites():
    """Get list of sites with available reports."""
    sites = {}
    
    if os.path.exists(REPORTS_DIR):
        for file in os.listdir(REPORTS_DIR):
            if '_audit_report_' in file:
                # Extract site name (first part before _audit_report_)
                parts = file.split('_audit_report_')
                if parts:
                    site_name = parts[0]
                    if site_name not in sites:
                        sites[site_name] = {
                            'name': site_name,
                            'history': get_report_history(REPORTS_DIR, site_name),
                        }
    
    return jsonify({'sites': list(sites.values())})


@app.route('/api/audit/run', methods=['POST'])
def run_audit():
    """Run an audit with provided parameters."""
    try:
        data = request.get_json()
        
        site_name = data.get('site_name', '').strip()
        source_url = data.get('source_url', '').strip()
        test_url = _normalize_url(data.get('test_url', ''))
        run_mode = data.get('run_mode', 'full')
        test_scope = data.get('test_scope', 'single')
        test_allowlist = data.get('test_allowlist', '')
        test_allowlist_file = data.get('test_allowlist_file', '')
        report_folder = data.get('report_folder', '')
        
        # Validate required inputs
        if not site_name:
            return jsonify({'error': 'Site name is required'}), 400
        if not test_url:
            return jsonify({'error': 'Test URL is required'}), 400
        
        # If reusing report folder, skip audit run
        if report_folder:
            return jsonify({
                'message': 'Using existing report folder',
                'folder': report_folder,
                'status': 'pending_triage',
            })
        
        if not source_url:
            return jsonify({'error': 'Source URL is required for new audit'}), 400
        
        # Build audit.py command (match workspace audit.py argument names)
        cmd = [sys.executable, AUDIT_SCRIPT]
        cmd.extend(['--site', site_name])
        cmd.extend(['--source', source_url])
        cmd.extend(['--test_url', test_url])
        
        if run_mode == 'quick':
            cmd.extend(['--max_paths', '80'])
        
        if test_scope:
            cmd.extend(['--test_scope', test_scope])
        
        if test_allowlist:
            cmd.extend(['--test_allowlist', test_allowlist])
        
        if test_allowlist_file:
            cmd.extend(['--test_allowlist_file', test_allowlist_file])
        
        # Run audit
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            return jsonify({
                'error': 'Audit run failed',
                'details': result.stderr or result.stdout,
            }), 500
        
        # Parse output to find generated report folder
        output = result.stdout
        generated_folder = None
        # Example line: [OK] Audit Complete! Results: Audit_Site_YYYYMMDD_HHMMSS
        for line in output.split('\n'):
            match = re.search(r'Results:\s*(.+)$', line)
            if match:
                generated_folder = match.group(1).strip()
                break

        # Copy key generated artifacts to REPORTS_DIR so dashboard history works.
        if generated_folder and not os.path.isabs(generated_folder):
            generated_folder = os.path.abspath(os.path.join(os.path.dirname(AUDIT_SCRIPT), generated_folder))

        if not generated_folder:
            return jsonify({
                'error': 'Audit run did not generate a report folder',
                'details': output.strip() or result.stderr.strip() or 'The audit stopped before producing report files.',
            }), 500

        if not os.path.isdir(generated_folder):
            return jsonify({
                'error': 'Audit run did not produce an accessible report folder',
                'details': generated_folder,
            }), 500

        generated_artifacts = [
            filename for filename in os.listdir(generated_folder)
            if filename.endswith(('.csv', '.html', '.xlsx'))
        ]

        if not generated_artifacts:
            return jsonify({
                'error': 'Audit run finished without report artifacts',
                'details': output.strip() or 'The audit stopped before writing CSV, HTML, or XLSX files.',
            }), 500

        if generated_folder and os.path.isdir(generated_folder):
            for filename in generated_artifacts:
                src = os.path.join(generated_folder, filename)
                dst = os.path.join(REPORTS_DIR, filename)
                shutil.copy2(src, dst)
        
        return jsonify({
            'status': 'success',
            'message': 'Audit completed',
            'folder': os.path.abspath(generated_folder) if generated_folder else REPORTS_DIR,
            'output': output[:500],  # First 500 chars
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Audit run timed out after 10 minutes'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/<site_name>', methods=['GET'])
def get_site_reports(site_name):
    """Get all reports for a site."""
    try:
        site_name = site_name.strip()
        history = get_report_history(REPORTS_DIR, site_name, limit=10)
        latest = history[0] if history else None
        previous = history[1] if len(history) > 1 else None
        
        latest_data = None
        if latest:
            report_files = find_report_files(REPORTS_DIR, site_name, latest['date'])
            if 'main_csv' in report_files:
                audit_data = parse_audit_csv(report_files['main_csv'])
                readiness_data = None
                if 'readiness_csv' in report_files:
                    readiness_data = parse_readiness_csv(report_files['readiness_csv'])
                
                latest_data = {
                    'date': latest['date'],
                    'display_date': latest['display_date'],
                    'files': report_files,
                    'links': {
                        'audit_html': _report_url_from_path(report_files.get('audit_html')),
                        'executive_html': _report_url_from_path(report_files.get('executive_html')),
                    },
                    'audit_summary': audit_data,
                    'readiness': readiness_data,
                }

        previous_data = None
        if previous:
            prev_files = find_report_files(REPORTS_DIR, site_name, previous['date'])
            previous_audit_data = None
            if 'main_csv' in prev_files:
                previous_audit_data = parse_audit_csv(prev_files['main_csv'])

            previous_data = {
                'date': previous['date'],
                'display_date': previous['display_date'],
                'files': prev_files,
                'links': {
                    'audit_html': _report_url_from_path(prev_files.get('audit_html')),
                    'executive_html': _report_url_from_path(prev_files.get('executive_html')),
                },
                'audit_summary': previous_audit_data,
                'improvements': _build_improvement_summary(
                    latest_data.get('audit_summary', {}).get('counts', {}) if latest_data else {},
                    previous_audit_data.get('counts', {}) if previous_audit_data else {},
                ),
            }
        
        return jsonify({
            'site_name': site_name,
            'latest': latest_data,
            'previous': previous_data,
            'history': history,
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/<site_name>/<date_str>/queues', methods=['GET'])
def get_queues(site_name, date_str):
    """Get Queue A and Queue B for a report."""
    try:
        report_files = find_report_files(REPORTS_DIR, site_name, date_str)
        
        if 'main_csv' not in report_files:
            return jsonify({'error': 'Report not found'}), 404
        
        audit_data = parse_audit_csv(report_files['main_csv'])
        
        return jsonify({
            'site_name': site_name,
            'date': date_str,
            'summary_counts': audit_data.get('counts', {}),
            'queue_a': audit_data.get('queue_a', []),
            'queue_b': audit_data.get('queue_b', []),
            'total_records': audit_data.get('total_records', 0),
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<site_name>/<date_str>/<file_type>', methods=['GET'])
def download_report(site_name, date_str, file_type):
    """Get download URL or file info for a report."""
    try:
        report_files = find_report_files(REPORTS_DIR, site_name, date_str)
        
        file_type_map = {
            'audit': 'audit_html',
            'executive': 'executive_html',
            'csv': 'main_csv',
            'clusters': 'clusters_csv',
            'readiness': 'readiness_csv',
            'xlsx': 'xlsx',
        }
        
        key = file_type_map.get(file_type)
        if not key or key not in report_files:
            return jsonify({'error': 'File not found'}), 404
        
        file_path = report_files[key]
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        return jsonify({
            'file_type': file_type,
            'filename': os.path.basename(file_path),
            'size': format_file_size(file_size),
            'path': file_path,  # In production, use secure download handler
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/readiness/<site_name>/<date_str>', methods=['GET'])
def get_readiness(site_name, date_str):
    """Get release readiness summary."""
    try:
        report_files = find_report_files(REPORTS_DIR, site_name, date_str)
        
        if 'readiness_csv' not in report_files:
            return jsonify({'error': 'Readiness report not found'}), 404
        
        readiness_data = parse_readiness_csv(report_files['readiness_csv'])
        
        return jsonify({
            'site_name': site_name,
            'date': date_str,
            'readiness': readiness_data,
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
