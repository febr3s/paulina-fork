from flask import Flask, render_template, request, redirect, Response, url_for, abort, flash, session, jsonify
from flask_caching import Cache
from flask_babel import Babel, _, get_locale
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from requests_oauthlib import OAuth2Session
import datetime
import requests
import os
import sys
import time
import traceback

# Local modules
import pdclasses
import search
import languages
import squeries
import filters
import oauth

# Determine Wikidata mode from  environment
if 'test' in sys.argv:
    os.environ['WIKIDATA_TEST_MODE'] = 'true'
    print("* Paulina running in TEST mode")
    print("* https://test.wikidata.org")
else:
    os.environ['WIKIDATA_TEST_MODE'] = 'false'
    print("* Paulina running in PRODUCTION mode")
    print("* https://www.wikidata.org")
        
WIKIDATA_TEST_MODE = os.environ.get('WIKIDATA_TEST_MODE', 'false').lower() == 'true'

import wikidata_api
from wikidata_constants import FORM_GENDERS, WORK_TYPES


# Configure Wikidata API URLs based on mode
if WIKIDATA_TEST_MODE:
    WIKIDATA_API_URL = 'https://test.wikidata.org/w/api.php'
    WIKIDATA_REST_API_URL = 'https://test.wikidata.org/w/rest.php/wikibase/v1'
else:
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


app = Flask(__name__)

# Load user config
app.config.from_pyfile('config.py')

# Add config settings to app.config
app.config['WIKIDATA_TEST_MODE'] = WIKIDATA_TEST_MODE
app.config['WIKIDATA_API_URL'] = WIKIDATA_API_URL
app.config['WIKIDATA_REST_API_URL'] = WIKIDATA_REST_API_URL
app.config['AUTHORIZATION_BASE_URL'] = AUTHORIZATION_BASE_URL
app.config['TOKEN_URL'] = TOKEN_URL
app.config['PROFILE_URL'] = PROFILE_URL
app.config['OAUTH_SCOPES'] = OAUTH_SCOPES
app.config['RATELIMIT_STORAGE_URL'] = RATELIMIT_STORAGE_URL
app.config['RATELIMIT_HEADERS_ENABLED'] = RATELIMIT_HEADERS_ENABLED


# Disable OAuth 2.0 HTTPS requirement for local development only
if app.config.get('DEBUG', False):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# i18n configuration

"""config.py contains the key for the session cookie.
The session cookie is required to store the language choice 
in the session and make it persistent."""


babel = Babel(app, locale_selector=languages.get_locale)  # Initializes Babel


# Cache configuration
app.config.update(CACHE_TYPE="SimpleCache",
                  CACHE_DEFAULT_TIMEOUT=300)

cache = Cache(app)  # Initializes Flask-Caching

@app.before_request  # Necessary to add language to request context
def before_request():
    setattr(request, "language", languages.get_locale())

def make_cache_key(*args, **kwargs) -> str:
   """Creates a cache key combining the request path and the locale."""
   request_language = request.language
   request_path = request.path
   request_args = {key:value for key, value in request.args.items() if key!= "language"}   
   return f"{request_language}, {request_path}, {request_args}"

def user_is_logged_in() -> bool:
    """Checks if the user is logged in"""
    return 'wikimedia_username' in session

# Initialize Rate Limiter
def get_user_identifier():
    """Get user identifier for rate limiting (Wikimedia user ID or IP)"""
    if 'wikimedia_userid' in session:
        return f"user:{session['wikimedia_userid']}"
    return get_remote_address()

limiter = Limiter(
    app=app,
    key_func=get_user_identifier,
    storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://'),
    headers_enabled=app.config.get('RATELIMIT_HEADERS_ENABLED', True)
)


# End of app and module configuration


def print_field(field: str | dict | None) -> str:
    """Takes a value of different possible types and converts it to a meaningful string to print on the screen"""
    if field is None:
        return ""
    elif field == "novalue":
        return _("No value")
    elif field == "somevalue":
        return _("Unknown value")
    elif isinstance(field, dict) and field.get("date string"):  # For dates from pdclasses.build_date
        return field["date string"]
    else:
        return field


@app.route("/")
def home():
    return render_template("home.html",
                           title=_("Home")
                           )


