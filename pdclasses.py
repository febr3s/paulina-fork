from flask import current_app
from flask_babel import _, format_date, get_locale
import datetime  # to calculate if the works are in public domain
import dateutil.relativedelta as rd
import requests

# Local modules
import squeries
import languages


def build_field(wikidata_statement: list[dict], field_type: str ="item_label") -> str | None:
    """Function to return a field from a Wikidata statement.
    If the statement does not exist, it returns None.
    If the statement exists and has a preferred value, it returns the preferred value.
    If the statement exists and does not have a preferred value, it returns the first value.
    The default behavior of the function is to return the item label of the value,
    but if the optional argument 'field_type' is set to 'plain_value',
    the function returns the Wikidata item ID or text string of the value."""
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
            if field_type == "plain_value":
                return [key for key, value in dictionary_of_claims.items()
                        if value == "preferred" and key not in ["novalue", "somevalue"]][0]
            else:
                return [retrieve_item(key, data_type="labels").get(languages.get_locale())
                        for key, value in dictionary_of_claims.items()
                        if value == "preferred" and key not in ["novalue", "somevalue"]][0]

        else:  # If there is not a preferred value, pick the first value
            first_claim = next(iter(dictionary_of_claims))
            if first_claim in ["novalue", "somevalue"]:  # If the value is not a Wikidata item ID
                if field_type == "plain_value":
                    return None
                else:
                    return first_claim
                
            else:  # If the value is a Wikidata item ID
                if field_type == "plain_value":
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
    headers = {'user-agent': current_app.config['USER_AGENT']}
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
        self.commons_link = self.wikidata_item.get('sitelinks', {}).get('commonswiki', {}).get('url')
        self.wikiquote_link = self.wikidata_item.get('sitelinks', {}).get(languages.get_locale() + 'wikiquote', {}).get('url')


