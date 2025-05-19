from flask_babel import _, format_date, get_locale
import datetime  # to calculate if the works are in public domain
import dateutil.relativedelta as rd
import requests

# Local modules
import squeries
import languages


def build_field(wikidata_statement: list[dict], field_type: str ="label") -> str | None:
    """Function to return a field from a Wikidata statement.
    If the statement does not exist, it returns None.
    If the statement exists and has a preferred value, it returns the preferred value.
    If the statement exists and does not have a preferred value, it returns the first value.
    The default behavior of the function is to return the label of the value,
    but if the optional argument 'field_type' is set to 'qid',
    the function returns the Wikidata item ID of the value."""
    if wikidata_statement is None:  # If statement doesn't exist
        return None
    else:  # If statement exists, check if there is a preferred value
        dictionary_of_claims = {}
        for claim in wikidata_statement:
            claim_info = claim.get("value")
            if claim_info["type"] in ["novalue", "somevalue"]:
                claim_target = claim_info["type"]
            else:
                claim_target = claim_info.get("content")
            claim_rank = claim.get('rank')
            dictionary_of_claims[claim_target] = claim_rank
            if claim_rank == "preferred":
                break

        if "preferred" in dictionary_of_claims.values():  # If there is a preferred value, pick it            
            if field_type == "qid":
                return [key for key, value in dictionary_of_claims.items()
                        if value == "preferred" and key not in ["novalue", "somevalue"]][0]
            else:
                return [retrieve_item(key, data_type="labels").get(languages.get_locale())
                        for key, value in dictionary_of_claims.items()
                        if value == "preferred" and key not in ["novalue", "somevalue"]][0]

        else:  # If there is not a preferred value, pick the first value
            first_claim = next(iter(dictionary_of_claims))
            if first_claim in ["novalue", "somevalue"]:  # If the value is not a Wikidata item ID
                if field_type == "qid":
                    return None
                else:
                    return first_claim
                
            else:  # If the value is a Wikidata item ID
                if field_type == "qid":
                    return first_claim
                else:
                    return retrieve_item(first_claim, data_type="labels").get(languages.get_locale())


def build_date(wikidata_statement: list[dict]) -> dict | None:
    """Builds a dictionary with a datetime.date object and a date string from a Wikidata timestamp"""
    if wikidata_statement is None:  # If statement doesn't exist
        return None
    else:  # If statement exists, check if there is a preferred value
        list_of_claims = []
        chosen_date_info = None
        for claim in wikidata_statement:
            claim_date = claim.get('value', {}).get('content', {}).get('time')
            claim_precision = claim.get('value', {}).get('content', {}).get('precision')
            claim_rank = claim.get('rank')
            if claim_rank == "preferred":
                chosen_date_info = {"claim date": claim_date, "claim precision": claim_precision}
                break
            else:
                list_of_claims.append({"claim date": claim_date, "claim precision": claim_precision})

        if chosen_date_info is None:
            chosen_date_info = list_of_claims[0]

        date = chosen_date_info["claim date"]
        precision = chosen_date_info["claim precision"]

        try:  # This try and except handles the case in which the date is unknown
            year = int(date[:5])
        except TypeError:
            return None
        month = int(date[6:8])
        day = int(date[9:11])
        if year < 1:  # If date is BC, datetime module can't handle it
            return {"date object": year, "date string": f"{year}"}  # For simplicity, dates BC have year precision
        else:
            if precision == 11:  # Day precision
                return {"date object": datetime.date(year, month, day), "date string": format_date(datetime.date(year, month, day), "long")}
            elif precision == 10:  # Month precision
                return {"date object": datetime.date(year, month, 1), "date string": format_date(datetime.date(year, month, 1), "MMMM yyyy")}
            elif precision == 9:  # Year precision
                return {"date object": datetime.date(year, 1, 1), "date string": f"{year}"}
            elif precision == 8:  # Decade precision
                return {"date object": datetime.date(year, 1, 1), "date string": f"{year} " + _("(decade)")}
            elif precision == 7:  # Century precision
                return {"date object": datetime.date(year, 1, 1), "date string": f"{year} " + _("(century)")}
            elif precision == 6:  # Millennium precision
                return {"date object": datetime.date(year, 1, 1), "date string": f"{year} " + _("(millennium)")}
            else:
                return {"date object": datetime.date(year, 1, 1), "date string": f"{year}"}


