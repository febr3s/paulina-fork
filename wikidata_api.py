"""
Wikidata API Helper Module
Handles creating and editing Wikidata items via the Wikibase REST API
Includes Wikidata property/item ID constants and utility functions
"""

import json
import requests
import os
import urllib.parse as urlparse
from flask_babel import lazy_gettext as _l, gettext as _ 



# WIKIDATA CONSTANTS - Test/Production Mode Configuration

# Check for test mode
WIKIDATA_TEST_MODE = os.environ.get('WIKIDATA_TEST_MODE', 'false').lower() == 'true'

# Property IDs (PIDs)
if WIKIDATA_TEST_MODE:
    # Test Wikidata properties (from test.wikidata.org)
    PID_INSTANCE_OF = 'P82'           # instance of
    PID_SEX_OR_GENDER = 'P192'         # sex or gender
    PID_COUNTRY_OF_CITIZENSHIP = 'P196' # country of citizenship
    PID_DATE_OF_BIRTH = 'P18'         # date of birth
    PID_DATE_OF_DEATH = 'P25'        # date of death
    PID_PLACE_OF_BIRTH = 'P342'       # place of birth
    PID_OCCUPATION = 'P204'           # occupation
    PID_ETHNIC_GROUP = 'P84982'         # ethnic group
    PID_IMAGE = 'P185'                # image
    PID_OFFICIAL_WEBSITE = 'P206'     # official website
    PID_REFERENCE_URL = 'P93'        # reference URL
    PID_TITLE = 'P77107'                # title
    PID_RETRIEVED = 'P388'            # retrieved
else:
    # Production Wikidata properties
    PID_INSTANCE_OF = 'P31'
    PID_SEX_OR_GENDER = 'P21'
    PID_COUNTRY_OF_CITIZENSHIP = 'P27'
    PID_DATE_OF_BIRTH = 'P569'
    PID_DATE_OF_DEATH = 'P570'
    PID_PLACE_OF_BIRTH = 'P19'
    PID_OCCUPATION = 'P106'
    PID_ETHNIC_GROUP = 'P172'
    PID_IMAGE = 'P18'
    PID_OFFICIAL_WEBSITE = 'P856'
    PID_REFERENCE_URL = 'P854'
    PID_TITLE = 'P1476'
    PID_RETRIEVED = 'P813'

# Item IDs (QIDs)
if WIKIDATA_TEST_MODE:
    # Test Wikidata items
    QID_HUMAN = 'Q224056'
else:
    # Production Wikidata items
    QID_HUMAN = 'Q5'
    
    
# Gender QIDs
if WIKIDATA_TEST_MODE:
    # Test Wikidata QIDs for genders
    FORM_GENDERS = [
        {"qid": "Q216154", "gender_name": _l("Female")},
        {"qid": "Q216156", "gender_name": _l("Male")},
        {"qid": "Q243752", "gender_name": _l("Trans man")},
        {"qid": "Q243753", "gender_name": _l("Trans woman")},
        {"qid": "Q243754", "gender_name": _l("Non-binary")}
    ]
else:
    # Production Wikidata QIDs for genders
    FORM_GENDERS = [
        {"qid": "Q6581072", "gender_name": _l("Female")},
        {"qid": "Q6581097", "gender_name": _l("Male")},
        {"qid": "Q2449503", "gender_name": _l("Trans man")},
        {"qid": "Q1052281", "gender_name": _l("Trans woman")},
        {"qid": "Q48270", "gender_name": _l("Non-binary")}
    ]


# UTILITY FUNCTIONS

def generate_author_description(nationality_label, date_of_birth=None, date_of_death=None, lang='en'):
    """
    Generate a simple standard description for an author.
    Format: "creator from {nationality} (birthDate–deathDate)" or "creator from {nationality}"
    
    Args:
        nationality_label: Human-readable nationality label
        date_of_birth: Birth date string (YYYY-MM-DD format)
        date_of_death: Death date string (YYYY-MM-DD format)
        lang: Language code for the description
    
    Returns:
        Generated description string (starts with lowercase per Wikidata rules)
    """
    # Base description 
    if nationality_label:
        description = _("creator from %(nationality)s", nationality=nationality_label)
    else:
        description = _("creator")

    # Add dates if both birth and death are present
    if date_of_birth and date_of_death:
        try:
            birth_year = date_of_birth.split('-')[0]
            death_year = date_of_death.split('-')[0]
            description += f" ({birth_year}–{death_year})" 
        except:
            pass  # Skip dates if parsing fails
    
    return description

