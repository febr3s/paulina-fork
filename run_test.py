#!/usr/bin/env python
"""
Run Paulina with test configuration
Usage: python run_test.py
"""

import os
import sys

# Use test config
os.environ['FLASK_ENV'] = 'development'

# Import app after setting environment
from app import app

# Override config with test config
app.config.from_pyfile('config_test.py')

if __name__ == '__main__':
    print("=" * 50)
    print("RUNNING PAULINA IN TEST MODE")
    print(f"OAuth endpoint: {app.config['OAUTH_MWURI']}")
    print(f"Wikidata API: {app.config['WIKIDATA_API_URL']}")
    print("=" * 50)
    app.run(debug=True, port=5000)