class Author(Parent):
    """A class for authors."""
    def __init__(self, wikidata_item_id):
        super().__init__(wikidata_item_id)

        """ Prevent loading an author page if the Wikidata item does not exist or it is not about a human:            
            - Raise a "TypeError: 'NoneType' object is not iterable" if the item does not exist.
            - Raise an "Exception: Not a human" if the item is not about a human."""
        is_human = False
        for statement in self.wikidata_item.get('statements', {}).get('P31'):
            if statement.get('value', {}).get('content') in ["Q5", "Q21070568"]:
                is_human = True
        if is_human is False:
            raise Exception("Not a human")

        self.wikisource_link = self.wikidata_item.get('sitelinks', {}).get(languages.get_locale() + 'wikisource', {}).get('url')
        self.official_website = build_field(self.wikidata_item.get('statements', {}).get('P856'), field_type="plain_value")
        
        # Nationality - store both label and QID
        self.nationality = build_field(self.wikidata_item.get('statements', {}).get('P27'))
        self.nationality_qid = build_field(self.wikidata_item.get('statements', {}).get('P27'), field_type="plain_value")
        
        # Gender - store both label and QID
        self.gender = build_field(self.wikidata_item.get('statements', {}).get('P21'))
        self.gender_qid = build_field(self.wikidata_item.get('statements', {}).get('P21'), field_type="plain_value")
        
        self.date_of_birth = build_date(self.wikidata_item.get('statements', {}).get('P569'))
        self.date_of_death = build_date(self.wikidata_item.get('statements', {}).get('P570'))
        
        # Ethnicity - store both label and QID
        self.ethnicity = build_field(self.wikidata_item.get('statements', {}).get('P172'))
        self.ethnicity_qid = build_field(self.wikidata_item.get('statements', {}).get('P172'), field_type="plain_value")

        if self.date_of_death and isinstance(self.date_of_death["date object"], datetime.date):
            self.date_enter_public_domain = self.date_of_death['date object'].year + 101
        else:
            self.date_enter_public_domain = None

        # Occupation - store both labels and QIDs
        occupations = self.wikidata_item.get('statements', {}).get('P106')
        if occupations is None:
            self.occupation = None
            self.occupation_qid = None
        else:
            occupations_ids = [occupation.get('value', {}).get('content') for occupation in occupations]
            occupations_labels_response = squeries.retrieve_query(squeries.query_for_labels_of_list_of_items,
                                                    qnames="wd:" + " wd:".join(occupations_ids),
                                                    lang=languages.get_locale()
                                                    )
            
            # Build a mapping of QID -> label to ensure correct order
            qid_to_label = {}
            for item in occupations_labels_response:
                qid = item.get('item', {}).get('value', '').split('/')[-1]  # Extract QID from full URI
                label = item.get('itemLabel', {}).get('value')
                if qid and label:
                    qid_to_label[qid] = label
            
            # Maintain the original order of QIDs
            self.occupation = [qid_to_label.get(qid, qid) for qid in occupations_ids]
            # Store QIDs as comma-separated string
            self.occupation_qid = ','.join(occupations_ids) if occupations_ids else None
            
        # Place of birth - store both label and QID
        place_of_birth = self.wikidata_item.get('statements', {}).get('P19')
        self.place_of_birth = build_field(place_of_birth)
        self.place_of_birth_qid = build_field(place_of_birth, field_type="plain_value")

        # Country of birth is built taking the place of birth and looking in what country it is.
        if place_of_birth:
            place_of_birth_Q = build_field(place_of_birth, field_type="plain_value")
            if place_of_birth_Q:
                country_of_birth = squeries.retrieve_query(squeries.query_for_country_of_birth,
                                                  qname=place_of_birth_Q,
                                                  lang=languages.get_locale()
                                                  )
                try:
                    self.country_of_birth = country_of_birth[0].get('itemLabel', {}).get('value')
                    # Store the country QID (extract from the country_of_birth query result)
                    self.country_of_birth_qid = country_of_birth[0].get('item', {}).get('value').split("/")[-1] if country_of_birth[0].get('item') else None
                except:
                    self.country_of_birth = None
                    self.country_of_birth_qid = None
            else:
                self.country_of_birth = None
                self.country_of_birth_qid = None
        else:
            self.country_of_birth = None
            self.country_of_birth_qid = None

        image = build_field(self.wikidata_item.get('statements', {}).get('P18'), field_type="plain_value")
        if image is None:
            self.image = "https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/No_portrait_(female).svg&width=400&height=200"
            self.image_link = "https://commons.wikimedia.org/wiki/Commons:Welcome"
            self.image_alt_text = _('Image of a generic human silhouette. The text above it indicates that there is no free image of the person available, and that if you own one, you can click on the placeholder link.')
        else:
            image_file_name = requests.utils.quote(image)
            self.image = 'https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/' + image_file_name + '&width=400&height=200'
            self.image_link = 'https://commons.wikimedia.org/wiki/File:' + image_file_name
            self.image_alt_text = _('Image of %(name)s.', name=self.name)

    def isInPublicDomain(self):
        copyright_status_response = squeries.retrieve_query(squeries.query_for_copyright_status_of_author,
                                                   qname=self.wikidata_item_id,
                                                   lang=languages.get_locale()
                                                   )
        if not copyright_status_response:
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
        else:
            copyright_status = []
            for claim in copyright_status_response:
                try:
                    status_dict = {
                        'status_label': claim.get('cstatusLabel', {}).get('value'),
                        'status_id': claim.get('cstatus', {}).get('value').split("/")[-1],
                        'applies_to_jurisdiction_label': claim.get('jurisdictionLabel', {}).get('value'),
                        'applies_to_jurisdiction_id': claim.get('jurisdiction', {}).get('value').split("/")[-1] if claim.get('jurisdiction', {}).get('value') else None,
                        'jurisdiction_is_instance_of': claim.get('jurisdictionIsInstanceOf', {}).get('value').split("/")[-1] if claim.get('jurisdictionIsInstanceOf', {}).get('value') else None
                        }
                    copyright_status.append(status_dict)
                except:
                    pass
            return copyright_status

    def ageOfAuthor(self):
        if self.date_of_birth is None:
            return None  # Authors with date of birth unavailable
        if self.date_of_death is None:
            if not isinstance(self.date_of_birth["date object"], datetime.date) or self.date_of_birth["date object"].year < (datetime.date.today().year - 110):
                return None  # Dead authors without date of death
            else:
                return rd.relativedelta(datetime.date.today(), self.date_of_birth["date object"]).years  # Age of living authors
        else:
            if not isinstance(self.date_of_death["date object"], datetime.date):
                return self.date_of_death["date object"] - self.date_of_birth["date object"]  # If died BC, dates are integers
            elif isinstance(self.date_of_death["date object"], datetime.date) and not isinstance(self.date_of_birth["date object"], datetime.date):
                return self.date_of_death["date object"].year - self.date_of_birth["date object"]  # If born BC and died AC, date types are mixed
            else:
                return rd.relativedelta(self.date_of_death["date object"], self.date_of_birth["date object"]).years  # If born AC, dates are datetime objects
            

    def getWorks(self, limit=50, offset=0):
        """Get works by this author with pagination support.

        Args:
            lang: Language code for labels
            limit: Maximum number of results to return (default: 50)
            offset: Number of results to skip (default: 0)

        Returns:
            List of works with download information
        """

        search_url_prefix = "https://www.wikidata.org/w/api.php?action=query&list=search&srlimit=50&srprop=&srsearch="
        works_by_this_author_filter = (f"%20haswbstatement:P170={self.wikidata_item_id}|P50={self.wikidata_item_id}|"
                       f"P57={self.wikidata_item_id}|P58={self.wikidata_item_id}|P84={self.wikidata_item_id}|"
                       f"P86={self.wikidata_item_id}|P87={self.wikidata_item_id}|P110={self.wikidata_item_id}|"
                       f"P676={self.wikidata_item_id}|P943={self.wikidata_item_id}|P175={self.wikidata_item_id}|"
                       f"P9191={self.wikidata_item_id}|P10837={self.wikidata_item_id}"
                       f"%20-haswbstatement:P31=Q3658341|P31=Q187931|P31=Q3375722")
        offset_param = f"&sroffset={offset}" if offset > 0 else ""
        search_format = "&format=json"
        search_url = search_url_prefix + works_by_this_author_filter + offset_param + search_format
        headers = {'user-agent': current_app.config['USER_AGENT']}
        search_response = requests.get(search_url, headers=headers
                                   # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                   )
        search_results = search_response.json()

        complete = not ("continue" in search_results)
        continue_offset = search_results.get("continue", {}).get("sroffset")
        results_quantity = search_results.get("query", {}).get("searchinfo", {}).get("totalhits")
        if not search_results.get("query", {}).get("search"):
            return {}, complete, continue_offset, results_quantity
        search_results = search_results["query"]["search"]
        search_results_qids = [search_result["title"] for search_result in search_results]
        search_results_qids = "|".join(search_results_qids)

        url_for_results_data = (f"https://www.wikidata.org/w/api.php?action=wbgetentities"
                                        f"&ids={search_results_qids}&props=labels|descriptions|sitelinks|claims"
                                        f"&languages={languages.get_locale()}&languagefallback=&format=json")

        results_data_response = requests.get(url_for_results_data, headers=headers
                                    # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                    )
        results_data = results_data_response.json()
        results_data = results_data.get("entities")

        # Check if there are downloads to access the work
        for result in results_data.values():
            if result.get("claims"):
                # If Internet Archive ID or work available at URL
                if "P724" in result["claims"] or "P953" in result["claims"]:
                    result["downloads"] = True
            if result.get("sitelinks"):
                for sitelink in result["sitelinks"]:
                    if sitelink.endswith("wikisource"):
                        result["downloads"] = True

        return results_data, complete, continue_offset, results_quantity


def get_author_field_edit_eligibility(wikidata_item):
    """Check which fields have only one value and are therefore editable."""
    statements = wikidata_item.get('statements', {})
    
    # Fields that are always locked regardless of value count
    always_locked = {'countryOfBirth'} # This field is derived from place of birth, so it should not be directly editable.
    
    # Fields that are always editable regardless of value count
    always_editable = {'occupation'}
    
    field_properties = {
        'nationality':  'P27',
        'ethnicity':    'P172',
        'gender':       'P21',
        'dateOfBirth':  'P569',
        'occupation':   'P106',
        'placeOfBirth': 'P19',
        'dateOfDeath':  'P570',
    }
    
    eligibility = {}
    for field, pid in field_properties.items():
        if field in always_locked:
            eligibility[field] = False
        elif field in always_editable:
            eligibility[field] = True
        else:
            count = len(statements.get(pid, []))
            eligibility[field] = (count <= 1)
    
    eligibility['countryOfBirth'] = False  # Always locked — derived field
    return eligibility

class Work(Parent):
    """A class for cultural works."""
    def __init__(self, wikidata_item_id):
        super().__init__(wikidata_item_id)
        self.instance_of = build_field(self.wikidata_item.get('statements', {}).get('P31'))

        image = build_field(self.wikidata_item.get('statements', {}).get('P18'), field_type="plain_value")
        if image is None:
            self.image = "https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/Placeholder_book.svg&width=400&height=200"
            self.image_link = "https://commons.wikimedia.org/wiki/Commons:Welcome"
            self.image_alt_text = _('Image of a generic work. The text above it indicates that there is no free image of the work available, and that if you own one, you can click on the placeholder link to upload it.')
        else:
            image_file_name = requests.utils.quote(image)
            self.image = 'https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/' + image_file_name + '&width=400&height=200'
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
        self.country_of_origin_qid = build_field(self.wikidata_item.get('statements', {}).get('P495'), field_type="plain_value")
        self.language = build_field(self.wikidata_item.get('statements', {}).get('P407'))
        self.language_qid = build_field(self.wikidata_item.get('statements', {}).get('P407'), field_type="plain_value")
        self.publication_date = build_date(self.wikidata_item.get('statements', {}).get('P577'))
        self.creation_date = build_date(self.wikidata_item.get('statements', {}).get('P571'))

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
                        'status_label': claim.get('cstatusLabel', {}).get('value'),
                        'status_id': claim.get('cstatus', {}).get('value').split("/")[-1],
                        'applies_to_jurisdiction_label': claim.get('jurisdictionLabel', {}).get('value'),
                        'applies_to_jurisdiction_id': claim.get('jurisdiction', {}).get('value').split("/")[-1] if claim.get('jurisdiction', {}).get('value') else None,
                        'jurisdiction_is_instance_of': claim.get('jurisdictionIsInstanceOf', {}).get('value').split("/")[-1] if claim.get('jurisdictionIsInstanceOf', {}).get('value') else None
                        }
                    copyright_status.append(status_dict)
                except:
                    pass
            return copyright_status
        # Other attributes to be created: identifiers, form of creative work, genre, Gutenberg link, etc

def get_work_field_edit_eligibility(wikidata_item):
    """Check which work fields have only one value and are therefore editable."""
    statements = wikidata_item.get('statements', {})
    field_properties = {
        'publicationDate':  'P577',
        'creationDate':     'P571',
        'workLanguage':     'P407',
        'countryOfOrigin':  'P495',
    }
    eligibility = {}
    for field, pid in field_properties.items():
        count = len(statements.get(pid, []))
        eligibility[field] = (count <= 1)
    return eligibility

class Country(Parent):
    """A class for countries."""
    def __init__(self, wikidata_item_id):
        super().__init__(wikidata_item_id)
        flag_image = build_field(self.wikidata_item.get('statements', {}).get('P41'), field_type="plain_value")
        if flag_image is None:
            self.flag_image = None
            self.flag_image_link = None
        else:
            flag_image_file_name = requests.utils.quote(flag_image)
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
