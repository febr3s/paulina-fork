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
    """Builds a datetime.date object from a pywikibot timestamp"""
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


def retrieve_query(query, **kwargs):
    """Takes a SPARQL query, sends it to the Wikidata Query Service and returns a list of results"""
    query_url_prefix = 'https://query.wikidata.org/sparql?query='
    query = query.format(**kwargs)
    query = requests.utils.quote(query)  # URL encoded
    request_json_format = '&format=json'
    query_url = query_url_prefix + query + request_json_format
    headers = {'user-agent': 'PaulinaApp/0.1 (https://gitlab.wikimedia.org/toolforge-repos/paulina)'}
    query_results = requests.get(query_url, headers=headers
                                 # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                 )
    query_results = query_results.json()
    query_results = query_results["results"]["bindings"]
    return query_results


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
                return "Unknown"
            elif not isinstance(self.date_of_birth, datetime.date):  # born BC
                return True
            elif self.date_of_birth.year < (datetime.date.today().year - 180):  # author was born in a date that assures is in public domain
                return True
            elif (datetime.date.today().year - 180) <= self.date_of_birth.year < (datetime.date.today().year - 90):
                return "Consult individual works"  # author born in a date that makes it impossible to determine copyright status worldwide.
            else:
                return False  # authors that are alive or whose works are probably in private domain worldwide

        elif not isinstance(self.date_of_death, datetime.date):  # died BC
            return True
        else:
            year_of_death = self.date_of_death.year
            if year_of_death < (datetime.date.today().year - 100):  # author works are in public domain worldwide
                return True
            elif (datetime.date.today().year - 100) <= year_of_death < (datetime.date.today().year - 50):
                return "Consult individual works"  # author works are in public domain in some countries
            elif ("film director" in self.occupation
                  or "photographer" in self.occupation) and self.date_of_birth.year < (datetime.date.today().year - 80):
                return "Consult individual works"   # This is to address works whose copyright
                # term is measured in years after being made available.
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

    def getWorks(self, lang):
        works = retrieve_query(squeries.query_for_works, qname=self.wikidata_item_id, lang=lang)
        return works

        # OLD CODE TO CHECK IF THERE ARE LINKS TO ACCESS THE WORK
        #         internet_archive_id = work.get()["claims"].get("P724")
        #         if 'enwikisource' in work.sitelinks or internet_archive_id:
        #             work_info[2] = True


class Work:
    """A class for cultural works."""
    def __init__(self, wikidata_work_id, title_lang):
        self.wikidata_work_id = wikidata_work_id

        self.wikidata_work_item = pywikibot.ItemPage(wikidata_site, wikidata_work_id)

        self.wikidata_link = self.wikidata_work_item.full_url()

        self.instance_of = build_field(self.wikidata_work_item.get()["claims"].get("P31"))

        if 'en' in self.wikidata_work_item.labels:
            self.title = self.wikidata_work_item.labels['en']  # Show the title in English if "en" label available
        elif title_lang in self.wikidata_work_item.labels:
            self.title = self.wikidata_work_item.labels[title_lang]  # Otherwise, show the title in the browser language
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

        full_work_available_at = self.wikidata_work_item.get()["claims"].get("P953")
        if full_work_available_at is None:
            self.full_work_link = None
        else:
            self.full_work_link = full_work_available_at[0].getTarget()

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
        copyright_term = retrieve_query(squeries.query_for_country_copyright_term, qname=self.wikidata_country_id)
        return copyright_term


class Term:
    """A class for terms."""

    def __init__(self, wikidata_term_id):

        self.wikidata_term_id = wikidata_term_id

        self.wikidata_item = pywikibot.ItemPage(wikidata_site, wikidata_term_id)

        self.wikidata_link = self.wikidata_item.full_url()

        self.name = self.wikidata_item.labels['en']

    # Method to get list of countries by copyright term
    def getCountries(self):
        countries = retrieve_query(squeries.query_for_countries_by_copyright_term, qname=self.wikidata_term_id)
        return countries
