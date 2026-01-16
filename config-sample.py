import os

# Determine mode from environment variable
WIKIDATA_TEST_MODE = os.environ.get('WIKIDATA_TEST_MODE', 'false').lower() == 'true'

# Session secret key
SECRET_KEY = ""

# Debug settings
# DEBUG = False

# OAuth 2.0 Tokens
CLIENT_ID = ""
CLIENT_SECRET = ""

# User Agent
USER_AGENT = 'Paulina/1.0 (https://paulina.toolforge.org/; your-email@example.com)'

# OAuth Configuration - based on mode
if WIKIDATA_TEST_MODE:
    # Test Wikidata
    REDIRECT_URL = ''
    WIKIDATA_API_URL = 'https://test.wikidata.org/w/api.php'
    WIKIDATA_REST_API_URL = 'https://test.wikidata.org/w/rest.php/wikibase/v1'
else:
    # Production Wikidata 
    REDIRECT_URL = 'https://paulina.toolforge.org/oauth-callback'
    WIKIDATA_API_URL = 'https://www.wikidata.org/w/api.php'
    WIKIDATA_REST_API_URL = 'https://www.wikidata.org/w/rest.php/wikibase/v1'

# OAuth URLs (same for both test and production)
AUTHORIZATION_BASE_URL = 'https://meta.wikimedia.org/w/rest.php/oauth2/authorize'
TOKEN_URL = 'https://meta.wikimedia.org/w/rest.php/oauth2/access_token'
PROFILE_URL = 'https://meta.wikimedia.org/w/rest.php/oauth2/resource/profile'

# OAuth Scopes
OAUTH_SCOPES = ['basic', 'editpage', 'createeditmovepage']

# Rate limiting
RATELIMIT_STORAGE_URL = 'memory://'
RATELIMIT_HEADERS_ENABLED = True