@app.route("/about/")
def about():
    return render_template("about.html",
                           title=_("About")
                           )


@app.route("/results")
def results():
    try:
        type_of_search = request.args.get("type_of_search")
        search_request = request.args.get("query")
        language = request.args.get("language")
        page = request.args.get("page", 1, type=int)

        # Ensure page is at least 1
        if page < 1:
            page = 1

        # Calculate offset for pagination (50 items per page)
        page_size = 50
        offset = (page - 1) * page_size

        # Show results when there is no query (for example in case of changing the language)
        if search_request is None:
            referer = request.headers.get('Referer')
            if referer is not None:
                if referer.startswith(url_for('home', _external=True)):
                    query_parameters = referer.split("?")[-1].split("&")
                    query_parameters_without_language = [parameter for parameter in query_parameters
                                                          if not parameter.startswith("language=")]
                    path_string = "&".join(query_parameters_without_language)
                    return redirect(url_for('results') + "?" + path_string + "&" + "language=" + language )
                else:
                    return redirect(url_for('home'))
            else:
                return redirect(url_for('home'))

        if type_of_search == "author":
            gender = request.args.get("gender")
            nationality = request.args.get("nationality")
            creative_area = request.args.get("creative_area")
            in_public_domain = request.args.get("in_public_domain")
            search_result, complete, continue_offset, results_quantity = search.search_author(search_request, gender, nationality,
                                                           creative_area, in_public_domain, offset)
            if results_quantity > 10000:
                results_quantity = 10000
            
            page_range = {"start": offset + 1,
                          "end": offset + page_size if (offset + page_size) <= results_quantity else results_quantity}

            if len(search_result) > 0:
                # Calculate pagination info
                has_next = continue_offset is not None
                has_prev = page > 1
                return render_template('results.html',
                                        title=_("Results"),
                                        list_of_authors=search_result,
                                        search_request=search_request,
                                        type_of_search=type_of_search,
                                        complete=complete,
                                        results_quantity=results_quantity,
                                        page_range=page_range,
                                        page=page,
                                        has_next=has_next,
                                        has_prev=has_prev)
            else:
                return render_template("no-results.html",
                                        title=_("No results found"),
                                        search_request=search_request,
                                        type_of_search=type_of_search)
        elif type_of_search == "work":
            type_of_work = request.args.get("type_of_work")
            country_of_origin = request.args.get("country_of_origin")
            search_result, complete, continue_offset, results_quantity = search.search_work(search_request, type_of_work, 
                                                                                            country_of_origin, offset)
            if results_quantity > 10000:
                results_quantity = 10000
            
            page_range = {"start": offset + 1,
                          "end": offset + page_size if (offset + page_size) <= results_quantity else results_quantity}

            if len(search_result) > 0:
                # Calculate pagination info
                has_next = continue_offset is not None
                has_prev = page > 1
                return render_template('results.html',
                                        title=_("Results"),
                                        list_of_works=search_result,
                                        search_request=search_request,
                                        type_of_search=type_of_search,
                                        complete=complete,
                                        results_quantity=results_quantity,
                                        page_range=page_range,
                                        page=page,
                                        has_next=has_next,
                                        has_prev=has_prev)
            else:
                return render_template("no-results.html",
                                        title=_("No results found"),
                                        search_request=search_request,
                                        type_of_search=type_of_search)
        else:
            return render_template("no-results.html",
                                        title=_("No results found"),
                                        search_request=search_request)
    except:
        abort(404)
        

