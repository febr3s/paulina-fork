"""
Wikidata API Helper Module
Handles creating and editing Wikidata items via the Wikibase REST API
and utility functions
"""
import json
import requests
import traceback
import urllib.parse as urlparse
from flask_babel import gettext as _ 

# Import Wikidata constants
from wikidata_constants import (
    WIKIDATA_TEST_MODE,
    PID_INSTANCE_OF,
    PID_SEX_OR_GENDER,
    PID_COUNTRY_OF_CITIZENSHIP,
    PID_DATE_OF_BIRTH,
    PID_DATE_OF_DEATH,
    PID_PLACE_OF_BIRTH,
    PID_OCCUPATION,
    PID_ETHNIC_GROUP,
    PID_IMAGE,
    PID_OFFICIAL_WEBSITE,
    PID_REFERENCE_URL,
    PID_RETRIEVED,
    PID_AUTHOR,
    PID_LANGUAGE,
    PID_COUNTRY_OF_ORIGIN,
    PID_PUBLICATION_DATE,
    PID_INCEPTION,
    PID_FULL_WORK_URL,
    PID_INTERNET_ARCHIVE,
    QID_HUMAN,
    PID_DIRECTOR,
    PID_SCREENWRITER,
    PID_COMPOSER,
    PID_CREATOR,
    PID_LYRICIST,
    PID_LOCATION,
    PID_LANGUAGE_FILM,
    PID_PERFORMER,
    PID_PRODUCER,
    PID_GENRE,
    PID_RECORD_LABEL,
    PID_COUNTRY_OF_PUBLICATION,
    WORK_TYPES,
)

