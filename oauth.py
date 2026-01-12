from flask import session, current_app as app
from flask_babel import _
from requests_oauthlib import OAuth2Session
import time


def save_token_to_session(new_token):
    """
    Callback function to save refreshed OAuth token to Flask session.
    
    This is called automatically by requests-oauthlib when a token is refreshed.
    
    Args:
        new_token (dict): The new token dictionary containing access_token, 
                         refresh_token, expires_at, etc.
    """
    session.update({'oauth_token': new_token})


def get_oauth_session(token=None, state=None):
    """Create OAuth2Session with automatic token refresh"""
    
    if token is None and 'oauth_token' in session:
        token = session['oauth_token']
    
    return OAuth2Session(
        app.config['CLIENT_ID'],
        token=token,
        state=state,
        redirect_uri=app.config['REDIRECT_URL'],
        scope=app.config['OAUTH_SCOPES'],
        auto_refresh_url=app.config['TOKEN_URL'],
        auto_refresh_kwargs={
            'client_id': app.config['CLIENT_ID'],
            'client_secret': app.config['CLIENT_SECRET']
        },
        token_updater=save_token_to_session
    )


def token_refresh():
    """Refresh the OAuth token before it expires."""
    if 'oauth_token' not in session:
        return False
    
    token = session['oauth_token']
    
    # Refresh if token expires in less than 5 minutes (300 seconds)
    if token['expires_at'] < time.time() + 300:
        # Check if we have a refresh token
        if not token.get('refresh_token'):
            session.clear()
            return False
        
        try:
            import requests
            
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': token['refresh_token'],
                'client_id': app.config['CLIENT_ID'],
                'client_secret': app.config['CLIENT_SECRET']
            }
            
            headers = {
                'User-Agent': app.config['USER_AGENT']
            }
            
            response = requests.post(app.config['TOKEN_URL'], data=refresh_data, headers=headers)
            
            if response.status_code == 200:
                response_json = response.json()
                
                if 'access_token' in response_json:
                    # Calculate expires_at
                    if 'expires_in' in response_json:
                        response_json['expires_at'] = time.time() + response_json['expires_in']
                    
                    session['oauth_token'] = response_json
                    return True
                else:
                    session.clear()
                    return False
            else:
                session.clear()
                return False
            
        except Exception as e:
            session.clear()
            return False
    else:
        return True