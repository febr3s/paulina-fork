import pywikibot
from pywikibot import pagegenerators as pg
import datetime  # to calculate if the works are in public domain
import dateutil.relativedelta as rd
import squeries  # local module with SPARQL queries
import requests

wikidata_site = pywikibot.Site('wikidata', 'wikidata')
wikipedia_site = pywikibot.Site("en", "wikipedia")
commons_site = pywikibot.Site("commons", "commons")
wikisource_site = pywikibot.Site("en", "wikisource")
wikiquote_site = pywikibot.Site("en", "wikiquote")


def build_field(wikidata_statement):
    """Function to return a field from a Wikidata statement.
    If the statement does not exist, it returns None.
    If the statement exists and has a preferred value, return the preferred value.
    If the statement exists and does not have a preferred value, print all values."""
    if wikidata_statement is None:  # If statement doesn't exist
        return None
    else:  # If statement exists, check if there is a preferred value
        dictionary_of_claims = {}
        for claim in wikidata_statement:
            claim_target = claim.getTarget()
            claim_rank = claim.getRank()
            dictionary_of_claims[claim_target] = claim_rank
            if claim_rank == "preferred":
                break

        if "preferred" in dictionary_of_claims.values():
            return [key.labels["en"] for key, value in dictionary_of_claims.items() if value == "preferred"][0]
        else:
            return [key.labels["en"] for key, value in dictionary_of_claims.items()][0]


def build_date(date_input):
    """Build a datetime.date object from a pywikibot timestamp"""
    try:  # This try and except handles the case in which the date is unknown
        year = date_input[0].getTarget().year
    except AttributeError:
        return None
    if int(year) < 1:  # If date is BC, datetime module can't handle it
        return int(year)  # For simplicity, dates BC have year precision
    else:
        month = date_input[0].getTarget().month
        day = date_input[0].getTarget().day
        try:
            return datetime.date(year, month, day)
        except:
            try:
                return datetime.date(year, 1, 1)  # Try to catch the year if date is not standard
            except:
                return None


class Author:
    """A class for authors."""

    def __init__(self, wikidata_item_id):

        self.wikidata_item_id = wikidata_item_id

        self.wikidata_item = pywikibot.ItemPage(wikidata_site, wikidata_item_id)

        self.wikidata_link = self.wikidata_item.full_url()

        if 'en' in self.wikidata_item.labels:
            self.name = self.wikidata_item.labels['en']
        else:
            self.name = None

        if 'en' in self.wikidata_item.descriptions:
            self.description = self.wikidata_item.descriptions['en']
        else:
            self.description = None

        if 'enwiki' in self.wikidata_item.sitelinks:
            self.wikipedia_link = pywikibot.Page(wikipedia_site, self.wikidata_item.getSitelink('enwiki')).full_url()
        else:
            self.wikipedia_link = None

        if 'commonswiki' in self.wikidata_item.sitelinks:
            self.commons_link = pywikibot.Page(commons_site, self.wikidata_item.getSitelink('commonswiki')).full_url()
        else:
            self.commons_link = None

        if 'enwikisource' in self.wikidata_item.sitelinks:
            self.wikisource_link = pywikibot.Page(wikisource_site, self.wikidata_item.getSitelink('enwikisource')).full_url()
        else:
            self.wikisource_link = None

        if 'enwikiquote' in self.wikidata_item.sitelinks:
            self.wikiquote_link = pywikibot.Page(wikiquote_site, self.wikidata_item.getSitelink('enwikiquote')).full_url()
        else:
            self.wikiquote_link = None

        self.nationality = build_field(self.wikidata_item.get()["claims"].get("P27"))

        self.gender = build_field(self.wikidata_item.get()["claims"].get("P21"))

        date_of_birth = self.wikidata_item.get()["claims"].get('P569')
        if date_of_birth is None:
            self.date_of_birth = None
        else:
            self.date_of_birth = build_date(date_of_birth)

        date_of_death = self.wikidata_item.get()["claims"].get('P570')
        if date_of_death is None:
            self.date_of_death = None
        else:
            self.date_of_death = build_date(date_of_death)

        occupations = self.wikidata_item.get()["claims"].get('P106')
        if occupations is None:
            self.occupation = None
        else:
            self.occupation = [occupation.getTarget().labels["en"] for occupation in occupations]

        self.place_of_birth = build_field(self.wikidata_item.get()["claims"].get("P19"))

        # Country of birth is built taking the place of birth and looking in what country it is.
        try:
            self.country_of_birth = build_field(self.wikidata_item.get()
                                                       ["claims"].get('P19')[0].getTarget().get()["claims"].get(
                'P17'))
        except TypeError:  # if there's no statement for place of birth, its value is None and the try statement gives a TypeError
            self.country_of_birth = None

        image = self.wikidata_item.get()["claims"].get('P18')
        if image is None:
            self.image = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Image_is_needed_female.svg/240px-Image_is_needed_female.svg.png"
            self.image_link = "https://commons.wikimedia.org/wiki/Commons:Welcome"
        else:
            self.image = image[0].getTarget().get_file_url()
            self.image_link = image[0].getTarget().get_file_url()

    def isInPublicDomain(self):
        if self.date_of_death is None:
            if self.date_of_birth is None:
                return "Unknown due to lack of available dates of birth and death"
            elif not isinstance(self.date_of_birth, datetime.date):  # born BC
                return True
            elif self.date_of_birth.year < (datetime.date.today().year - 170):  # authors born in a date that assures is in public domain
                return True
            else:
                return False  # authors that are alive or whose works may still be in private domain

        elif not isinstance(self.date_of_death, datetime.date):  # died BC
            return True
        else:
            year_of_death = self.date_of_death.year
            if year_of_death < (datetime.date.today().year - 70):
                return True
            else:
                return False

    def ageOfAuthor(self):
        if self.date_of_death is None:
            if not isinstance(self.date_of_birth, datetime.date) or self.date_of_birth.year < (datetime.date.today().year - 110):
                return "Unknown"  # Dead authors without date of death, and authors with date of birth and death unavailable
            else:
                return rd.relativedelta(datetime.date.today(), self.date_of_birth).years  # Age of living authors
        else:
            if not isinstance(self.date_of_death, datetime.date):
                return self.date_of_death - self.date_of_birth  # If died BC, dates are integers
            elif isinstance(self.date_of_death, datetime.date) and not isinstance(self.date_of_birth, datetime.date):
                return self.date_of_death.year - self.date_of_birth  # If born BC and died AC, date types are mixed
            else:
                return rd.relativedelta(self.date_of_death, self.date_of_birth).years  # If born AC, dates are datetime objects

    def getWorks(self):
        query_for_works = squeries.query_for_works.format(qname=self.wikidata_item_id)
        generator = pg.WikidataSPARQLPageGenerator(query_for_works, site=wikidata_site)

        list_of_works = []
        for work in generator:
            if 'en' in work.labels:  # Display only works that have a label
                work_info = [work.labels['en'], work.id, False]
                internet_archive_id = work.get()["claims"].get("P724")
                if 'enwikisource' in work.sitelinks or internet_archive_id:  # Check if there are links to access the work
                    work_info[2] = True
                list_of_works.append(work_info)
        return list_of_works


