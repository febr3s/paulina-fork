import pywikibot
from pywikibot import pagegenerators as pg
import squeries  # local module with SPARQL queries


wikidata_site = pywikibot.Site('wikidata', 'wikidata')


def search_author(user_search):
    search = user_search

    searchgenerator = pg.WikibaseSearchItemPageGenerator(search, site=wikidata_site, total=100)
    query_list = []
    for qresult in searchgenerator:
        query_list.append(qresult.id)
    string_query = "wd:" + " wd:".join(query_list)
    query_for_humans = squeries.query_for_humans.format(qname=string_query)
    query_generator = pg.WikidataSPARQLPageGenerator(query_for_humans, site=wikidata_site)

    generator_list = []
    for result in query_generator:
        generator_list.append(result)

    if not generator_list:
        return None
    elif len(generator_list) == 1:
        return generator_list[0].id
    else:
        # Order the results by decreasing number of sitelinks
        results_with_number_of_sitelinks = {}
        for result in generator_list:
            sitelinks = len(result.sitelinks)
            results_with_number_of_sitelinks[result] = sitelinks
        sorted_list = sorted(results_with_number_of_sitelinks.items(), key=lambda item: item[1], reverse=True)

        final_results = []
        for result in sorted_list:
            if 'en' in result[0].labels and 'en' in result[0].descriptions:
                final_results.append((result[0].labels['en'], result[0].descriptions['en'], result[0].id))
        return final_results