@app.route("/author/<author_data>")
@cache.cached(make_cache_key=make_cache_key, unless=user_is_logged_in)  # Prevent caching if user is logged in
def author_page(author_data):
    try:
        author = pdclasses.Author(author_data)
        edit_eligibility = pdclasses.get_author_field_edit_eligibility(author.wikidata_item)
        
        # Convert dates to ISO format for date inputs
        author_date_of_birth_iso = None
        if author.date_of_birth and isinstance(author.date_of_birth.get('date object'), datetime.date):
            author_date_of_birth_iso = author.date_of_birth['date object'].isoformat()
        
        author_date_of_death_iso = None
        if author.date_of_death and isinstance(author.date_of_death.get('date object'), datetime.date):
            author_date_of_death_iso = author.date_of_death['date object'].isoformat() 
        
        
        return render_template("author.html",
            title=print_field(author.name),
            author_name=print_field(author.name),
            author_id=print_field(author.wikidata_item_id),
            author_description=print_field(author.description),
            author_nationality=print_field(author.nationality),
            author_nationality_qid=author.nationality_qid, 
            author_gender=print_field(author.gender),
            author_gender_qid=author.gender_qid, 
            author_ethnicity=print_field(author.ethnicity),
            author_ethnicity_qid=author.ethnicity_qid, 
            author_date_of_birth=print_field(author.date_of_birth),  # Display format
            author_date_of_birth_iso=author_date_of_birth_iso,  # ISO format for input
            author_occupation=", ".join(print_field(author.occupation)) if isinstance(author.occupation, list) else print_field(author.occupation),
            author_occupation_qid=author.occupation_qid, 
            author_place_of_birth=print_field(author.place_of_birth),
            author_place_of_birth_qid=author.place_of_birth_qid, 
            author_country_of_birth=print_field(author.country_of_birth),
            author_country_of_birth_qid=author.country_of_birth_qid, 
            author_date_of_death=print_field(author.date_of_death),  # Display format
            author_date_of_death_iso=author_date_of_death_iso,  # ISO format for input
            author_age=print_field(author.ageOfAuthor()),
            author_image=print_field(author.image),
            author_image_link=print_field(author.image_link),
            author_image_alt_text=print_field(author.image_alt_text),
            author_wikipedia_link=print_field(author.wikipedia_link),
            author_commons_link=print_field(author.commons_link),
            author_wikisource_link=print_field(author.wikisource_link),
            author_wikiquote_link=print_field(author.wikiquote_link),
            author_official_website=print_field(author.official_website),
            author_is_in_public_domain=print_field(author.isInPublicDomain()),
            author_wikidata_link=print_field(author.wikidata_link),
            author_date_enter_public_domain=print_field(author.date_enter_public_domain),
            form_genders=FORM_GENDERS,
            edit_eligibility=edit_eligibility
        )
    except:
        abort(404)


@app.route("/works-list/<author_id>")
@cache.cached(make_cache_key=make_cache_key)
def works_list(author_id):
    try:
        page = request.args.get("page", 1, type=int)

        # Ensure page is at least 1
        if page < 1:
            page = 1

        # Calculate offset for pagination (50 items per page)
        page_size = 50
        offset = (page - 1) * page_size

        # To show the query link at the top of the results 
        query = squeries.query_for_works_by_an_author.format(qname=author_id, lang=languages.get_locale(), 
                                                             limit_clause="", offset_clause="")
        wqs_link = "https://query.wikidata.org/#" + requests.utils.quote(query)

        author = pdclasses.Author(author_id)
        author_works = author.getWorks(languages.get_locale(), limit=page_size, offset=offset)
        # Check if there are more results by trying to get one more result
        has_next = len(author.getWorks(languages.get_locale(), limit=1, offset=offset + page_size)) > 0
        has_prev = page > 1

        return render_template("works-list.html",
            title=_('List of works') + " - " + print_field(author.name),
            author_name=print_field(author.name),
            wqs_link=wqs_link,
            author_works=print_field(author_works),
            page=page,
            has_next=has_next,
            has_prev=has_prev
        )

    except:  # If the Q number doesn't match any item or the item is not about a human
        abort(404)