class Work:
    """A class for cultural works."""
    def __init__(self, wikidata_work_id):
        self.wikidata_work_id = wikidata_work_id

        self.wikidata_work_item = pywikibot.ItemPage(wikidata_site, wikidata_work_id)

        self.wikidata_link = self.wikidata_work_item.full_url()

        self.instance_of = build_field(self.wikidata_work_item.get()["claims"].get("P31"))

        if 'en' in self.wikidata_work_item.labels:
            self.title = self.wikidata_work_item.labels['en']
        else:
            self.title = None

        if 'en' in self.wikidata_work_item.descriptions:
            self.description = self.wikidata_work_item.descriptions['en']
        else:
            self.description = None

        image = self.wikidata_work_item.get()["claims"].get('P18')
        if image is None:
            self.image = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Placeholder_book.svg/464px-Placeholder_book.svg.png"
            self.image_link = "https://commons.wikimedia.org/wiki/Commons:Welcome"
        else:
            self.image = image[0].getTarget().get_file_url()
            self.image_link = image[0].getTarget().get_file_url()

        types_of_author = {"creator": "P170",
                           "author": "P50",
                           "director": "P57",
                           "screenwriter": "P58",
                           "architect": "P84",
                           "composer": "P86",
                           "librettist": "P87",
                           "illustrator": "P110",
                           "lyrics_by": "P676",
                           "programmer": "P943"
                           }

        dict_of_authors = {}
        for type_of_author, value in types_of_author.items():
            authors = self.wikidata_work_item.get()["claims"].get(value)
            if authors is not None:
                dict_of_authors[type_of_author] = [{"name": author.getTarget().labels["en"], "ID": author.getTarget().id} for author in authors]

        self.authors = dict_of_authors

        self.country_of_origin = build_field(self.wikidata_work_item.get()["claims"].get("P495"))

        self.language = build_field(self.wikidata_work_item.get()["claims"].get("P407"))

        publication_date = self.wikidata_work_item.get()["claims"].get('P577')
        if publication_date is None:
            self.publication_date = None
        else:
            self.publication_date = build_date(publication_date)

        if 'enwiki' in self.wikidata_work_item.sitelinks:
            self.wikipedia_link = pywikibot.Page(wikipedia_site, self.wikidata_work_item.getSitelink('enwiki')).full_url()
        else:
            self.wikipedia_link = None

        if 'enwikisource' in self.wikidata_work_item.sitelinks:
            self.wikisource_link = pywikibot.Page(wikisource_site, self.wikidata_work_item.getSitelink('enwikisource')).full_url()
        else:
            self.wikisource_link = None

        internet_archive_ID = self.wikidata_work_item.get()["claims"].get("P724")
        if internet_archive_ID is None:
            self.internet_archive_link = None
        else:
            self.internet_archive_link = "https://archive.org/details/" + internet_archive_ID[0].getTarget()


    def getCopyrightStatus(self):  # Improve this: when copyright status is None, try to estimate it by author's death or publication date
        copyright_status_statement = self.wikidata_work_item.get()["claims"].get('P6216')
        if not copyright_status_statement:
            return None
        else:
            copyright_status = []
            for claim in copyright_status_statement:
                try:
                    status_dict = {
                        'status': claim.getTarget().labels["en"],
                        'applies_to_jurisdiction_label': claim.qualifiers['P1001'][0].getTarget().labels["en"],
                        'applies_to_jurisdiction_id': claim.qualifiers['P1001'][0].getTarget().id,
                        'jurisdiction_is_instance_of': claim.qualifiers['P1001'][0].getTarget().get()['claims']["P31"][0].getTarget().id
                        }
                    copyright_status.append(status_dict)
                except:
                    pass
            return copyright_status

        # Other attributes to be created: identifiers, etc
        # form of creative work, genre, Gutenberg link, etc


