import requests

# Local modules
import squeries
import languages


def search_filters(gender=None, nationality=None, type_of_work=None, country_of_origin=None, in_public_domain=None) -> str:
    filters_string = ""
    if gender:
        filters_string = filters_string + f"%20haswbstatement:P21={gender}"
    if nationality:
        filters_string = filters_string + f"%20haswbstatement:P27={nationality}"
    if type_of_work:
        filters_string = filters_string + f"%20haswbstatement:P31={type_of_work}"
    if country_of_origin:
        filters_string = filters_string + f"%20haswbstatement:P495={country_of_origin}"
    if in_public_domain:
        filters_string = filters_string + f"%20haswbstatement:P7763=Q71887839|P7763=Q75700125"
    return filters_string

def search_author(user_search: str, gender:str, nationality:str, in_public_domain:bool) -> list:
    """Takes a user search string and returns a list of search results using the Wikidata API.
    Results are filtered in order to get only human beings."""
    search = requests.utils.quote(user_search)  # URL encoded
    search_url_prefix = "https://www.wikidata.org/w/api.php?action=query&generator=search&gsrlimit=200&gsrsearch="
    human_being_filter = "%20haswbstatement:P31=Q5|P31=Q21070568"
    user_filters = search_filters(gender=gender, nationality=nationality, in_public_domain=in_public_domain)
    search_url_suffix = "&prop=entityterms&wbetlanguage="
    search_language = languages.get_locale()
    search_format = "&format=json"
    search_url = search_url_prefix + search + human_being_filter + user_filters + search_url_suffix + search_language + search_format
    headers = {'user-agent': 'PaulinaApp/0.9 (https://gitlab.wikimedia.org/toolforge-repos/paulina)'}
    search_response = requests.get(search_url, headers=headers
                                   # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                   )
    search_results = search_response.json()
    complete = not ("continue" in search_results)
    try:
        search_results = search_results["query"]["pages"]
    except KeyError:  # If there are no pages, return an empty list
        return [], complete
    search_results_list = list(search_results.values())
    ordered_results = sorted(search_results_list, key=lambda x: x["index"])
    final_results = []
    for item in ordered_results:
        try:
            if item["entityterms"]["label"]:
                final_results.append(item)
        except KeyError:  # If there is no label, exclude
            pass
    return final_results, complete

def search_work(user_search: str, type_of_work: str, country_of_origin: str) -> list:
    """Takes a user search string and returns a list of search results using the Wikidata API.
    Results are filtered in order to get only works."""
    search = requests.utils.quote(user_search)  # URL encoded
    search_url_prefix = "https://www.wikidata.org/w/api.php?action=query&generator=search&gsrlimit=200&gsrsearch="
    user_filters = search_filters(type_of_work=type_of_work, country_of_origin=country_of_origin)
    search_url_suffix = "&prop=entityterms&wbetlanguage="
    search_language = languages.get_locale()
    search_format = "&format=json"
    search_url = search_url_prefix + search + user_filters + search_url_suffix + search_language + search_format
    headers = {'user-agent': 'PaulinaApp/0.9 (https://gitlab.wikimedia.org/toolforge-repos/paulina)'}
    search_response = requests.get(search_url, headers=headers
                                   # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                   )
    search_results = search_response.json()
    complete = not ("continue" in search_results)

    try:
        search_results = search_results["query"]["pages"]
    except KeyError:  # If there are no pages, return an empty list
        return [], complete
    search_results_list = list(search_results.values())
    results_q_and_index = {item["title"]: item["index"] for item in search_results_list}
    filtered_results = squeries.retrieve_query(squeries.query_for_works_from_search_results,
                                        qnames="wd:" + " wd:".join(results_q_and_index),
                                        lang=languages.get_locale()
                                        )
    # Sort the filtered query results by the index of the original search results
    ordered_filtered_results = sorted(filtered_results, key=lambda x: results_q_and_index[x["item"]["value"].split("/")[-1]])
    for work in ordered_filtered_results:  # Check if there are links to access the work
        if (int(work['wikisourceFullWork']['value']) > 0
                or int(work['iaDownloads']['value']) > 0
                or int(work['otherDownloads']['value']) > 0):
            work['downloads'] = True
        else:
            work['downloads'] = False
    return ordered_filtered_results, complete
