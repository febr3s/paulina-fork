from flask import Flask, render_template, request, redirect, Response, url_for, abort, flash, session, jsonify
from flask_caching import Cache
from flask_babel import Babel, _, get_locale
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mwoauth import ConsumerToken, Handshaker, RequestToken
from wikidata_api import WikidataAPI
import datetime
import requests

# Local modules
import pdclasses
import search
import languages
import squeries
import filters

app = Flask(__name__)


# i18n configuration

"""config.py contains the key for the session cookie.
The session cookie is required to store the language choice 
in the session and make it persistent."""

app.config.from_pyfile('config.py')

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
            work_language=print_field(work.language),
            work_country=print_field(work.country_of_origin),
            work_wikipedia_link=print_field(work.wikipedia_link),
            work_wikisource_links=print_field(work.wikisource_links),
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
    entity_type = request.args.get('type', 'author')
    
    # Get language from request, fall back to user's locale, then 'en'
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
            'User-Agent': 'Paulina/1.0 (https://paulina.toolforge.org/) Python/requests'
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
@limiter.limit("5 per minute")  # Prevent login spam
def login():
    """Initiate OAuth login with Wikimedia"""
    try:
        consumer_token = ConsumerToken(app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])
        handshaker = Handshaker(app.config['OAUTH_MWURI'], consumer_token)
        
        redirect_url, request_token = handshaker.initiate()
        
        # Store request token in session for callback
        session['request_token'] = dict(
            key=request_token.key,
            secret=request_token.secret
        )
        
        return redirect(redirect_url)
    
    except Exception as e:
        flash(_('Login failed. Please try again.'), 'danger')
        return redirect(url_for('home'))


@app.route('/oauth-callback')
def oauth_callback():
    """Handle OAuth callback from Wikimedia"""
    try:
        # Get the request token from session
        if 'request_token' not in session:
            flash('Login session expired. Please try again.', 'warning')
            return redirect(url_for('home'))
        
        request_token_dict = session.pop('request_token')
        
        # Recreate RequestToken object from dict
        request_token = RequestToken(
            request_token_dict['key'],
            request_token_dict['secret']
        )
        
        # Recreate the consumer token and handshaker
        consumer_token = ConsumerToken(app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])
        handshaker = Handshaker(app.config['OAUTH_MWURI'], consumer_token)
        
        # Complete the OAuth handshake with RequestToken object
        access_token = handshaker.complete(
            request_token,  
            request.query_string.decode('utf-8')
        )
        
        # Get user identity
        identity = handshaker.identify(access_token)
        
        # Store user info in session
        session['access_token'] = dict(
            key=access_token.key,
            secret=access_token.secret
        )
        session['wikimedia_username'] = identity['username']
        session['wikimedia_userid'] = identity['sub']      
        return redirect(url_for('home'))
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(_('Authentication failed. Please try again.'), 'danger')
        return redirect(url_for('home'))


@app.route('/auth/logout')
def logout():
    # Clear OAuth-related session data
    session.pop('access_token', None)
    session.pop('wikimedia_username', None)
    session.pop('wikimedia_userid', None)

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
    
    if request.method == 'POST':
        return process_add_author_form()
    
    return render_template('add-author.html', title=_('Add Author'))

