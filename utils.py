"""Utilities for report parsing and triaging."""
import os
import csv
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json


def _canonical_site_key(value):
    """Normalize site identifiers for tolerant report file matching."""
    value = (value or '').strip().lower()
    if not value:
        return ''
    return re.sub(r'[^a-z0-9]+', '', value)


def _report_file_matches_site(file_name, site_name):
    """Match report files regardless of spaces, underscores, or hyphens."""
    marker_match = re.search(r'_(audit_report|failure_clusters|release_readiness|executive_view)_', file_name)
    if not marker_match:
        return False

    file_site_name = file_name[:marker_match.start()]
    return _canonical_site_key(file_site_name) == _canonical_site_key(site_name)


def find_latest_report(reports_dir, site_name):
    """Find the latest generated report for a site."""
    if not os.path.exists(reports_dir):
        return None
    
    files = []
    for file in os.listdir(reports_dir):
        if _report_file_matches_site(file, site_name) and '_audit_report_' in file and file.endswith('.csv'):
            files.append(file)
    
    if files:
        files.sort(reverse=True)
        return files[0]
    return None


def find_report_files(reports_dir, site_name, date_str=None):
    """Find all report files for a site and optional date."""
    results = {}
    
    if not os.path.exists(reports_dir):
        return results
    
    for file in os.listdir(reports_dir):
        if not _report_file_matches_site(file, site_name):
            continue
        
        if date_str and date_str not in file:
            continue
        
        full_path = os.path.join(reports_dir, file)
        
        if '_audit_report_' in file and file.endswith('.csv'):
            results['main_csv'] = full_path
        elif '_failure_clusters_' in file and file.endswith('.csv'):
            results['clusters_csv'] = full_path
        elif '_release_readiness_' in file and file.endswith('.csv'):
            results['readiness_csv'] = full_path
        elif '_audit_report_' in file and file.endswith('.html'):
            results['audit_html'] = full_path
        elif '_executive_view_' in file and file.endswith('.html'):
            results['executive_html'] = full_path
        elif file.endswith('.xlsx'):
            results['xlsx'] = full_path
    
    return results


def parse_audit_csv(csv_path):
    """Parse audit CSV and extract summary counts and queues."""
    if not os.path.exists(csv_path):
        return None
    
    counts = {
        'PASS': 0,
        'SOFT PASS': 0,
        'REVIEW': 0,
        'FAIL': 0,
        'REDIRECT': 0,
    }
    
    queue_a = []  # Fix on test site (migration gaps)
    queue_b = []  # Source/shared instability
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                status = row.get('status', '').upper()
                
                if status in counts:
                    counts[status] += 1
                
                # Build queues from FAIL and REVIEW rows
                if status in ['FAIL', 'REVIEW']:
                    if status == 'REDIRECT':
                        continue  # Skip redirects in priority
                    
                    item = {
                        'path': row.get('path', ''),
                        'status': status,
                        'score': float(row.get('score', 0)) if row.get('score') else 0,
                        'note': row.get('note', ''),
                        'root_cause': row.get('root_cause', ''),
                    }
                    
                    # Classify into Queue A or B
                    root_cause = item['root_cause'].lower() if item['root_cause'] else ''
                    
                    if any(keyword in root_cause for keyword in ['migration', 'mapping', 'redirect', 'url']):
                        queue_a.append(item)
                    else:
                        queue_b.append(item)
        
        # Sort queues: FAIL before REVIEW, then by score (lowest first for REVIEW)
        queue_a.sort(key=lambda x: (x['status'] != 'FAIL', x['score']))
        queue_b.sort(key=lambda x: (x['status'] != 'FAIL', x['score']))
        
        return {
            'counts': counts,
            'queue_a': queue_a[:20],  # Limit to top 20
            'queue_b': queue_b[:20],
            'total_records': sum(counts.values()),
        }
    
    except Exception as e:
        return {'error': str(e)}


def parse_readiness_csv(csv_path):
    """Parse release readiness CSV."""
    if not os.path.exists(csv_path):
        return None
    
    readiness = {
        'GO': 0,
        'CONDITIONAL GO': 0,
        'NO GO': 0,
        'sections': {},
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                status = row.get('status', '').upper()
                
                if status in readiness:
                    readiness[status] += 1
                
                if status == 'NO GO':
                    section = row.get('section', 'General')
                    reason = row.get('reason', '')
                    
                    if section not in readiness['sections']:
                        readiness['sections'][section] = []
                    
                    readiness['sections'][section].append(reason)
        
        return readiness
    
    except Exception as e:
        return {'error': str(e)}


def get_report_history(reports_dir, site_name, limit=5):
    """Get report history for a site."""
    if not os.path.exists(reports_dir):
        return []
    
    reports = []
    
    for file in os.listdir(reports_dir):
        if not _report_file_matches_site(file, site_name) or '_audit_report_' not in file or not file.endswith('.csv'):
            continue
        
        try:
            # Extract YYYYMMDD from names like site_audit_report_YYYYMMDD.csv
            match = re.search(r'(\d{8})(?=\.[^.]+$)', file)
            if not match:
                continue

            date_str = match.group(1)
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            reports.append({
                'date': date_str,
                'display_date': date_obj.strftime('%Y-%m-%d'),
                'file': file,
                'path': os.path.join(reports_dir, file),
            })
        except (ValueError, IndexError):
            pass
    
    # Sort by date descending
    reports.sort(key=lambda x: x['date'], reverse=True)
    
    return reports[:limit]


def format_file_size(bytes_size):
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"
