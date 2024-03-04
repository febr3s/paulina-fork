# SPARQL queries module

query_for_humans = ''' SELECT ?item ?itemLabel

WHERE
{{
    VALUES ?type {{  wd:Q5 wd:Q21070568  }}
    
    ?item wdt:P31 ?type .

    VALUES ?item {{ {qname} }}

    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es". }}  
}}
        '''

query_for_works = ''' SELECT ?item ?itemLabel

WHERE
{{
  ?item ( wdt:P170 | wdt:P50 | wdt:P57 | wdt:P58 | wdt:P84 | wdt:P86 | wdt:P87 | wdt:P110 | wdt:P676 | wdt:P943 ) wd:{qname}.

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es". }}
}}

ORDER BY ASC(?itemLabel)
        '''

query_for_country_copyright_term = ''' SELECT ?item ?itemLabel

WHERE {{
  
  ?item wdt:P279 wd:Q108698760 .
        
  ?item wdt:P1001 wd:{qname}.
    
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
}}
'''

query_for_countries_by_copyright_term = ''' SELECT ?item ?itemLabel WHERE {{ VALUES ?term {{ wd:{qname} }} . ?term ( wdt:P1001|wdt:P150 ) ?item SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}'''