class Country:
    """A class for countries."""

    def __init__(self, wikidata_country_id):

        self.wikidata_country_id = wikidata_country_id

        self.wikidata_item = pywikibot.ItemPage(wikidata_site, wikidata_country_id)

        self.wikidata_link = self.wikidata_item.full_url()

        self.name = self.wikidata_item.labels['en']

        image = self.wikidata_item.get()["claims"].get('P41')
        if image is None:
            self.image = None
            self.image_link = None
        else:
            self.image = image[0].getTarget().get_file_url()
            self.image_link = image[0].getTarget().get_file_url()

    # Method to determine the copyright term of the country
    def getCopyrightTerm(self):
        query_for_term = squeries.query_for_country_copyright_term.format(qname=self.wikidata_country_id)
        generator = pg.WikidataSPARQLPageGenerator(query_for_term, site=wikidata_site)

        # list_of_terms = []
        # for term in generator:
        #     if 'en' in term.labels:  # Display only terms that have a label
        #         term_info = [term.labels['en'], term.id]
        #         list_of_terms.append(term_info)
        # return list_of_terms
        return generator


class Term:
    """A class for terms."""

    def __init__(self, wikidata_term_id):

        self.wikidata_term_id = wikidata_term_id

        self.wikidata_item = pywikibot.ItemPage(wikidata_site, wikidata_term_id)

        self.wikidata_link = self.wikidata_item.full_url()

        self.name = self.wikidata_item.labels['en']

    # Method to get list of countries by copyright term
    def getCountries(self):
        query_url_prefix = 'https://query.wikidata.org/sparql?query='
        query_for_countries = squeries.query_for_countries_by_copyright_term.format(qname=self.wikidata_term_id)
        query_for_countries = requests.utils.quote(query_for_countries)  # URL encoded
        request_json_format = '&format=json'
        url_query_countries_by_copyright_term = query_url_prefix + query_for_countries + request_json_format
        headers = {'user-agent': 'PaulinaApp/0.1 (https://gitlab.wikimedia.org/toolforge-repos/paulina)'}
        query_results = requests.get(url_query_countries_by_copyright_term, headers=headers
                                     # , timeout=1    # If IPv6 doesn't work, force time out and use IPv4
                                     )
        query_results = query_results.json()
        query_results = query_results["results"]["bindings"]
        query_results.sort(key=lambda e: e['itemLabel']['value'])
        return query_results


if __name__ == "__main__":
    def print_profile():
        print(f"Name: {author.name}")
        print(f"Description: {author.description}")
        print(f"Nationality: {author.nationality}")
        print(f"Gender: {author.gender}")
        print(f"Date of birth: {author.date_of_birth}")
        print(f"Occupation: {author.occupation}")
        print(f"Place of birth: {author.place_of_birth}")
        print(f"Country of birth: {author.country_of_birth}")
        print(f"Date of death: {author.date_of_death}")
        print(f"Age of author: {author.ageOfAuthor()} years")
        print(f"Image: {author.image}")
        print(f"Wikipedia link: {author.wikipedia_link}")
        print(f"Wikimedia Commons link: {author.commons_link}")
        print(f"Wikisource link: {author.wikisource_link}")
        print(f"Wikiquote link: {author.wikiquote_link}")
        print(f"Are the author's works in public domain?: {author.isInPublicDomain()}")
        print(f"Did you find wrong information? Correct it in Wikidata: {author.wikidata_link}")
        print()


    def print_works():
        print("Loading. It can take some time...")
        works_retrieved = author.getWorks()
        print("\nLIST OF WORKS:\n")
        for work in works_retrieved:
            work_title = work[0]
            work_link = work[1]
            print(f"{work_title}: {work_link}")


    author_wikidata_item = 'Q692'

    author = Author(author_wikidata_item)

    print_profile()

    show_author_works = input("Do you want to look for the author's works? Y/N: ").lower()
    if show_author_works in ["y", "yes"]:
        print_works()
    else:
        print("\nGood bye.")