@app.route("/work/<work_data>")
@cache.cached(make_cache_key=make_cache_key, unless=user_is_logged_in)  # Prevent caching if user is logged in
def work_page(work_data):
    try:
        work = pdclasses.Work(work_data)
        work_edit_eligibility = pdclasses.get_work_field_edit_eligibility(work.wikidata_item)

        # Convert dates to ISO format for date inputs
        work_publication_date_iso = None
        if work.publication_date and isinstance(work.publication_date.get('date object'), datetime.date):
            work_publication_date_iso = work.publication_date['date object'].isoformat()

        work_creation_date_iso = None
        if work.creation_date and isinstance(work.creation_date.get('date object'), datetime.date):
            work_creation_date_iso = work.creation_date['date object'].isoformat()

        return render_template("work.html",
            title=print_field(work.name),
            work_id=print_field(work.wikidata_item_id),
            work_title=print_field(work.name),
            work_description=print_field(work.description),
            work_image=print_field(work.image),
            work_image_link=print_field(work.image_link),
            work_image_alt_text=print_field(work.image_alt_text),
            work_authors=print_field(work.authors),
            work_publication_date=print_field(work.publication_date),
            work_publication_date_iso=work_publication_date_iso,
            work_creation_date=print_field(work.creation_date),
            work_creation_date_iso=work_creation_date_iso,
            work_language=print_field(work.language),
            work_language_qid=work.language_qid,
            work_country=print_field(work.country_of_origin),
            work_country_qid=work.country_of_origin_qid,
            work_wikipedia_link=print_field(work.wikipedia_link),
            work_commons_link=print_field(work.commons_link),
            work_wikisource_links=print_field(work.wikisource_links),
            work_wikiquote_link=print_field(work.wikiquote_link),
            work_internet_archive_link=print_field(work.internet_archive_link),
            work_full_work_link=print_field(work.full_work_link),
            work_wikidata_link=print_field(work.wikidata_link),
            work_copyright_status=print_field(work.getCopyrightStatus()),
            work_edit_eligibility=work_edit_eligibility
        )
    except:
        abort(404)


