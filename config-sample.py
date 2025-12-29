import os

# Flask Configuration
SECRET_KEY = ""  
DEBUG = False

# OAuth Configuration (See README.md for detailed setup instructions)
CONSUMER_KEY = ""
CONSUMER_SECRET = ""
OAUTH_MWURI = "https://meta.wikimedia.org/w/index.php"

# User-Agent for API requests 
USER_AGENT = 'Paulina/1.0 (https://paulina.toolforge.org/; your-email@example.com)'

# Wikidata API URLs
WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_REST_API_URL = "https://www.wikidata.org/w/rest.php/wikibase/v1"

# Rate Limiting
RATELIMIT_STORAGE_URL = "memory://" 
RATELIMIT_HEADERS_ENABLED = True

# Rate limit values
RATE_LIMIT_PER_DAY = int(os.getenv('RATE_LIMIT_PER_DAY', '200'))
RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', '50'))
RATE_LIMIT_SUBMISSIONS_PER_HOUR = int(os.getenv('RATE_LIMIT_SUBMISSIONS_PER_HOUR', '20'))