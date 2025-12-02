from flask import Flask, render_template, request, redirect, Response, url_for, abort
from flask_caching import Cache
from flask_babel import Babel, _, get_locale
import datetime
from urllib.parse import quote

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
        user_lang = str(get_locale())
        query = squeries.query_for_works_by_an_author.format(qname=author_id, lang=user_lang)
        wqs_link = "https://query.wikidata.org/#" + quote(query)
        author = pdclasses.Author(author_id)
        return render_template("works-list.html",
            title=_('List of works') + " - " + print_field(author.name),
            author_name=print_field(author.name),
            wqs_link=wqs_link,
            author_works=print_field(author.getWorks(user_lang))  # Get list of works
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
            country_number_of_works_in_public_domain=print_field(country.number_of_works_in_public_domain)
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


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',
                           title=_('404 error')
                           ), 404


if __name__ == "__main__":
    app.run()