@app.route("/country/<country_data>")
@cache.cached(timeout=86400, make_cache_key=make_cache_key)
def country_page(country_data):
    try:
        country = pdclasses.Country(country_data)
        return render_template("country.html",
            title=print_field(country.name),
            country_name=print_field(country.name),
            country_copyright_terms=print_field(country.getCopyrightTerm()),
            country_flag_image=print_field(country.flag_image),
            country_flag_image_link=print_field(country.flag_image_link),
            country_flag_image_alt_text=print_field(country.flag_image_alt_text),
            country_number_of_works_in_public_domain=print_field(country.number_of_works_in_public_domain),
            prefill_country_qid=country.wikidata_item_id
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/term/<term_id>")
@cache.cached(timeout=86400, make_cache_key=make_cache_key)
def term_page(term_id):
    try:
        term = pdclasses.Term(term_id)
        description = print_field(term.description)
        if isinstance(description, str) and description:
            description = description.capitalize() + "."
        return render_template("term.html",
            title=_('List of %(term_name)s', term_name=print_field(term.name)),
            term_name=print_field(term.name),
            term_countries=print_field(term.getCountries()),
            term_description=description,
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/countries/")
@cache.cached(timeout=86400, make_cache_key=make_cache_key)
def countries_main():
    countries_info = squeries.retrieve_query(squeries.query_for_all_countries_info, lang=languages.get_locale())
    for country in countries_info:
        if country.get('terms', {}).get('value'):
            country['terms']['value'] = country['terms']['value'].replace('countries with ', "")
        else:
            country['terms']['value'] = _("Unknown term")
    return render_template("countries.html",
                           title=_('Countries and terms'),
                           countries_info=print_field(countries_info)
                           )


@app.route("/robots.txt")
def show_robots_txt():
    ROBOTS_TXT = "User-agent: *\nCrawl-Delay: 10\n"
    return Response(ROBOTS_TXT, mimetype="text/plain")


@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now(datetime.timezone.utc)}


@app.context_processor
def inject_language():
    return {"CURRENT_LANGUAGE": languages.get_locale(),
            "TRANSLATED_LANGUAGES": languages.TRANSLATED_LANGUAGES}

@app.context_processor
def inject_filters():
    countries = [{"qid": country["qid"], 
                  "country_name": get_locale().territories.get(country["country_iso"])} 
                  for country in filters.COUNTRIES ]  # Check: North Macedonia doesn't have Asturian label in Babel
    return {        
        "GENDERS": filters.GENDERS,
        "CREATIVE_AREAS": filters.CREATIVE_AREAS,
        "TYPES_OF_WORK": filters.TYPES_OF_WORK,
        "COUNTRIES": countries
        }

@app.route('/api/search-wikidata-items')
@cache.cached(timeout=60, make_cache_key=make_cache_key)
def search_wikidata_items():
    query = request.args.get('q', '')
    
    # Get language from request, fall back to user's locale, then 'en' as default
    lang = request.args.get('lang', '')
    if not lang:
        try:
            lang = languages.get_locale()
        except:
            lang = 'en'
            
    url = app.config.get('WIKIDATA_API_URL', 'https://www.wikidata.org/w/api.php')

    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        params = {
            'action': 'wbsearchentities',
            'search': query,
            'language': lang,      # Labels in user's language
            'uselang': lang,       # UI/descriptions in user's language
            'type': 'item',
            'limit': 10,
            'format': 'json'
        }
        
        headers = {
           'User-Agent': app.config.get('USER_AGENT')
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        results = []
        for item in data.get('search', []):
            results.append({
                'id': item.get('id'),
                'label': item.get('label', ''),
                'description': item.get('description', '')
            })
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Wikidata search error: {e}")
        return jsonify([])

# OAuth Routes

@app.route('/auth/login')
@limiter.limit("5 per minute")
def login():
    """Initiate OAuth 2.0 login with Wikimedia"""
    try:
        oauth = OAuth2Session(
            app.config['CLIENT_ID'],
            redirect_uri=app.config['REDIRECT_URL'],
            scope=app.config['OAUTH_SCOPES']
        )
        
        authorization_url, state = oauth.authorization_url(
            app.config['AUTHORIZATION_BASE_URL']
        )
        
        # Store state in session for CSRF protection
        session['oauth_state'] = state
        
        return redirect(authorization_url)
    
    except Exception as e:
        traceback.print_exc()
        flash(_('Login failed. Please try again.'), 'danger')
        return redirect(url_for('home'))
    

@app.route('/oauth-callback')
def oauth_callback():
    """Handle OAuth 2.0 callback from Wikimedia"""
    try:
        # Check for errors in callback
        if 'error' in request.args:
            flash(_('Authentication failed. Please try again.'), 'danger')
            return redirect(url_for('home'))
        
        # Get state from session
        if 'oauth_state' not in session:
            flash(_('Login session expired. Please try again.'), 'warning')
            return redirect(url_for('home'))
        
        state = session.pop('oauth_state')
        
        # Verify state matches (CSRF protection)
        if state != request.args.get('state'):
            flash(_('Invalid state parameter. Please try again.'), 'danger')
            return redirect(url_for('home'))
        
        # Exchange authorization code for access token
    
        token_params = {
            'grant_type': 'authorization_code',
            'code': request.args.get('code'),
            'redirect_uri': app.config['REDIRECT_URL'],
            'client_id': app.config['CLIENT_ID'],
            'client_secret': app.config['CLIENT_SECRET']
        }
        
        token_response = requests.post(
            app.config['TOKEN_URL'],
            data=token_params,
            headers={'User-Agent': app.config.get('USER_AGENT')}
        )
        
        if token_response.status_code != 200:
            flash(_('Failed to obtain access token. Please try again.'), 'danger')
            return redirect(url_for('home'))
        
        token_data = token_response.json()
        
        # Build token dict with expiration timestamp
        token = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'token_type': token_data.get('token_type', 'Bearer'),
            'expires_in': token_data.get('expires_in', 14400),
            'expires_at': time.time() + token_data.get('expires_in', 14400)
        }
        
        # Store token in session
        session['oauth_token'] = token
        
        # Get user identity using the access token
        profile_response = requests.get(
            app.config['PROFILE_URL'],
            headers={
                'Authorization': f"Bearer {token['access_token']}",
                'User-Agent': app.config.get('USER_AGENT')
            }
        )
        
        if profile_response.status_code != 200:
            flash(_('Failed to get user profile. Please try again.'), 'danger')
            return redirect(url_for('home'))
        
        user_info = profile_response.json()
        
        session['wikimedia_username'] = user_info.get('username')
        session['wikimedia_userid'] = user_info.get('sub')
        return redirect(url_for('home'))
    
    except Exception as e:
        traceback.print_exc()
        flash(_('Authentication failed. Please try again.'), 'danger')
        return redirect(url_for('home'))
    

@app.route('/auth/logout')
def logout():
    """Clear OAuth session"""
    session.pop('oauth_token', None)
    session.pop('wikimedia_username', None)
    session.pop('wikimedia_userid', None)
    session.pop('author_form_data', None)
    session.pop('work_form_data', None)
    
    flash(_('You have been logged out.'), 'info')
    return redirect(request.referrer or url_for('home'))

# WIKIDATA EDITING ROUTES

# Add author route
@app.route('/add-author', methods=['GET', 'POST'])
@limiter.limit("20 per hour", methods=['POST'])
def add_author():
    """Handle the Add Author form"""
    
    # Check if user is logged in
    if not user_is_logged_in():
        flash(_('Please login to add an author.'), 'warning')
        return redirect(url_for('home'))
    
    # Refresh token if needed
    if not oauth.token_refresh():
        flash(_('Your session has expired. Please login again.'), 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get OAuth session
            oauth_session = oauth.get_oauth_session()
            if not oauth_session:
                flash(_('Session expired. Please log in again.'), 'warning')
                return redirect(url_for('login'))

            wikidata = wikidata_api.WikidataAPI(app.config, oauth_session=oauth_session)

            # Process the author form (validation + creation)
            result = wikidata.process_author_form(request.form, current_lang=languages.get_locale())
            
            if result['success']:
                item_id = result['item_id']
               
                # Build URLs for the new item
                wikidata_url = f"https://www.wikidata.org/wiki/{item_id}"
                if wikidata_api.WIKIDATA_TEST_MODE:
                    wikidata_url = f"https://test.wikidata.org/wiki/{item_id}"
                
                paulina_url = url_for('author_page', author_data=item_id, _external=False)
                
                # Clear the author form data after successful creation
                session.pop('author_form_data', None)
                
                session['author_success_data'] = {
                    'item_id': item_id,
                    'wikidata_url': wikidata_url,
                    'paulina_url': paulina_url
                }
                    
                return redirect(url_for('add_author', success=1))
            
            else:
                if 'errors' in result:
                    for error in result['errors']:
                        flash(_(error), 'error')
                else:
                    error_msg = result.get('error', 'Unknown error')
                    if isinstance(error_msg, dict):
                        error_text = error_msg.get('info', str(error_msg))
                    else:
                        error_text = str(error_msg)
                    flash(_('Error creating author: %(error)s', error=error_text), 'danger')
                
                # Store form data in session for restoration
                session['author_form_data'] = dict(request.form)
                
                return render_template('add-author.html', 
                                     title=_('Add Author'),
                                     form_data=session['author_form_data'],
                                    form_genders=FORM_GENDERS)
        
        except Exception as e:
            flash(_('An error occurred while creating the author. Please try again.'), 'danger')
            
            # Store form data for restoration
            session['author_form_data'] = dict(request.form)
            
            return render_template('add-author.html', 
                                 title=_('Add Author'),
                                 form_data=session['author_form_data'],
                                 form_genders=FORM_GENDERS)
    
    # GET request handling
    if request.args.get('cleared') == '1':
        session.pop('author_form_data', None)
        session.pop('author_success_data', None) 
        form_data = None
        success_item_id = None
        wikidata_url = None
        paulina_url = None
    elif request.args.get('success') == '1':
        # Show success message from session
        success_data = session.pop('author_success_data', None) 
        form_data = None
        if success_data:
            success_item_id = success_data.get('item_id')
            wikidata_url = success_data.get('wikidata_url')
            paulina_url = success_data.get('paulina_url')
        else:
            success_item_id = None
            wikidata_url = None
            paulina_url = None
    else:
        form_data = session.get('author_form_data', None)
        success_item_id = None
        wikidata_url = None
        paulina_url = None
    
    return render_template('add-author.html', 
                        title=_('Add Author'),
                        form_data=form_data,
                        success_item_id=success_item_id,
                        wikidata_url=wikidata_url,
                        paulina_url=paulina_url,
                        form_genders=FORM_GENDERS)

# Add work route
@app.route('/add-work', methods=['GET', 'POST'])
@limiter.limit("20 per hour", methods=['POST'])
def add_work():
    """Handle the Add Work form"""
    
    # Check if user is logged in
    if not user_is_logged_in():
        flash(_('Please login to add a work.'), 'warning')
        return redirect(url_for('home'))
    
    # Refresh token if needed
    if not oauth.token_refresh():
        flash(_('Your session has expired. Please login again.'), 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get OAuth session
            oauth_session = oauth.get_oauth_session()
            if not oauth_session:
                flash(_('Session expired. Please log in again.'), 'warning')
                return redirect(url_for('login'))

            wikidata = wikidata_api.WikidataAPI(app.config, oauth_session=oauth_session)

            # Process the work form (validation + creation)
            result = wikidata.process_work_form(request.form, current_lang=languages.get_locale())
            
            if result['success']:
                item_id = result['item_id']
               
                # Build URLs for the new item
                wikidata_url = f"https://www.wikidata.org/wiki/{item_id}"
                if wikidata_api.WIKIDATA_TEST_MODE:
                    wikidata_url = f"https://test.wikidata.org/wiki/{item_id}"
                
                paulina_url = url_for('work_page', work_data=item_id, _external=False)
                
                # Clear the form after successful creation
                session.pop('work_form_data', None)
                
                session['work_success_data'] = {
                    'item_id': item_id,
                    'wikidata_url': wikidata_url,
                    'paulina_url': paulina_url
                }
                    
                return redirect(url_for('add_work', success=1))
            
            else:
                if 'errors' in result:
                    for error in result['errors']:
                        flash(_(error), 'error')
                else:
                    error_msg = result.get('error', 'Unknown error')
                    if isinstance(error_msg, dict):
                        error_text = error_msg.get('info', str(error_msg))
                    else:
                        error_text = str(error_msg)
                    flash(_('Error creating work: %(error)s', error=error_text), 'danger')
                
                # Store form data in session for restoration
                session['work_form_data'] = dict(request.form)
                
                return render_template('add-work.html', 
                                     title=_('Add Work'),
                                     form_data=session['work_form_data'],
                                     work_types=WORK_TYPES)
        
        except Exception as e:
            flash(_('An error occurred while creating the work. Please try again.'), 'danger')
            
            # Store form data for restoration
            session['work_form_data'] = dict(request.form)
            
            return render_template('add-work.html', 
                                 title=_('Add Work'),
                                 form_data=session['work_form_data'],
                                 work_types=WORK_TYPES)
    
    # GET request handling
    if request.args.get('cleared') == '1':
        session.pop('work_form_data', None)
        session.pop('work_success_data', None) 
        form_data = None
        success_item_id = None
        wikidata_url = None
        paulina_url = None
    elif request.args.get('success') == '1':
        # Show success message from session
        success_data = session.pop('work_success_data', None) 
        form_data = None
        if success_data:
            success_item_id = success_data.get('item_id')
            wikidata_url = success_data.get('wikidata_url')
            paulina_url = success_data.get('paulina_url')
        else:
            success_item_id = None
            wikidata_url = None
            paulina_url = None
    else:
        form_data = session.get('work_form_data', None)
        success_item_id = None
        wikidata_url = None
        paulina_url = None
    
    return render_template('add-work.html', 
                        title=_('Add Work'),
                        form_data=form_data,
                        success_item_id=success_item_id,
                        wikidata_url=wikidata_url,
                        paulina_url=paulina_url,
                        work_types=WORK_TYPES)
    
# Update fields - author page
@app.route('/update-author/<author_id>', methods=['PATCH'])
@limiter.limit("30 per hour")
def update_author(author_id):
    """Handle inline editing of author biography fields"""
    
    # Check if user is logged in
    if not user_is_logged_in():
        return jsonify({
            'success': False,
            'message': _('You must be logged in to edit.')
        }), 401
    
    # Refresh OAuth token if needed
    if not oauth.token_refresh():
        return jsonify({
            'success': False,
            'message': _('Session expired. Please log in again.')
        }), 401
    
    try:
        # Get the changes from request body
        data = request.get_json()
        if not data or 'changes' not in data:
            return jsonify({
                'success': False,
                'message': _('Invalid request data.')
            }), 400
        
        changes = data['changes']
        if not changes or not isinstance(changes, list):
            return jsonify({
                'success': False,
                'message': _('No changes provided.')
            }), 400
        
        # Initialize WikidataAPI with OAuth session
        oauth_session = oauth.get_oauth_session()
        wikidata = wikidata_api.WikidataAPI(app.config, oauth_session)
        
        # Process each change
        success_count = 0
        errors = []
        
        for change in changes:
            property_id = change.get('property')
            field_name = change.get('field')
            value = change.get('value')
            is_date = change.get('isDate', False)
            is_multi_select = change.get('isMultiSelect', False)
            references = change.get('references', [])
            
            if not property_id or not value:
                errors.append(_('Missing property or value for field: %(field)s', field=field_name))
                continue
            
            # Use the helper function to update the field
            result = wikidata.update_statement_field(
                item_id=author_id,
                property_id=property_id,
                value=value,
                field_name=field_name,
                is_date=is_date,
                is_multi_select=is_multi_select,
                references=references
            )
            
            if result['success']:
                success_count += 1
                
                # Clear cache for this author page
                cache_key = f"{request.language}, /author/{author_id}, {{}}"
                cache.delete(cache_key)
            else:
                errors.append(_('Error updating %(field)s: %(error)s', 
                              field=field_name, 
                              error=result.get('error', _('Unknown error'))))
        
        # Return result
        if success_count > 0 and not errors:
            return jsonify({
                'success': True,
                'message': _('Successfully updated!')
            }), 200
        elif success_count > 0 and errors:
            return jsonify({
                'success': True,
                'message': _('Updated with some errors.'),
                'errors': errors
            }), 207  # Multi-Status
        else:
            return jsonify({
                'success': False,
                'message': _('Failed to update fields.'),
                'errors': errors
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': _('Server error: %(error)s', error=str(e))
        }), 500

# Update fields - work page
@app.route('/update-work/<work_id>', methods=['PATCH'])
@limiter.limit("30 per hour")
def update_work(work_id):
    """Handle inline editing of work fields"""
    
    if not user_is_logged_in():
        return jsonify({
            'success': False,
            'message': _('You must be logged in to edit.')
        }), 401
    
    if not oauth.token_refresh():
        return jsonify({
            'success': False,
            'message': _('Session expired. Please log in again.')
        }), 401
    
    try:
        data = request.get_json()
        if not data or 'changes' not in data:
            return jsonify({'success': False, 'message': _('Invalid request data.')}), 400
        
        changes = data['changes']
        if not changes or not isinstance(changes, list):
            return jsonify({'success': False, 'message': _('No changes provided.')}), 400
        
        oauth_session = oauth.get_oauth_session()
        wikidata = wikidata_api.WikidataAPI(app.config, oauth_session)
        
        success_count = 0
        errors = []
        
        for change in changes:
            property_id = change.get('property')
            field_name = change.get('field')
            value = change.get('value')
            is_date = change.get('isDate', False)
            references = change.get('references', [])
            
            if not property_id or not value:
                errors.append(_('Missing property or value for field: %(field)s', field=field_name))
                continue
            
            result = wikidata.update_statement_field(
                item_id=work_id,
                property_id=property_id,
                value=value,
                field_name=field_name,
                is_date=is_date,
                is_multi_select=False,
                references=references
            )
            
            if result['success']:
                success_count += 1
                cache_key = f"{request.language}, /work/{work_id}, {{}}"
                cache.delete(cache_key)
            else:
                errors.append(_('Error updating %(field)s: %(error)s',
                              field=field_name,
                              error=result.get('error', _('Unknown error'))))
        
        if success_count > 0 and not errors:
            return jsonify({'success': True, 'message': _('Successfully updated!')}), 200
        elif success_count > 0 and errors:
            return jsonify({'success': True, 'message': _('Updated with some errors.'), 'errors': errors}), 207
        else:
            return jsonify({'success': False, 'message': _('Failed to update fields.'), 'errors': errors}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': _('Server error: %(error)s', error=str(e))}), 500


# Clear form data from session
@app.route('/clear_form_data', methods=['POST'])
def clear_form_data():
    """Clear stored form data from session"""
    if 'form_data' in session:
        session.pop('form_data')
    return jsonify({'success': True})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',
                           title=_('404 error')
                           ), 404


if __name__ == "__main__":
    app.run()

