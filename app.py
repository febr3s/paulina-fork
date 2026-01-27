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
from wikidata_constants import FORM_GENDERS, WIKIDATA_TEST_MODE


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

def make_cache_key(**kwargs) -> str:
   """Creates a cache key combining the request path and the locale."""
   request_language = request.language
   request_path = request.path
   request_args = {key:value for key, value in request.args.items() if key!= "language"}   
   return f"{request_language}, {request_path}, {request_args}"

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
            in_public_domain = request.args.get("in-public-domain")
            search_result, complete = search.search_author(search_request, gender, nationality, in_public_domain)
            if len(search_result) > 0:
                return render_template('results.html',
                                        title=_("Results"),
                                        list_of_authors=search_result,
                                        search_request=search_request,
                                        type_of_search=type_of_search,
                                        complete=complete)
            else:
                return render_template("no-results.html",
                                        title=_("No results found"),
                                        search_request=search_request,
                                        type_of_search=type_of_search)
        elif type_of_search == "work":
            #if no search parameters have been input for Works search, show message
            type_of_work = request.args.get("type_of_work")
            country_of_origin = request.args.get("country_of_origin")
            search_result, complete = search.search_work(search_request, type_of_work, country_of_origin)
            if len(search_result) > 0:
                return render_template('results.html',
                                        title=_("Results"),
                                        list_of_works=search_result,
                                        search_request=search_request,
                                        type_of_search=type_of_search,
                                        complete=complete)
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
@cache.cached(make_cache_key=make_cache_key)
def author_page(author_data):
    try:
        author = pdclasses.Author(author_data)
        return render_template("author.html",
            title=print_field(author.name),
            author_name=print_field(author.name),
            author_id=print_field(author.wikidata_item_id),
            author_description=print_field(author.description),
            author_nationality=print_field(author.nationality),
            author_gender=print_field(author.gender),
            author_ethnicity=print_field(author.ethnicity),
            author_date_of_birth=print_field(author.date_of_birth),
            author_occupation=", ".join(print_field(author.occupation)),
            author_place_of_birth=print_field(author.place_of_birth),
            author_country_of_birth=print_field(author.country_of_birth),
            author_date_of_death=print_field(author.date_of_death),
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
            author_date_enter_public_domain=print_field(author.date_enter_public_domain)
        )
    except:  # If the Q number doesn't match any item or the item is not about a human
        abort(404)


@app.route("/works-list/<author_id>")
@cache.cached(make_cache_key=make_cache_key)
def works_list(author_id):
    try:
        query = squeries.query_for_works_by_an_author.format(qname=author_id, lang=languages.get_locale())
        wqs_link = "https://query.wikidata.org/#" + requests.utils.quote(query)
        author = pdclasses.Author(author_id)
        return render_template("works-list.html",
            title=_('List of works') + " - " + print_field(author.name),
            author_name=print_field(author.name),
            wqs_link=wqs_link,
            author_works=print_field(author.getWorks(languages.get_locale()))  # Get list of works
        )

    except:  # If the Q number doesn't match any item or the item is not about a human
        abort(404)


@app.route("/work/<work_data>")
@cache.cached(make_cache_key=make_cache_key)
def work_page(work_data):
    try:
        work = pdclasses.Work(work_data)  # Make a work object
        return render_template("work.html",
            title=print_field(work.name),  # This is for Open Graph meta tags
            work_title=print_field(work.name),
            work_description=print_field(work.description),
            work_image=print_field(work.image),
            work_image_link=print_field(work.image_link),
            work_image_alt_text=print_field(work.image_alt_text),
            work_authors=print_field(work.authors),
            work_publication_date=print_field(work.publication_date),
            work_creation_date=print_field(work.creation_date),
            work_language=print_field(work.language),
            work_country=print_field(work.country_of_origin),
            work_wikipedia_link=print_field(work.wikipedia_link),
            work_commons_link=print_field(work.commons_link),
            work_wikisource_links=print_field(work.wikisource_links),
            work_wikiquote_link=print_field(work.wikiquote_link),
            work_internet_archive_link=print_field(work.internet_archive_link),
            work_full_work_link=print_field(work.full_work_link),
            work_wikidata_link=print_field(work.wikidata_link),
            work_copyright_status=print_field(work.getCopyrightStatus())
        )
    except:  # If the Q number doesn't match any item
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
    ROBOTS_TXT = "User-agent: *\nAllow: /\n"
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
        import traceback
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
        import traceback
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

# Wikidata Editing Routes

@app.route('/add-author', methods=['GET', 'POST'])
@limiter.limit("20 per hour", methods=['POST'])
def add_author():
    """Handle the Add Author form"""
    
    # Check if user is logged in
    if 'wikimedia_username' not in session:
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
                flash(_('Session expired. Please login again.'), 'warning')
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
            app.logger.error(f"Author creation failed: {str(e)}", exc_info=True)
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


@app.route('/add-work', methods=['GET', 'POST'])
@limiter.limit("20 per hour", methods=['POST'])
def add_work():
    """Handle the Add Work form"""
    
    # Check if user is logged in
    if 'wikimedia_username' not in session:
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
                flash(_('Session expired. Please login again.'), 'warning')
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
                
                # Clear the work form data after successful creation
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
                                     form_data=session['work_form_data'])
        
        except Exception as e:
            app.logger.error(f"Work creation failed: {str(e)}", exc_info=True)
            flash(_('An error occurred while creating the work. Please try again.'), 'danger')
            
            # Store form data for restoration
            session['work_form_data'] = dict(request.form)
            
            return render_template('add-work.html', 
                                 title=_('Add Work'),
                                 form_data=session['work_form_data'])
    
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
                        paulina_url=paulina_url)


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
    
    app.run(debug=True)