# WIKIDATA API CLASS

class WikidataAPI:
    """Handles creating and editing Wikidata items via the Wikibase REST API"""
    
    def __init__(self, config, oauth_session=None):
        self.config = config
        self.oauth_session = oauth_session
        self.api_url = config['WIKIDATA_API_URL']  
        self.rest_api_url = config['WIKIDATA_REST_API_URL']  
        self.user_agent = config['USER_AGENT']
        
    # AUTHENTICATION
  
    def get_csrf_token(self):
        """Get CSRF token for authenticated actions."""
        if not self.oauth_session:
            raise Exception(_("No OAuth session available"))
      
        token_url = f"{self.api_url}?action=query&meta=tokens&type=csrf&format=json"
        
        try:
            headers = {'User-Agent': self.user_agent}
            
            response = self.oauth_session.get(token_url, headers=headers)
            data = response.json()
            
            # MediaWiki API returns token in query.tokens.csrftoken
            if 'query' in data and 'tokens' in data['query']:
                csrf_token = data['query']['tokens'].get('csrftoken')
                if csrf_token:
                    print(_("CSRF token obtained: %(token)s...", token=csrf_token[:20]))
                    return csrf_token
            
            raise Exception(_("Unexpected token response: %(data)s", data=str(data)))
            
        except Exception as e:
            print(_("Error getting CSRF token: %(error)s", error=str(e)))
            raise
    
    # ITEM CREATION
    
    def create_item(self, labels, descriptions, statements):
        """Create a new Wikidata item using REST API."""
        if not self.oauth_session:
            raise Exception(_("No OAuth session available"))
        
        try:
            # Group statements by property ID 
            grouped_statements = {}
            for statement in statements:
                prop_id = statement['property']['id']
                if prop_id not in grouped_statements:
                    grouped_statements[prop_id] = []
                grouped_statements[prop_id].append(statement)
            
            # Build item data structure with correct REST API format
            item_data = {
                "item": {
                    "labels": labels,
                    "descriptions": descriptions,
                    "statements": grouped_statements
                },
                "comment": "using [[toolforge:paulina|Paulina]]: data for the public domain",
            }
            
            create_url = f"{self.rest_api_url}/entities/items"
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': self.user_agent
            }
            
            # Add Bearer token only for production Wikidata
            if not WIKIDATA_TEST_MODE:
                token = self.oauth_session.token
                headers['Authorization'] = f"Bearer {token['access_token']}"
            else:
                print(_("Test mode - no authentication required"))
            
            print(_("Creating item at: %(url)s", url=create_url))
            print(_("Item data: %(data)s", data=json.dumps(item_data, indent=2, ensure_ascii=False, default=str)))

            # Use regular requests for test mode, oauth_session for production
            if WIKIDATA_TEST_MODE:
                response = requests.post(create_url, json=item_data, headers=headers)
            else:
                response = self.oauth_session.post(create_url, json=item_data, headers=headers)
            
            print(_("Response status: %(status)s", status=response.status_code))
            print(_("Response body: %(body)s", body=response.text))
            
            if response.status_code in [200, 201]:
                result = response.json()
                item_id = result.get('id')
                print(_("Item created successfully: %(item_id)s", item_id=item_id))
                return {
                    'success': True,
                    'item_id': item_id,
                    'data': result
                }
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(_("Failed to create item: %(error)s", error=str(error_data)))
                return {
                    'success': False,
                    'error': error_data
                }
                
        except Exception as e:
            print(_("Exception creating item: %(error)s", error=str(e)))
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    
    # STATEMENT & VALUE BUILDERS
    
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
    
    def build_reference(self, url, title=None, retrieved_date=None):
        """
        Build a reference structure.
        
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
                'property': {'id': PID_REFERENCE_URL},
                'value': {'type': 'value', 'content': url}
            })
        
        if title:
            parts.append({
                'property': {'id': PID_TITLE},
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
                'property': {'id': PID_RETRIEVED},
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
    
    
    # AUTHOR FORM PROCESSING
    
    def process_author_form(self, form_data, current_lang='en'):
        """
        Processing of author form - validation, building labels/descriptions/statements.
        
        Args:
            form_data: Flask request.form object
            current_lang: Current language code for labels/descriptions
        
        Returns:
            dict with 'success', 'item_id' or 'errors'
        """
        # Validate
        is_valid, errors = self.validate_author_form_data(form_data)
        if not is_valid:
            return {'success': False, 'errors': errors}
        
        # Extract form data
        name = form_data.get('name', '').strip()
        description = form_data.get('description', '').strip()
        nationality_label = form_data.get('nationality', '').strip()
        date_of_birth = form_data.get('dateOfBirth', '').strip()
        date_of_death = form_data.get('dateOfDeath', '').strip()
        
        # Handle description
        if description:
            description = description
        else:
            description = generate_author_description(
                nationality_label,
                date_of_birth,
                date_of_death,
                current_lang
            )
        
        # Build labels and descriptions
        labels = {current_lang: name}
        descriptions = {current_lang: description} if description else {}
        
        # Build statements
        statements = self.build_author_statements_from_form(form_data)
        
        # Create the item
        result = self.create_item(labels, descriptions, statements)
        
        return result
    
    def validate_author_form_data(self, form_data):
        """
        Validate required fields for author creation.
        
        Args:
            form_data: Flask request.form object
        
        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []
        
        #Required fields
        if not form_data.get('name', '').strip():
            errors.append(_('Name is required'))
        if not form_data.get('genderQid', '').strip():
            errors.append(_('Gender is required'))
        if not form_data.get('nationalityQid', '').strip():
            errors.append(_('Nationality is required'))
        if not form_data.get('placeOfBirthQid', '').strip():
            errors.append(_('Place of birth is required'))
        if not form_data.get('occupationQids', '').strip():
            errors.append(_('Occupation is required'))
            
        # Validate date formats
        date_of_birth = form_data.get('dateOfBirth', '').strip()
        if date_of_birth:
            is_valid, error_msg = self.validate_date_format(date_of_birth)
            if not is_valid:
                errors.append(_('Date of birth: %(error)s', error=error_msg))
        
        date_of_death = form_data.get('dateOfDeath', '').strip()
        if date_of_death:
            is_valid, error_msg = self.validate_date_format(date_of_death)
            if not is_valid:
                errors.append(_('Date of death: %(error)s', error=error_msg))
            
        return len(errors) == 0, errors

    def collect_references_from_form(self, field_id, form_data):
        """
        Collect references for a specific field from form data.
        
        Args:
            field_id: The field identifier (e.g., 'author-gender', 'author-nationality')
            form_data: Flask request.form object
        
        Returns:
            List of reference dicts or None if no references
        """
        references = []
        
        # Check for up to 3 references per field
        for i in range(3):
            url = form_data.get(f'{field_id}_ref_url_{i}', '').strip()
            title = form_data.get(f'{field_id}_ref_title_{i}', '').strip()
            retrieved = form_data.get(f'{field_id}_ref_retrieved_{i}', '').strip()
            
            if url:
                # Auto-prepend https:// if protocol is missing
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                ref = self.build_reference(url, title, retrieved)
                references.append(ref)
        
        return references if references else None

    def build_author_statements_from_form(self, form_data):
        """
        Build all Wikidata statements for an author from form data.
        Uses constants that adapt to test/production mode.
        
        Args:
            form_data: Flask request.form object
        
        Returns:
            List of statement dictionaries
        """
        statements = []
        
        # Instance of: Human (Q5) - Required
        statements.append(
            self.build_statement(PID_INSTANCE_OF, QID_HUMAN, 'wikibase-item')
        )
        
        # Gender
        gender = form_data.get('genderQid', '').strip()
        if gender:
            refs = self.collect_references_from_form('author-gender', form_data)
            statements.append(
                self.build_statement(PID_SEX_OR_GENDER, gender, 'wikibase-item', refs)
            )
        
        # Nationality
        nationality = form_data.get('nationalityQid', '').strip()
        if nationality:
            refs = self.collect_references_from_form('author-nationality', form_data)
            statements.append(
                self.build_statement(PID_COUNTRY_OF_CITIZENSHIP, nationality, 'wikibase-item', refs)
            )
        
        # Place of birth
        place_of_birth = form_data.get('placeOfBirthQid', '').strip()
        if place_of_birth:
            refs = self.collect_references_from_form('author-place-of-birth', form_data)
            statements.append(
                self.build_statement(PID_PLACE_OF_BIRTH, place_of_birth, 'wikibase-item', refs)
            )
        
        # Date of birth
        date_of_birth = form_data.get('dateOfBirth', '').strip()
        if date_of_birth:
            refs = self.collect_references_from_form('author-date-of-birth', form_data)
            statements.append(
                self.build_statement(PID_DATE_OF_BIRTH, date_of_birth, 'time', refs)
            )
        
        # Date of death
        date_of_death = form_data.get('dateOfDeath', '').strip()
        if date_of_death:
            refs = self.collect_references_from_form('author-date-of-death', form_data)
            statements.append(
                self.build_statement(PID_DATE_OF_DEATH, date_of_death, 'time', refs)
            )
        
        # Occupations - can be multiple
        occupation = form_data.get('occupationQids', '').strip()
        if occupation:
            refs = self.collect_references_from_form('author-occupation', form_data)
            for qid in occupation.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        self.build_statement(PID_OCCUPATION, qid, 'wikibase-item', refs)
                    )
        
        # Ethnicity
        ethnicity = form_data.get('ethnicityQid', '').strip()
        if ethnicity:
            refs = self.collect_references_from_form('author-ethnicity', form_data)
            statements.append(
                self.build_statement(PID_ETHNIC_GROUP, ethnicity, 'wikibase-item', refs)
            )
        
        # Image
        image_url = form_data.get('imageUrl', '').strip()
        if image_url:
            filename = self.extract_commons_filename(image_url)
            if filename:
                statements.append(
                    self.build_statement(PID_IMAGE, filename, 'commonsMedia')
                )
        
        # Official website
        official_website = form_data.get('officialWebsite', '').strip()
        if official_website:
            if not official_website.startswith(('http://', 'https://')):
                official_website = 'https://' + official_website
            statements.append(
                self.build_statement(PID_OFFICIAL_WEBSITE, official_website, 'url')
            )
        
        return statements
    
    # HELPER METHODS
    
    def _format_date(self, date_string):
        """
        Convert date string (YYYY-MM-DD) to Wikidata format.
        Handles less precise dates (YYYY-00-00, YYYY-MM-00, etc.)
        """
        if not date_string:
            return None
        
        parts = date_string.split('-')
        year = parts[0] if len(parts) > 0 else '0000'
        month = parts[1] if len(parts) > 1 and parts[1] else '00'
        day = parts[2] if len(parts) > 2 and parts[2] else '00'
        
        # Ensure zero-padding
        year = year.zfill(4)
        month = month.zfill(2)
        day = day.zfill(2)
        
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
    
    def validate_date_format(self, date_string):
        """
        Validate date format and check for invalid placeholders.

        Args:
            date_string: Date in YYYY-MM-DD format

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not date_string:
            return True, None

        # Check for invalid placeholders
        invalid_patterns = ['yyyy', 'mm', 'dd', 'YYYY', 'MM', 'DD']
        for pattern in invalid_patterns:
            if pattern in date_string.lower():
                return False, _("Invalid date: contains '%(pattern)s'", pattern=pattern)

        parts = date_string.split('-')

        # Must have at least year
        if len(parts) < 1:
            return False, _("Invalid date format")

        year = parts[0] if len(parts) > 0 else ''
        month = parts[1] if len(parts) > 1 else '00'
        day = parts[2] if len(parts) > 2 else '00'

        # Year is required and must be valid
        if not year or year == '0000' or not year.isdigit() or len(year) != 4:
            return False, _("Year is required and must be a valid 4-digit number")

        # If month is provided, it must be valid 
        if month and month != '00':
            if not month.isdigit() or int(month) < 1 or int(month) > 12:
                return False, _("Invalid month: %(month)s. Must be 01-12 or 00 for unknown", month=month)

        # If day is provided, it must be valid 
        if day and day != '00':
            if not day.isdigit() or int(day) < 1 or int(day) > 31:
                return False, _("Invalid day: %(day)s. Must be 01-31 or 00 for unknown", day=day)

        return True, None
    
    def extract_commons_filename(self, url):
        """Extract filename from Commons URL"""
        if not url:
            return None
        
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