import requests

# Local modules
import squeries
import languages


def search_author(user_search):
    search = requests.utils.quote(user_search)  # URL encoded
    search_url_prefix = "https://www.wikidata.org/w/api.php?action=query&generator=search&gsrlimit=100&gsrsearch="
    search_url_suffix = "%20haswbstatement:P31=Q5|P31=Q21070568&prop=entityterms&wbetlanguage="
    search_language = languages.get_locale()
    search_format = "&format=json"
    search_url = search_url_prefix + search + search_url_suffix + search_language + search_format
    headers = {'user-agent': 'PaulinaApp/0.9 (https://gitlab.wikimedia.org/toolforge-repos/paulina)'}
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

def search_work(user_search):
    search = requests.utils.quote(user_search)  # URL encoded
    search_url_prefix = "https://www.wikidata.org/w/api.php?action=query&generator=search&gsrlimit=100&gsrsearch="
    search_url_suffix = "&prop=entityterms&wbetlanguage="
    search_language = languages.get_locale()
    search_format = "&format=json"
    search_url = search_url_prefix + search + search_url_suffix + search_language + search_format
    headers = {'user-agent': 'PaulinaApp/0.9 (https://gitlab.wikimedia.org/toolforge-repos/paulina)'}
    search_response = requests.get(search_url, headers=headers
                                   # , timeout=1  # If IPv6 doesn't work, force time out and use IPv4
                                   )
    search_results = search_response.json()
    try:
        search_results = search_results["query"]["pages"]
    except KeyError:  # If there are no pages, return an empty list
        return []
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
    return ordered_filtered_results