# Edit comment for Wikidata
edit_comment = "using [[toolforge:paulina|Paulina]]: data for the public domain"

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
                    print(f"CSRF token obtained: {csrf_token[:20]}...")
                    return csrf_token
            
            raise Exception(_("Unexpected token response: %(data)s", data=str(data)))
            
        except Exception as e:
            print(f"Error getting CSRF token: {e}")
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
                "comment": edit_comment,
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
                print(f"Test mode - no authentication required")
            
            print(f"Creating item at: {create_url}")
            print(f"Item data: {json.dumps(item_data, indent=2, ensure_ascii=False, default=str)}")

            # Use regular requests for test mode, oauth_session for production
            if WIKIDATA_TEST_MODE:
                response = requests.post(create_url, json=item_data, headers=headers)
            else:
                response = self.oauth_session.post(create_url, json=item_data, headers=headers)
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                item_id = result.get('id')
                print(f"Item created successfully: {item_id}")
                return {
                    'success': True,
                    'item_id': item_id,
                    'data': result
                }
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"Failed to create item: {error_data}")
                return {
                    'success': False,
                    'error': error_data
                }
                
        except Exception as e:
            print(f"Exception creating item: {e}")
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
    
    def build_reference(self, url, retrieved_date=None):
        """
        Build a reference structure.
        
        Args:
            url: Reference URL
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
            retrieved = form_data.get(f'{field_id}_ref_retrieved_{i}', '').strip()
            
            if url:
                # Auto-prepend https:// if protocol is missing
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                ref = self.build_reference(url, retrieved)
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
    
    # WORK FORM PROCESSING
    
    def process_work_form(self, form_data, current_lang='en'):
        """
        Processing of work form - validation, building labels/descriptions/statements.
        
        Args:
            form_data: Flask request.form object
            current_lang: Current language code for labels/descriptions
        
        Returns:
            dict with 'success', 'item_id' or 'errors'
        """
        # Validate
        is_valid, errors = self.validate_work_form_data(form_data)
        if not is_valid:
            return {'success': False, 'errors': errors}
        
        # Extract form data
        title = form_data.get('title', '').strip()
        description = form_data.get('description', '').strip()
        
        # Generate description if not provided
        if not description:
            # Get work type
            instance_of_qid = form_data.get('instanceOfQid', '').strip()
            work_type_config = None
            
            # Find the work type configuration
            for wt in WORK_TYPES:
                if wt['qid'] == instance_of_qid:
                    work_type_config = wt
                    break
            
            if work_type_config:
                work_type_label = work_type_config['type_name']
                creator_property = work_type_config['creator_property']
                
                # Get creator label(s) from the required creator field
                # Map creator property name to form field name
                creator_field_mapping = {
                    'author': 'authorQids',
                    'director': 'directorQids',
                    'creator': 'creatorQids',
                    'composer': 'composerQids',
                    'performer': 'performerQids'
                }
                
                creator_form_field = creator_field_mapping.get(creator_property)
                creator_labels_field = creator_form_field.replace('Qids', 'Labels') if creator_form_field else None

                creator_label = None
                if creator_labels_field:
                    creator_labels_str = form_data.get(creator_labels_field, '').strip()
                    if creator_labels_str:
                        creator_names = [name.strip() for name in creator_labels_str.split(',') if name.strip()]
                        
                        # Format the creator label based on count
                        if len(creator_names) == 1:
                            creator_label = creator_names[0]
                        elif len(creator_names) == 2:
                            creator_label = f"{creator_names[0]} and {creator_names[1]}"
                        elif len(creator_names) > 2:
                            # For 3+ creators: "Name1, Name2 and Name3"
                            all_but_last = ', '.join(creator_names[:-1])
                            creator_label = f"{all_but_last} and {creator_names[-1]}"
                
                # Get creation/publication date
                creation_date = (form_data.get('publicationDate', '').strip() or 
                                form_data.get('creationDate', '').strip())
                
                # Generate description
                description = generate_work_description(
                    work_type_label,
                    creator_label,
                    creation_date,
                    current_lang
                )
            else:
                # Fallback if work type not found
                description = _("work")
    
        # Build labels and descriptions
        labels = {current_lang: title}
        descriptions = {current_lang: description} if description else {}
        
        # Build statements
        statements = self.build_work_statements_from_form(form_data)
        
        # Create the item
        result = self.create_item(labels, descriptions, statements)
        
        return result

    def validate_work_form_data(self, form_data, current_lang='en'):
        """
        Validate required fields for work creation based on work type.
        
        Args:
            form_data: Flask request.form object
            current_lang: Current language code for error messages
        
        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []
        
        # Title is always required
        if not form_data.get('title', '').strip():
            errors.append(_('Title is required'))
        
        # Type of work is always required
        instance_of_qid = form_data.get('instanceOfQid', '').strip()
        if not instance_of_qid:
            errors.append(_('Type of work is required'))
            return False, errors
        
        # Find the work type configuration
        work_type_config = None
        for wt in WORK_TYPES:
            if wt['qid'] == instance_of_qid:
                work_type_config = wt
                break
        
        if not work_type_config:
            errors.append(_('Invalid type of work selected'))
            return False, errors
        
        # Get required fields for this work type
        required_fields = work_type_config['fields']['required']
        
        # Field name mapping to form field names and display names
        field_mapping = {
            'author': ('authorQids', _('Author')),
            'director': ('directorQids', _('Director')),
            'creator': ('creatorQids', _('Creator')),
            'composer': ('composerQids', _('Composer')),
            'screenwriter': ('screenwriterQids', _('Screenwriter')),
            'lyricist': ('lyricistQids', _('Lyricist')),
            'performer': ('performerQids', _('Performer')),  
            'producer': ('producerQids', _('Producer')),  
            'language': ('languageQid', _('Language')),
            'languageFilm': ('languageFilmQid', _('Original language')),
            'country': ('countryQid', _('Country of origin')),
            'countryOfPublication': ('countryOfPublicationQid', _('Country of publication')), 
            'location': ('locationQid', _('Location')),
            'genre': ('genreQid', _('Genre')),  
            'recordLabel': ('recordLabelQid', _('Record label')), 
            'publicationDate': ('publicationDate', _('Publication date')),
            'creationDate': ('creationDate', _('Creation date')),
        }
        
        # Validate required fields
        for field in required_fields:
            if field in field_mapping:
                form_field_name, display_name = field_mapping[field]
                if not form_data.get(form_field_name, '').strip():
                    errors.append(_('%(field)s is required', field=display_name))
        
        # Validate date formats
        publication_date = form_data.get('publicationDate', '').strip()
        if publication_date:
            is_valid, error_msg = self.validate_date_format(publication_date)
            if not is_valid:
                errors.append(_('Publication date: %(error)s', error=error_msg))

        creation_date = form_data.get('creationDate', '').strip()
        if creation_date:
            is_valid, error_msg = self.validate_date_format(creation_date)
            if not is_valid:
                errors.append(_('Creation date: %(error)s', error=error_msg))
        
        return len(errors) == 0, errors

    def build_work_statements_from_form(self, form_data):
        """
        Build all Wikidata statements for a work from form data.
        Handles multiple creator types (author, director, composer, etc.)
        Uses constants that adapt to test/production mode.
        
        Args:
            form_data: Flask request.form object
        
        Returns:
            List of statement dictionaries
        """
        statements = []
        
        # Instance of (type of work) - Required
        instance_of = form_data.get('instanceOfQid', '').strip()
        if instance_of:
            refs = self.collect_references_from_form('work-type-select', form_data)
            statements.append(
                self.build_statement(PID_INSTANCE_OF, instance_of, 'wikibase-item', refs)
            )
        
        # Authors (P50) - Literary works
        authors = form_data.get('authorQids', '').strip()
        if authors:
            refs = self.collect_references_from_form('work-author', form_data)
            for qid in authors.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        self.build_statement(PID_AUTHOR, qid, 'wikibase-item', refs)
                    )
        
        # Directors (P57) - Films/Audiovisual
        directors = form_data.get('directorQids', '').strip()
        if directors:
            refs = self.collect_references_from_form('work-director', form_data)
            for qid in directors.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        self.build_statement(PID_DIRECTOR, qid, 'wikibase-item', refs)
                    )
        
        # Creators (P170) - Visual arts
        creators = form_data.get('creatorQids', '').strip()
        if creators:
            refs = self.collect_references_from_form('work-creator', form_data)
            for qid in creators.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        self.build_statement(PID_CREATOR, qid, 'wikibase-item', refs)
                    )
        
        # Composers (P86) - Music/Films
        composers = form_data.get('composerQids', '').strip()
        if composers:
            refs = self.collect_references_from_form('work-composer', form_data)
            for qid in composers.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        self.build_statement(PID_COMPOSER, qid, 'wikibase-item', refs)
                    )
        
        # Screenwriters (P58) - Films (optional)
        screenwriters = form_data.get('screenwriterQids', '').strip()
        if screenwriters:
            refs = self.collect_references_from_form('work-screenwriter', form_data)
            for qid in screenwriters.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        self.build_statement(PID_SCREENWRITER, qid, 'wikibase-item', refs)
                    )
        
        # Lyricists (P676) - Music (optional)
        lyricists = form_data.get('lyricistQids', '').strip()
        if lyricists:
            refs = self.collect_references_from_form('work-lyricist', form_data)
            for qid in lyricists.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        self.build_statement(PID_LYRICIST, qid, 'wikibase-item', refs)
                    )
        
        # Performers (P175) - Albums
        performers = form_data.get('performerQids', '').strip()
        if performers:
            refs = self.collect_references_from_form('work-performer', form_data)
            for qid in performers.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        self.build_statement(PID_PERFORMER, qid, 'wikibase-item', refs)
                    )
        
        # Producers (P162) - Albums/Films
        producers = form_data.get('producerQids', '').strip()
        if producers:
            refs = self.collect_references_from_form('work-producer', form_data)
            for qid in producers.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        self.build_statement(PID_PRODUCER, qid, 'wikibase-item', refs)
                    )
        
        # Language (P407) - Literary/Music works
        language = form_data.get('languageQid', '').strip()
        if language:
            refs = self.collect_references_from_form('work-language', form_data)
            statements.append(
                self.build_statement(PID_LANGUAGE, language, 'wikibase-item', refs)
            )
        
        # Language (Film) (P364) - Films/Audiovisual
        language_film = form_data.get('languageFilmQid', '').strip()
        if language_film:
            refs = self.collect_references_from_form('work-language-film', form_data)
            statements.append(
                self.build_statement(PID_LANGUAGE_FILM, language_film, 'wikibase-item', refs)
            )
        
        # Country of origin (P495)
        country = form_data.get('countryQid', '').strip()
        if country:
            refs = self.collect_references_from_form('work-country', form_data)
            statements.append(
                self.build_statement(PID_COUNTRY_OF_ORIGIN, country, 'wikibase-item', refs)
            )
        
        # Location (P276) - Visual arts
        location = form_data.get('locationQid', '').strip()
        if location:
            refs = self.collect_references_from_form('work-location', form_data)
            statements.append(
                self.build_statement(PID_LOCATION, location, 'wikibase-item', refs)
            )
        
        # Publication date (P577)
        publication_date = form_data.get('publicationDate', '').strip()
        if publication_date:
            refs = self.collect_references_from_form('work-publication-date', form_data)
            statements.append(
                self.build_statement(PID_PUBLICATION_DATE, publication_date, 'time', refs)
            )
        
        # Creation date (P571)
        creation_date = form_data.get('creationDate', '').strip()
        if creation_date:
            refs = self.collect_references_from_form('work-creation-date', form_data)
            statements.append(
                self.build_statement(PID_INCEPTION, creation_date, 'time', refs)
            )
        
        # Genre (P136) - Albums/Music
        genre = form_data.get('genreQid', '').strip()
        if genre:
            refs = self.collect_references_from_form('work-genre', form_data)
            statements.append(
                self.build_statement(PID_GENRE, genre, 'wikibase-item', refs)
            )

        # Record Label (P264) - Albums
        record_label = form_data.get('recordLabelQid', '').strip()
        if record_label:
            refs = self.collect_references_from_form('work-record-label', form_data)
            statements.append(
                self.build_statement(PID_RECORD_LABEL, record_label, 'wikibase-item', refs)
            )

        # Country of Publication (P291) - Albums  
        country_of_publication = form_data.get('countryOfPublicationQid', '').strip()
        if country_of_publication:
            refs = self.collect_references_from_form('work-country-publication', form_data)
            statements.append(
                self.build_statement(PID_COUNTRY_OF_PUBLICATION, country_of_publication, 'wikibase-item', refs)
            )
        
        # Image
        image_url = form_data.get('imageUrl', '').strip()
        if image_url:
            filename = self.extract_commons_filename(image_url)
            if filename:
                statements.append(
                    self.build_statement(PID_IMAGE, filename, 'commonsMedia')
                )
        
        # Full work URL
        full_work_url = form_data.get('fullWorkUrl', '').strip()
        if full_work_url:
            if not full_work_url.startswith(('http://', 'https://')):
                full_work_url = 'https://' + full_work_url
            statements.append(
                self.build_statement(PID_FULL_WORK_URL, full_work_url, 'url')
            )
        
        # Internet Archive ID
        internet_archive_id = form_data.get('internetArchiveId', '').strip()
        if internet_archive_id:
            statements.append(
                self.build_statement(PID_INTERNET_ARCHIVE, internet_archive_id, 'string')
            )
        
        return statements
    
    
    # AUTHOR UPDATE PROCESSING

    def update_author_field(self, author_id, property_id, value, field_name, is_date=False, is_multi_select=False):
        """
        Update a single author field on Wikidata.
        
        Args:
            author_id: Wikidata item ID (e.g., 'Q123')
            property_id: Wikidata property ID (e.g., 'P106')
            value: New value (QID for items, date string for dates, comma-separated QIDs for multi-select)
            field_name: Field identifier for error messages
            is_date: Whether this is a date field
            is_multi_select: Whether this is a multi-select field (e.g., occupation)
        
        Returns:
            dict with 'success' and optional 'error' key
        """
        try:
            # Get existing item data to find statement IDs
            item_url = f"{self.rest_api_url}/entities/items/{author_id}"
            item_response = self.oauth_session.get(
                item_url,
                headers={'User-Agent': self.user_agent}
            )
            
            if item_response.status_code != 200:
                return {
                    'success': False,
                    'error': _('Could not retrieve author data from Wikidata.')
                }
            
            item_data = item_response.json()
            existing_statements = item_data.get('statements', {})
            existing_property_statements = existing_statements.get(property_id, [])
            
            if is_multi_select:
                # For multi-select: replace all existing statements with new ones
                # First, delete all existing statements
                for stmt in existing_property_statements:
                    statement_id = stmt.get('id')
                    if statement_id:
                        delete_url = f"{self.rest_api_url}/statements/{statement_id}"
                        delete_params = {'comment': edit_comment}
                        self.oauth_session.delete(
                            delete_url,
                            params=delete_params,
                            headers={'User-Agent': self.user_agent}
                        )
                
                # Add new statements for each value
                qids = [qid.strip() for qid in value.split(',') if qid.strip()]
                for qid in qids:
                    statement = self.build_statement(
                        property_id,
                        qid,
                        'wikibase-item'
                    )
                    
                    add_url = f"{self.rest_api_url}/entities/items/{author_id}/statements"
                    add_data = {
                        'statement': statement,
                        'comment': edit_comment
                    }
                    response = self.oauth_session.post(
                        add_url,
                        json=add_data,
                        headers={
                            'Content-Type': 'application/json',
                            'User-Agent': self.user_agent
                        }
                    )
                    
                    if response.status_code not in [200, 201]:
                        return {
                            'success': False,
                            'error': _('Failed to add statement: %(error)s', error=response.text)
                        }
                
                return {'success': True}
                
            elif existing_property_statements:
                # Single-value property with existing statement - update it
                statement_id = existing_property_statements[0].get('id')
                
                if is_date:
                    new_value = self._build_value(value, 'time')
                else:
                    new_value = self._build_value(value, 'wikibase-item')
                
                # Use PATCH to update the statement value
                patch_url = f"{self.rest_api_url}/statements/{statement_id}"
                patch_data = {
                    'patch': [
                        {
                            'op': 'replace',
                            'path': '/value',
                            'value': new_value
                        }
                    ],
                    'comment': edit_comment
                }
                
                response = self.oauth_session.patch(
                    patch_url,
                    json=patch_data,
                    headers={
                        'Content-Type': 'application/json-patch+json',
                        'User-Agent': self.user_agent
                    }
                )
                
                if response.status_code == 200:
                    return {'success': True}
                else:
                    return {
                        'success': False,
                        'error': _('Failed to update statement: %(error)s', error=response.text)
                    }
                    
            else:
                # No existing statement - create new one
                if is_date:
                    statement = self.build_statement(property_id, value, 'time')
                else:
                    statement = self.build_statement(property_id, value, 'wikibase-item')
                
                add_url = f"{self.rest_api_url}/entities/items/{author_id}/statements"
                add_data = {
                    'statement': statement,
                    'comment': edit_comment
                }
                response = self.oauth_session.post(
                    add_url,
                    json=add_data,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': self.user_agent
                    }
                )
                
                if response.status_code in [200, 201]:
                    return {'success': True}
                else:
                    return {
                        'success': False,
                        'error': _('Failed to add statement: %(error)s', error=response.text)
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
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
        
        if 'upload.wikimedia.org' in url and '/thumb/' not in url:
            # Format: https://upload.wikimedia.org/wikipedia/commons/a/ab/Filename.jpg
            parts = url.split('/')
            if len(parts) > 0:
                return urlparse.unquote(parts[-1])
        
        elif 'upload.wikimedia.org' in url and '/thumb/' in url:
            # Format: https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Filename.jpg/500px-Filename.jpg
            parts = url.split('/')
            if len(parts) > 0:
                return urlparse.unquote(parts[-2])
        
        elif 'commons.wikimedia.org/wiki/File:' in url:
            # Format: https://commons.wikimedia.org/wiki/File:Filename.jpg
            filename = url.split('File:')[-1]
            return urlparse.unquote(filename.split('?')[0])
        
        elif 'Special:Redirect/file/' in url:
            # Format: https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/Filename.jpg&width=400&height=200
            filename = url.split('/')[-1]
            return urlparse.unquote(filename.split('&')[0])
        
        return None
    


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

def generate_work_description(work_type_label, creator_label, creation_date=None, lang='en'):
    """
    Generate a simple standard description for a work.
    Format: "{work_type} by {creator}" or "{work_type} by {creator} (year)"
    
    Args:
        work_type_label: Human-readable work type label (e.g., "literary work", "film", "painting")
        creator_label: Human-readable creator name(s) (can be multiple, comma-separated)
        creation_date: Creation/publication date string in YYYY-MM-DD format (optional)
        lang: Language code for the description
    
    Returns:
        Generated description string 
    """
    # Base description with work type and creator(s)
    if creator_label:
        description = _("%(work_type)s by %(creator)s", 
                       work_type=work_type_label, 
                       creator=creator_label)
    else:
        description = work_type_label.lower()
    
    # Add creation year if present
    if creation_date:
        try:
            year = creation_date.split('-')[0]
            if year and year != '0000':
                description += f" ({year})"
        except:
            pass  # Skip date if parsing fails
    
    return description