from flask import current_app
import requests

# Local modules
import squeries
import languages
import filters


def search_filters(gender=None, nationality=None, creative_area=None,
                   in_public_domain=None, type_of_work=None, country_of_origin=None) -> str:
    filters_string = ""
    if gender:
        filters_string = filters_string + f"%20haswbstatement:P21={gender}"
    if nationality:
        filters_string = filters_string + f"%20haswbstatement:P27={nationality}"
    if creative_area:
        for ca in filters.CREATIVE_AREAS:
            if creative_area == ca["area_value"]:
                selected_area = ca
        filters_string = filters_string + f"%20haswbstatement:{'|'.join("P106=" + qid for qid in selected_area["qids"]) }"
    if in_public_domain:
        filters_string = filters_string + f"%20haswbstatement:P7763=Q71887839|P7763=Q75700125"
    if type_of_work:
        for tow in filters.TYPES_OF_WORK:
            if type_of_work == tow["type_value"]:
                selected_type = tow
        filters_string = filters_string + f"%20haswbstatement:{'|'.join("P31=" + qid for qid in selected_type["qids"]) }"
        # filters_string = filters_string + f"%20haswbstatement:P31={type_of_work}"
    if country_of_origin:
        filters_string = filters_string + f"%20haswbstatement:P495={country_of_origin}|P17={country_of_origin}"
    return filters_string

def search_author(user_search: str, gender:str, nationality:str, 
                  creative_area:str, in_public_domain:bool, offset:int=0) -> tuple:
    """The function takes a user search string and search filters.
    Then it applies a filter in order to get only human beings.
    It returns a tuple that includes:
    - a list of search results,
    - a boolean indicating if search results are complete,
    - the continue offset of the results,
    - and the total result hits of the search."""
    search = requests.utils.quote(user_search)  # URL encoded
    search_url_prefix = "https://www.wikidata.org/w/api.php?action=query&list=search&srlimit=50&srprop=&srsearch="
    human_being_filter = "%20haswbstatement:P31=Q5|P31=Q21070568"
    user_filters = search_filters(gender=gender, nationality=nationality,
                                  creative_area=creative_area, in_public_domain=in_public_domain)
    offset_param = f"&sroffset={offset}" if offset > 0 else ""
    search_format = "&format=json"
    search_url = search_url_prefix + search + human_being_filter + user_filters + offset_param + search_format
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
                                       f"&ids={search_results_qids}&props=labels|descriptions"
                                       f"&languages={languages.get_locale()}&languagefallback=&format=json")

    results_data_response = requests.get(url_for_results_data, headers=headers
                                   # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                   )
    results_data = results_data_response.json()
    results_data = results_data.get("entities")
    return results_data, complete, continue_offset, results_quantity

def search_work(user_search: str, type_of_work: str, country_of_origin: str, offset:int=0) -> tuple:
    """The function takes a user search string and search filters.
    Results are filtered in order to get only works.
    It returns a tuple that includes:
    - a list of search results,
    - a boolean indicating if search results are complete,
    - the continue offset of the results,
    - and the total result hits of the search."""
    search = requests.utils.quote(user_search)  # URL encoded
    search_url_prefix = "https://www.wikidata.org/w/api.php?action=query&list=search&srlimit=50&srprop=&srsearch="
    work_filter = "%20haswbstatement:P170|P50|P57|P58|P84|P86|P87|P110|P676|P943|P175|P9191|P10837%20-haswbstatement:P31=Q3658341|P31=Q187931|P31=Q3375722|P31=Q13442814"
    user_filters = search_filters(type_of_work=type_of_work, country_of_origin=country_of_origin)
    offset_param = f"&sroffset={offset}" if offset > 0 else ""
    search_format = "&format=json"
    search_url = search_url_prefix + search + work_filter + user_filters + offset_param + search_format
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
