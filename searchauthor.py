import requests
import languages


def search_author(user_search):
    search = requests.utils.quote(user_search)  # URL encoded
    search_url_prefix = "https://www.wikidata.org/w/api.php?action=query&generator=search&gsrlimit=100&gsrsearch="
    search_url_suffix = "%20haswbstatement:P31=Q5|P31=Q21070568&prop=entityterms&wbetlanguage="
    search_language = languages.get_locale()
    search_format = "&format=json"
    search_url = search_url_prefix + search + search_url_suffix + search_language + search_format
    headers = {'user-agent': 'PaulinaApp/0.1 (https://gitlab.wikimedia.org/toolforge-repos/paulina)'}
    search_response = requests.get(search_url, headers=headers
                                   # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                   )
    search_results = search_response.json()
    try:
        search_results = search_results["query"]["pages"]
    except KeyError:  # If there are no pages, return an empty list
        return []
    search_results_list = list(search_results.values())
    ordered_results = sorted(search_results_list, key=lambda x: x["index"])
    final_results = []
    for item in ordered_results:
        try:
            if item["entityterms"]["label"]:
                final_results.append(item)
        except KeyError:  # If there is no label, exclude
            pass
    return final_results
