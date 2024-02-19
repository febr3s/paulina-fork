from flask import Flask, render_template, request, redirect, url_for, abort
import pdclasses
import searchauthor
import datetime

app = Flask(__name__)


def print_field(field):
    if field is None:
        return ""
    elif field is True:
        return "Yes"
    elif field is False:
        return "No"
    else:
        return field


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/results", methods=["GET"])
def results():
    search_request = request.args.get("query")
    if search_request == "" or len(search_request) == 1:
        return render_template("no-results.html")
    search_result = searchauthor.search_author(search_request)
    if isinstance(search_result, list):
        return render_template('results.html', list_of_authors=search_result)
    elif search_result is None:
        return render_template("no-results.html")


@app.route("/author/<author_data>")
def author_page(author_data):
    try:
        author = pdclasses.Author(author_data)  # If user enters a URL with a Q of a non-human, this renders it anyway.
        return render_template(
            "author.html", author_name=print_field(author.name),
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
        return render_template(
            "works-list.html",
            author_name=author.name,
            author_works=print_field(author.getWorks())
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/work/<work_data>")
def work_page(work_data):
    try:
        work = pdclasses.Work(work_data)
        return render_template(
            "work.html", work_title=print_field(work.title),
            work_description=print_field(work.description),
            work_image=print_field(work.image),
            work_image_link=print_field(work.image_link),
            work_authors=print_field(work.authors),
            work_publication_date=print_field(work.publication_date),
            work_language=print_field(work.language),
            work_country=print_field(work.country_of_origin),
            work_wikipedia_link=print_field(work.wikipedia_link),
            work_wikisource_link=print_field(work.wikisource_link),
            work_internet_archive_link=print_field(work.internet_archive_link),
            work_wikidata_link=print_field(work.wikidata_link),
            work_copyright_status=print_field(work.getCopyrightStatus())
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/country/<country_data>")
def country_page(country_data):
    try:
        country = pdclasses.Country(country_data)
        return render_template(
            "country.html", country_name=print_field(country.name),
            country_copyright_terms=print_field(country.getCopyrightTerm()),
            country_image=print_field(country.image),
            country_image_link=print_field(country.image_link)
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.route("/term/<term_id>")
def term_page(term_id):
    try:
        term = pdclasses.Term(term_id)
        return render_template(
            "term.html",
            term_name=term.name,
            term_countries=print_field(term.getCountries())
        )
    except:  # If the Q number doesn't match any item
        abort(404)


@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow()}


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run()
    # app.run(debug=True)
