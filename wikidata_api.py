"""
Wikidata API Helper Module
Handles creating and editing Wikidata items via the Wikibase REST API

"""

import requests
from flask import session
import hashlib
import hmac
import time
import urllib.parse
import secrets
import base64


class WikidataAPI:
    """Helper class for Wikidata REST API operations"""
    
    BASE_URL = "https://www.wikidata.org/w/rest.php/wikibase/v1"
    
    # Property IDs for author data
    PROPERTIES = {
        'instance_of': 'P31',
        'sex_or_gender': 'P21',
        'country_of_citizenship': 'P27',
        'place_of_birth': 'P19',
        'date_of_birth': 'P569',
        'date_of_death': 'P570',
        'occupation': 'P106',
        'ethnic_group': 'P172',
        'image': 'P18',
        'official_website': 'P856',
    }
    
    # Reference properties
    REF_PROPERTIES = {
        'reference_url': 'P854',
        'title': 'P1476',
        'retrieved': 'P813',
    }
    
    def __init__(self, app_config):
        self.config = app_config 
        self.consumer_key = app_config['CONSUMER_KEY']
        self.consumer_secret = app_config['CONSUMER_SECRET']
        self.user_agent = app_config.get('USER_AGENT', 'Paulina/1.0')
        self.base_url = app_config.get('WIKIDATA_REST_API_URL', 'https://www.wikidata.org/w/rest.php/wikibase/v1/entities')
        print("Wikidata REST API URL:", self.base_url)
    
    
    def _get_access_token(self):
        """Get OAuth access token from session"""
        if 'access_token' not in session:
            raise Exception("User not authenticated")
        
        return (
            session['access_token']['key'],
            session['access_token']['secret']
        )
    
    def _generate_oauth_signature(self, method, url, params, token_secret):
        """Generate OAuth 1.0a signature"""
        # Sort and encode parameters
        sorted_params = sorted(params.items())
        param_string = urllib.parse.urlencode(sorted_params, quote_via=urllib.parse.quote)
        
        # Create signature base string
        base_string = '&'.join([
            method.upper(),
            urllib.parse.quote(url, safe=''),
            urllib.parse.quote(param_string, safe='')
        ])
        
        # Create signing key
        signing_key = '&'.join([
            urllib.parse.quote(self.consumer_secret, safe=''),
            urllib.parse.quote(token_secret, safe='')
        ])
        
        # Generate HMAC-SHA1 signature
        signature = hmac.new(
            signing_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        return base64.b64encode(signature).decode('utf-8')
    
    def _build_oauth_header(self, method, url, token_key, token_secret):
        """Build OAuth 1.0a Authorization header"""
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_token': token_key,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': secrets.token_hex(16),
            'oauth_version': '1.0'
        }
        
        # Generate signature
        signature = self._generate_oauth_signature(method, url, oauth_params, token_secret)
        oauth_params['oauth_signature'] = signature
        
        # Build header string
        header_parts = [f'{k}="{urllib.parse.quote(str(v), safe="")}"' 
                       for k, v in sorted(oauth_params.items())]
        
        return 'OAuth ' + ', '.join(header_parts)
    
    def _make_authenticated_request(self, method, endpoint, json_data=None):
        """Make an authenticated request using the mwoauth access token"""
        token_key, token_secret = self._get_access_token()
        
        url = f"{self.base_url}{endpoint}"
        
        # Build OAuth header
        auth_header = self._build_oauth_header(method, url, token_key, token_secret)
        
        headers = {
            'Authorization': auth_header,
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json'
        }
        
        if method == 'POST':
            response = requests.post(url, headers=headers, json=json_data, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=json_data, timeout=30)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=json_data, timeout=30)
        elif method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response
    
    def create_item(self, labels, descriptions, statements):
        """
        Create a new Wikidata item using REST API
        """
        try:
            url = f"{self.base_url}/items"

            # Build the item payload
            item_data = {
                "labels": labels,
                "descriptions": descriptions
            }

            # Add statements if provided
            if statements:
                # Group statements by property
                statements_dict = {}
                for statement in statements:
                    prop = statement['property']['id']
                    if prop not in statements_dict:
                        statements_dict[prop] = []
                    statements_dict[prop].append(statement)
                item_data["statements"] = statements_dict

            # Wrap in "item" key as required by API
            payload = {
                "item": item_data
            }

            # Log the payload
            print("\n" + "="*60)
            print("CREATE ITEM PAYLOAD:")
            print("="*60)
            import json
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print("="*60 + "\n")

            # Get OAuth headers
            token_key, token_secret = self._get_access_token()
            headers = {
                'Authorization': self._build_oauth_header('POST', url, token_key, token_secret),
                'User-Agent': self.user_agent,
                'Content-Type': 'application/json'
            }

            # Make the request
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            # Log the response
            print("\n" + "="*60)
            print("RAW API RESPONSE:")
            print("="*60)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"Raw Content (first 1000 chars): {response.text[:1000]}")
            print("="*60 + "\n")

            if response.status_code == 201:  # Created
                data = response.json()
                item_id = data.get('id')
                return {
                    'success': True,
                    'item_id': item_id,
                    'error': None
                }
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', 'Unknown error')
                except:
                    error_message = response.text

                return {
                    'success': False,
                    'item_id': None,
                    'error': error_message
                }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'item_id': None,
                'error': str(e)
            }
    
    def build_statement(self, property_id, value, value_type='wikibase-item', references=None):
        """
        Build a statement structure for the API
        
        Args:
            property_id: Wikidata property ID (e.g., 'P31')
            value: The value (Q-id for items, string for strings, etc.)
            value_type: Type of value ('wikibase-item', 'string', 'time', 'url', 'commonsMedia')
            references: List of reference dicts (optional)
        
        Returns:
            Statement dict ready for API
        """
        statement = {
            'property': {'id': property_id},
            'value': self._build_value(value, value_type)
        }
        
        if references:
            statement['references'] = references
        
        return statement

    def _build_value(self, value, value_type):
        """Build the value structure based on type"""
        if value_type == 'wikibase-item':
            return {
                'type': 'value',
                'content': value  # Just the QID as string
            }
        elif value_type == 'string':
            return {
                'type': 'value',
                'content': value
            }
        elif value_type == 'url':
            return {
                'type': 'value',
                'content': value
            }
        elif value_type == 'time':
            return {
                'type': 'value',
                'content': {
                    'time': self._format_date(value),
                    'precision': self._get_date_precision(value),
                    'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
                }
            }
        elif value_type == 'commonsMedia':
            return {
                'type': 'value',
                'content': value
            }
        else:
            return {
                'type': 'value',
                'content': value
            }
    
    def _format_date(self, date_string):
        """Convert date string (YYYY-MM-DD) to Wikidata format"""
        if not date_string:
            return None
        
        parts = date_string.split('-')
        year = parts[0] if len(parts) > 0 else '0000'
        month = parts[1] if len(parts) > 1 else '00'
        day = parts[2] if len(parts) > 2 else '00'
        
        return f"+{year}-{month}-{day}T00:00:00Z"
    
    def _get_date_precision(self, date_string):
        """Determine date precision (11=day, 10=month, 9=year)"""
        if not date_string:
            return 9
        
        parts = date_string.split('-')
        if len(parts) >= 3 and parts[2] not in ['', '00']:
            return 11
        elif len(parts) >= 2 and parts[1] not in ['', '00']:
            return 10
        else:
            return 9
    
    def build_reference(self, url, title=None, retrieved_date=None):
        """
        Build a reference structure
        
        Args:
            url: Reference URL
            title: Title of the source (optional)
            retrieved_date: Date accessed in YYYY-MM-DD format (optional)
        
        Returns:
            Reference dict ready for API
        """
        parts = []
        
        if url:
            parts.append({
                'property': {'id': self.REF_PROPERTIES['reference_url']},
                'value': {'type': 'value', 'content': url}
            })
        
        if title:
            parts.append({
                'property': {'id': self.REF_PROPERTIES['title']},
                'value': {
                    'type': 'value',
                    'content': {
                        'text': title,
                        'language': 'en'
                    }
                }
            })
        
        if retrieved_date:
            parts.append({
                'property': {'id': self.REF_PROPERTIES['retrieved']},
                'value': {
                    'type': 'value',
                    'content': {
                        'time': self._format_date(retrieved_date),
                        'precision': 11,
                        'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
                    }
                }
            })
        
        return {'parts': parts}
    
    def extract_commons_filename(self, url):
        """Extract filename from Commons URL"""
        if not url:
            return None
        
        import urllib.parse as urlparse
        
        if 'upload.wikimedia.org' in url:
            # Format: https://upload.wikimedia.org/wikipedia/commons/a/ab/Filename.jpg
            parts = url.split('/')
            if len(parts) > 0:
                return urlparse.unquote(parts[-1])
        
        elif 'commons.wikimedia.org' in url:
            # Format: https://commons.wikimedia.org/wiki/File:Filename.jpg
            if 'File:' in url:
                filename = url.split('File:')[-1]
                return urlparse.unquote(filename.split('?')[0])
        
        return None