def retrieve_item(wikidata_item_id: str, data_type: str ="item") -> dict:
    """Takes a Q identifier and returns the item full data or the item labels in case the optional argument
    'data-type' is set to 'labels'"""
    item_url_prefix = "https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/"
    if data_type == "labels":
        item_url_suffix = "/labels"
    else:
        item_url_suffix = ""
    item_url = item_url_prefix + wikidata_item_id + item_url_suffix
    headers = {'user-agent': 'PaulinaApp/0.9 (https://gitlab.wikimedia.org/toolforge-repos/paulina)'}
    item_response = requests.get(item_url, headers=headers
                                   # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                   )
    item_attributes = item_response.json()
    return item_attributes


class Parent:
    """A parent class with general information about an item."""
    def __init__(self, wikidata_item_id):
        self.wikidata_item_id = wikidata_item_id
        self.wikidata_item = retrieve_item(wikidata_item_id, data_type="item")
        self.wikidata_link = "https://www.wikidata.org/wiki/" + wikidata_item_id

        if self.wikidata_item.get('labels', {}).get(languages.get_locale()) is not None:
            self.name = self.wikidata_item.get('labels', {}).get(languages.get_locale())
        elif self.wikidata_item.get('labels', {}).get("mul") is not None:
            self.name = self.wikidata_item.get('labels', {}).get("mul")
        else:
            self.name = self.wikidata_item.get('labels', {}).get("en")

        self.description = self.wikidata_item.get('descriptions', {}).get(languages.get_locale())
        self.wikipedia_link = self.wikidata_item.get('sitelinks', {}).get(languages.get_locale() + 'wiki', {}).get('url')


class Author(Parent):
    """A class for authors."""
    def __init__(self, wikidata_item_id):
        super().__init__(wikidata_item_id)

        """ Prevent loading an author page if the Wikidata item does not exist or it is not about a human:            
            - Raise a "TypeError: 'NoneType' object is not iterable" if the item does not exist.
            - Raise an "Exception: Not a human" if the item is not about a human."""
        for statement in self.wikidata_item.get('statements', {}).get('P31'):
            if statement.get('value', {}).get('content') not in ["Q5", "Q21070568"]:
                raise Exception("Not a human")
            
        self.commons_link = self.wikidata_item.get('sitelinks', {}).get('commonswiki', {}).get('url')
        self.wikisource_link = self.wikidata_item.get('sitelinks', {}).get(languages.get_locale() + 'wikisource', {}).get('url')
        self.wikiquote_link = self.wikidata_item.get('sitelinks', {}).get(languages.get_locale() + 'wikiquote', {}).get('url')
        self.nationality = build_field(self.wikidata_item.get('statements', {}).get('P27'))
        self.gender = build_field(self.wikidata_item.get('statements', {}).get('P21'))
        self.date_of_birth = build_date(self.wikidata_item.get('statements', {}).get('P569'))
        self.date_of_death = build_date(self.wikidata_item.get('statements', {}).get('P570'))
        self.date_enter_public_domain = self.date_of_death['date object'].year + 101 if self.date_of_death else None

        occupations = self.wikidata_item.get('statements', {}).get('P106')
        if occupations is None:
            self.occupation = None
        else:
            occupations_ids = [occupation.get('value', {}).get('content') for occupation in occupations]
            occupations_labels = squeries.retrieve_query(squeries.query_for_labels_of_list_of_items,
                                                qnames="wd:" + " wd:".join(occupations_ids),
                                                lang=languages.get_locale()
                                                )
            self.occupation = [occupation_item.get('itemLabel', {}).get('value')
                               for occupation_item in occupations_labels]

        place_of_birth = self.wikidata_item.get('statements', {}).get('P19')
        self.place_of_birth = build_field(place_of_birth)

        # Country of birth is built taking the place of birth and looking in what country it is.
        if place_of_birth:
            place_of_birth_Q = build_field(place_of_birth, field_type="qid")
            if place_of_birth_Q:
                country_of_birth = squeries.retrieve_query(squeries.query_for_country_of_birth,
                                                  qname=place_of_birth_Q,
                                                  lang=languages.get_locale()
                                                  )
                self.country_of_birth = country_of_birth[0].get('itemLabel', {}).get('value')
            else:
                self.country_of_birth = None
        else:
            self.country_of_birth = None

        image = self.wikidata_item.get('statements', {}).get('P18')
        if image is None:
            self.image = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Image_is_needed_female.svg/240px-Image_is_needed_female.svg.png"
            self.image_link = "https://commons.wikimedia.org/wiki/Commons:Welcome"
            self.image_alt_text = _('Image of a generic human silhouette. The text above it indicates that there is no free image of the person available, and that if you own one, you can click on the placeholder link.')
        else:
            image_file_name = image[0]["value"]["content"]
            image_file_name = requests.utils.quote(image_file_name)
            self.image = 'https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/' + image_file_name + '&width=400&height=100'
            self.image_link = 'https://commons.wikimedia.org/wiki/File:' + image_file_name
            self.image_alt_text = _('Image of %(name)s.', name=self.name)

    def isInPublicDomain(self):
        if self.date_of_death is None:
            if self.date_of_birth is None:
                return "Unknown"
            elif not isinstance(self.date_of_birth["date object"], datetime.date):  # born BC
                return True
            elif self.date_of_birth["date object"].year < (datetime.date.today().year - 180):  # author was born in a date that assures is in public domain
                return True
            elif (datetime.date.today().year - 180) <= self.date_of_birth["date object"].year < (datetime.date.today().year - 90):
                return "Consult individual works"  # author born in a date that makes it impossible to determine copyright status worldwide.
            else:
                return False  # authors that are alive or whose works are probably in private domain worldwide

        elif not isinstance(self.date_of_death["date object"], datetime.date):  # died BC
            return True
        else:
            year_of_death = self.date_of_death["date object"].year
            if year_of_death < (datetime.date.today().year - 100):  # author works are in public domain worldwide
                return True
            elif (datetime.date.today().year - 100) <= year_of_death < (datetime.date.today().year - 50):
                return "Consult individual works"  # author works are in public domain in some countries
            elif self.occupation and ("film director" in self.occupation
                  or "photographer" in self.occupation) and self.date_of_birth["date object"].year < (datetime.date.today().year - 80):
                return "Consult individual works"   # This is to address works whose copyright
                # term is measured in years after being made available.
            else:
                return False

    def ageOfAuthor(self):
        if self.date_of_birth is None:
            return _('Unknown')  # Authors with date of birth unavailable
        if self.date_of_death is None:
            if not isinstance(self.date_of_birth["date object"], datetime.date) or self.date_of_birth["date object"].year < (datetime.date.today().year - 110):
                return _('Unknown')  # Dead authors without date of death
            else:
                return rd.relativedelta(datetime.date.today(), self.date_of_birth["date object"]).years  # Age of living authors
        else:
            if not isinstance(self.date_of_death["date object"], datetime.date):
                return self.date_of_death["date object"] - self.date_of_birth["date object"]  # If died BC, dates are integers
            elif isinstance(self.date_of_death["date object"], datetime.date) and not isinstance(self.date_of_birth["date object"], datetime.date):
                return self.date_of_death["date object"].year - self.date_of_birth["date object"]  # If born BC and died AC, date types are mixed
            else:
                return rd.relativedelta(self.date_of_death["date object"], self.date_of_birth["date object"]).years  # If born AC, dates are datetime objects
            

    def getWorks(self, lang):
        works = squeries.retrieve_query(squeries.query_for_works_by_an_author, qname=self.wikidata_item_id, lang=lang)
        for work in works:  # Check if there are links to access the work
            if (int(work['wikisourceFullWork']['value']) > 0
                    or int(work['iaDownloads']['value']) > 0
                    or int(work['otherDownloads']['value']) > 0):
                work['downloads'] = True
            else:
                work['downloads'] = False
        return works


class Work(Parent):
    """A class for cultural works."""
    def __init__(self, wikidata_item_id):
        super().__init__(wikidata_item_id)
        self.instance_of = build_field(self.wikidata_item.get('statements', {}).get('P31'))

        image = self.wikidata_item.get('statements', {}).get('P18')
        if image is None:
            self.image = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Placeholder_book.svg/464px-Placeholder_book.svg.png"
            self.image_link = "https://commons.wikimedia.org/wiki/Commons:Welcome"
            self.image_alt_text = _('Image of a generic work. The text above it indicates that there is no free image of the work available, and that if you own one, you can click on the placeholder link to upload it.')

        else:
            image_file_name = image[0]["value"]["content"]
            image_file_name = requests.utils.quote(image_file_name)
            self.image = 'https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/' + image_file_name + '&width=400&height=100'
            self.image_link = 'https://commons.wikimedia.org/wiki/File:' + image_file_name
            self.image_alt_text = _('Image of %(title)s.', title=self.name)

        query_for_authors_response = squeries.retrieve_query(squeries.query_for_authors_of_a_work,
                                                   qname=wikidata_item_id,
                                                   lang=languages.get_locale()
                                                   )
        dict_of_authors = {}
        for result in query_for_authors_response:
            type_of_author = result.get('typeOfAuthorLabel', {}).get('value')
            if type_of_author not in dict_of_authors:
                dict_of_authors[type_of_author] = [{"name": result.get('authorLabel', {}).get('value'),
                                                    "ID": result.get('author', {}).get('value').split("/")[-1]}]
            else:
                dict_of_authors[type_of_author].append({"name": result.get('authorLabel', {}).get('value'),
                                                        "ID": result.get('author', {}).get('value').split("/")[-1]})
        self.authors = dict_of_authors

        self.country_of_origin = build_field(self.wikidata_item.get('statements', {}).get('P495'))
        self.language = build_field(self.wikidata_item.get('statements', {}).get('P407'))
        self.publication_date = build_date(self.wikidata_item.get('statements', {}).get('P577'))

        self.wikisource_links = {wikisource_version: {'title': value.get('title'),
                                                      'url': value.get('url'),
                                                      'language': get_locale().languages[wikisource_version.removesuffix('wikisource')]}
                                 for wikisource_version, value in self.wikidata_item.get('sitelinks', {}).items()
                                 if "wikisource" in wikisource_version }

        internet_archive_ID = self.wikidata_item.get('statements', {}).get('P724')
        if internet_archive_ID is None:
            self.internet_archive_link = None
        else:
            self.internet_archive_link = "https://archive.org/details/" + internet_archive_ID[0].get('value', {}).get('content')

        full_work_available_at = self.wikidata_item.get('statements', {}).get('P953')
        if full_work_available_at is None:
            self.full_work_link = None
        else:
            self.full_work_link = full_work_available_at[0].get('value', {}).get('content')

    def getCopyrightStatus(self):  # Improve this: when copyright status is None, try to estimate it by author's death or publication date
        copyright_status_response = squeries.retrieve_query(squeries.query_for_copyright_status_of_work,
                                                   qname=self.wikidata_item_id,
                                                   lang=languages.get_locale()
                                                   )
        if not copyright_status_response:
            return None
        else:
            copyright_status = []
            for claim in copyright_status_response:
                try:
                    status_dict = {
                        'status': claim.get('cstatusLabel', {}).get('value'),
                        'applies_to_jurisdiction_label': claim.get('jurisdictionLabel', {}).get('value'),
                        'applies_to_jurisdiction_id': claim.get('jurisdiction', {}).get('value').split("/")[-1],
                        'jurisdiction_is_instance_of': claim.get('jurisdictionIsInstanceOf', {}).get('value').split("/")[-1]
                        }
                    copyright_status.append(status_dict)
                except:
                    pass
            return copyright_status
        # Other attributes to be created: identifiers, form of creative work, genre, Gutenberg link, etc


class Country(Parent):
    """A class for countries."""
    def __init__(self, wikidata_item_id):
        super().__init__(wikidata_item_id)
        flag_image = self.wikidata_item.get('statements', {}).get('P41')
        if flag_image is None:
            self.flag_image = None
            self.flag_image_link = None
        else:
            flag_image_file_name = flag_image[0]["value"]["content"]
            flag_image_file_name = requests.utils.quote(flag_image_file_name)
            self.flag_image = 'https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/' + flag_image_file_name + '&width=200&height=30'
            self.flag_image_link = 'https://commons.wikimedia.org/wiki/File:' + flag_image_file_name
            self.flag_image_alt_text = _('Flag of %(country_name)s.', country_name=self.name)
        
        self.number_of_works_in_public_domain = squeries.retrieve_query(squeries.query_for_number_of_works_in_public_domain_from_a_country,
                                                         qname=self.wikidata_item_id,
                                                         lang=languages.get_locale()
                                                         )
        
    
    # Method to determine the copyright term of the country
    def getCopyrightTerm(self):
        copyright_term = squeries.retrieve_query(squeries.query_for_country_copyright_term,
                                        qname=self.wikidata_item_id,
                                        lang=languages.get_locale()
                                        )
        return copyright_term


class Term(Parent):
    """A class for copyright terms."""
    def __init__(self, wikidata_item_id):
        super().__init__(wikidata_item_id)

    # Method to get list of countries by copyright term
    def getCountries(self):
        countries = squeries.retrieve_query(squeries.query_for_countries_by_copyright_term,
                                   qname=self.wikidata_item_id,
                                   lang=languages.get_locale()
                                   )
        return countries
