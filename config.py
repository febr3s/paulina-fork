import os

# Session secret key
SECRET_KEY = os.environ.get("SECRET_KEY", "1234567890")

# Debug settings
DEBUG = os.environ.get("DEBUG", False)

# OAuth 2.0 Tokens
CLIENT_ID = os.environ.get("CLIENT_ID", "1234567890")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "1234567890")

# OAuth callback URL
REDIRECT_URL = os.environ.get("REDIRECT_URL", "https://paulina.toolforge.org/oauth-callback")

# User Agent
USER_AGENT = os.environ.get("USER_AGENT", "Paulina/1.0 (https://paulina.toolforge.org/; your-email@example.com)")
