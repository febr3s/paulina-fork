from flask import Flask, render_template, request, redirect, url_for, abort
from flask_babel import Babel, _
import datetime

# Local modules
import pdclasses
import search
import languages
import squeries

app = Flask(__name__)

app.config.from_pyfile('config.py')

babel = Babel(app, locale_selector=languages.get_locale)

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
        if search_request is None:
            referer = request.headers.get('Referer')
            if referer is not None:
                if referer.startswith(url_for('home', _external=True)):
                    path_string = "&".join(referer.split("?")[-1].split("&")[0:2])
                    return redirect(url_for('results') + "?" + path_string + "&" + "language=" + language )
                else:
                    return redirect(url_for('home'))
            else:
                return redirect(url_for('home'))
        elif search_request == "" or len(search_request) == 1:
            return render_template("no-results.html",
                                   title=_("No results found"),
                                   search_request=search_request,
                                   type_of_search=type_of_search)
        elif len(search_request) > 1:
            if type_of_search == "author":
                search_result = search.search_author(search_request)
                if len(search_result) > 0:
                    return render_template('results.html',
                                           title=_("Results"),
                                           list_of_authors=search_result,
                                           search_request=search_request,
                                           type_of_search=type_of_search)
                else:
                    return render_template("no-results.html",
                                           title=_("No results found"),
                                           search_request=search_request,
                                           type_of_search=type_of_search)
            elif type_of_search == "work":
                search_result = search.search_work(search_request)
                if len(search_result) > 0:
                    return render_template('results.html',
                                           title=_("Results"),
                                           list_of_works=search_result,
                                           search_request=search_request,
                                           type_of_search=type_of_search)
                else:
                    return render_template("no-results.html",
                                           title=_("No results found"),
                                           search_request=search_request,
                                           type_of_search=type_of_search)
    except:
        abort(404)

@app.route("/author/<author_data>")
def author_page(author_data):
    try:
        author = pdclasses.Author(author_data)  # If user enters a URL with a Q of a non-human, this renders it anyway.
        return render_template("author.html",
            title=print_field(author.name),
            author_name=print_field(author.name),
            author_id=print_field(author.wikidata_item_id),
            author_description=print_field(author.description),
            author_nationality=print_field(author.nationality),
            author_gender=print_field(author.gender),
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
            author_is_in_public_domain=print_field(author.isInPublicDomain()),
            author_wikidata_link=print_field(author.wikidata_link)
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/works-list/<author_id>")
def works_list(author_id):
    try:
        author = pdclasses.Author(author_id)
        return render_template("works-list.html",
            title=_('List of works') + " - " + print_field(author.name),
            author_name=print_field(author.name),
            author_works=print_field(author.getWorks(languages.get_locale()))  # Get list of works
        )

    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/work/<work_data>")
def work_page(work_data):
    try:
        work = pdclasses.Work(work_data)  # Make a work object
        return render_template("work.html",
            title=print_field(work.title),
            work_title=print_field(work.title),
            work_description=print_field(work.description),
            work_image=print_field(work.image),
            work_image_link=print_field(work.image_link),
            work_image_alt_text=print_field(work.image_alt_text),
            work_authors=print_field(work.authors),
            work_publication_date=print_field(work.publication_date),
            work_language=print_field(work.language),
            work_country=print_field(work.country_of_origin),
            work_wikipedia_link=print_field(work.wikipedia_link),
            work_wikisource_link=print_field(work.wikisource_link),
            work_internet_archive_link=print_field(work.internet_archive_link),
            work_full_work_link=print_field(work.full_work_link),
            work_wikidata_link=print_field(work.wikidata_link),
            work_copyright_status=print_field(work.getCopyrightStatus())
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/country/<country_data>")
def country_page(country_data):
    try:
        country = pdclasses.Country(country_data)
        return render_template("country.html",
            title=print_field(country.name),
            country_name=print_field(country.name),
            country_copyright_terms=print_field(country.getCopyrightTerm()),
            country_flag_image=print_field(country.flag_image),
            country_flag_image_link=print_field(country.flag_image_link),
            country_flag_image_alt_text=print_field(country.flag_image_alt_text)
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/term/<term_id>")
def term_page(term_id):
    try:
        term = pdclasses.Term(term_id)
        return render_template("term.html",
            title=_('List of %(term_name)s', term_name=print_field(term.name)),
            term_name=print_field(term.name),
            term_countries=print_field(term.getCountries())
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/countries/")
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


@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now(datetime.timezone.utc)}


@app.context_processor
def inject_language():
    return {"CURRENT_LANGUAGE": languages.get_locale(),
            "TRANSLATED_LANGUAGES": languages.TRANSLATED_LANGUAGES}


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',
                           title=_('404 error')
                           ), 404


if __name__ == "__main__":
    # app.run()
    app.run(debug=True)
