"""Configuration for Migration Audit Dashboard."""
import os
from datetime import datetime

# Flask configuration
DEBUG = True
HOST = '127.0.0.1'
PORT = 5000

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
AUDIT_SCRIPT = os.path.join(BASE_DIR, 'audit.py')

# Ensure reports directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

# Report file patterns
REPORT_PATTERNS = {
    'main_csv': '{site}_audit_report_{date}.csv',
    'clusters_csv': '{site}_failure_clusters_{date}.csv',
    'readiness_csv': '{site}_release_readiness_{date}.csv',
    'audit_html': '{site}_audit_report_{date}.html',
    'executive_html': '{site}_executive_view_{date}.html',
    'xlsx': '{site}_audit_report_{date}.xlsx',
}

# WSU Branding
WSU_PRIMARY_COLOR = '#981E32'  # WSU Crimson
WSU_SECONDARY_COLOR = '#003C71'  # WSU Navy
WSU_ACCENT_COLOR = '#D4AF37'  # Gold accent
WSU_LIGHT_BG = '#F5F5F5'
WSU_TEXT_COLOR = '#333333'