def process_add_author_form():
    """Process the Add Author form submission"""
    
    try:
        wikidata = WikidataAPI(app.config)
        
        # Get form data
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        gender = request.form.get('gender', '').strip()
        nationality = request.form.get('nationality', '').strip()
        place_of_birth_qid = request.form.get('placeOfBirthQid', '').strip()
        place_of_birth_text = request.form.get('placeOfBirth', '').strip()
        date_of_birth = request.form.get('dateOfBirth', '').strip()
        date_of_death = request.form.get('dateOfDeath', '').strip()
        occupation_qids = request.form.get('occupationQids', '').strip()
        occupation_texts = request.form.get('occupationTexts', '').strip()
        ethnicity_qid = request.form.get('ethnicityQid', '').strip()
        ethnicity_text = request.form.get('ethnicity', '').strip()
        image_url = request.form.get('imageUrl', '').strip()
        official_website = request.form.get('officialWebsite', '').strip()
                
        # Validate required fields
        errors = []
        if not name:
            errors.append(_('Name is required'))
        if not description:
            errors.append(_('Description is required'))
        if not gender:
            errors.append(_('Gender is required'))
        if not nationality:
            errors.append(_('Nationality is required'))
        if not place_of_birth_qid and not place_of_birth_text:
            errors.append(_('Place of birth is required'))
        if not occupation_qids and not occupation_texts:
            errors.append(_('Occupation is required'))
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('add-author.html', 
                                 title=_('Add Author'),
                                 form_data=request.form)
        
        # Get current language for labels/descriptions
        lang = languages.get_locale()
        
        # Build labels and descriptions
        labels = {lang: name}
        descriptions = {lang: description} if description else {}
        
        # Build statements
        statements = []
        
        # Instance of: Human (Q5) - Required
        statements.append(
            wikidata.build_statement('P31', 'Q5', 'wikibase-item')
        )
        
        # Gender
        if gender:
            refs = collect_references('author-gender')
            statements.append(
                wikidata.build_statement('P21', gender, 'wikibase-item', refs)
            )
        
        # Nationality (Country of citizenship)
        if nationality:
            refs = collect_references('author-nationality')
            statements.append(
                wikidata.build_statement('P27', nationality, 'wikibase-item', refs)
            )
        
        # Place of birth
        if place_of_birth_qid:
            refs = collect_references('author-place-of-birth')
            statements.append(
                wikidata.build_statement('P19', place_of_birth_qid, 'wikibase-item', refs)
            )
        
        # Date of birth
        if date_of_birth:
            refs = collect_references('author-date-of-birth')
            statements.append(
                wikidata.build_statement('P569', date_of_birth, 'time', refs)
            )
        
        # Date of death
        if date_of_death:
            refs = collect_references('author-date-of-death')
            statements.append(
                wikidata.build_statement('P570', date_of_death, 'time', refs)
            )
        
        # Occupations (can be multiple)
        if occupation_qids:
            refs = collect_references('author-occupation')
            for qid in occupation_qids.split(','):
                qid = qid.strip()
                if qid:
                    statements.append(
                        wikidata.build_statement('P106', qid, 'wikibase-item', refs)
                    )
        
        # Ethnicity
        if ethnicity_qid:
            refs = collect_references('author-ethnicity')
            statements.append(
                wikidata.build_statement('P172', ethnicity_qid, 'wikibase-item', refs)
            )
        
        # Image (Commons)
        if image_url:
            filename = wikidata.extract_commons_filename(image_url)
            if filename:
                statements.append(
                    wikidata.build_statement('P18', filename, 'commonsMedia')
                )
        
        # Official website
        if official_website:
            statements.append(
                wikidata.build_statement('P856', official_website, 'url')
            )
        
        # Log the payload being sent to Wikidata
        payload = {
            'labels': labels,
            'descriptions': descriptions,
            'statements': statements
        }
        
        print("\n" + "="*60)
        print("WIKIDATA API PAYLOAD:")
        print("="*60)
        import json
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("="*60 + "\n")

        for field in ['gender', 'nationality', 'placeOfBirth', 'dateOfBirth', 'dateOfDeath', 'occupation', 'ethnicity']:
            refs = collect_references(field)
            print(f"{field} references: {refs}")

        print("="*60 + "\n")
        
        # Create the item on Wikidata
        result = wikidata.create_item(labels, descriptions, statements)
        
        # Log the result
        print("\n" + "="*60)
        print("WIKIDATA API RESPONSE:")
        print("="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("="*60 + "\n")
        
        if result['success']:
            item_id = result['item_id']
            flash(_('Author created successfully! Wikidata ID: %(item_id)s', item_id=item_id), 'success')
            # Keep form filled by passing form data back
            return render_template('add-author.html', 
                                 title=_('Add Author'),
                                 form_data=request.form,
                                 success_item_id=item_id)
        else:
            flash(_('Error creating author: %(error)s', error=result['error']), 'error')
            # Keep form filled on error
            return render_template('add-author.html', 
                                 title=_('Add Author'),
                                 form_data=request.form)
    
    except Exception as e:
        import traceback
        print("\n" + "="*60)
        print("EXCEPTION OCCURRED:")
        print("="*60)
        traceback.print_exc()
        print("="*60 + "\n")
        
        flash(_('An error occurred while creating the author. Please try again.'), 'error')
        # Keep form filled on exception
        return render_template('add-author.html', 
                             title=_('Add Author'),
                             form_data=request.form)
        
def collect_references(field_id):
    """
    Collect references for a specific field from form data
    
    Args:
        field_id: The field identifier (e.g., 'gender', 'nationality')
    
    Returns:
        List of reference dicts or None if no references
    """
    wikidata = WikidataAPI(app.config)
    references = []
    
    # Check for up to 3 references per field
    for i in range(3):
        url = request.form.get(f'{field_id}_ref_url_{i}', '').strip()
        title = request.form.get(f'{field_id}_ref_title_{i}', '').strip()
        retrieved = request.form.get(f'{field_id}_ref_retrieved_{i}', '').strip()
        
        if url:
            ref = wikidata.build_reference(url, title, retrieved)
            references.append(ref)
    
    return references if references else None

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',
                           title=_('404 error')
                           ), 404


if __name__ == "__main__":
    app.run()
