# SPARQL queries module

# old query_for_works = '''SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {{ SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en, {lang}". }} {{ SELECT DISTINCT ?item WHERE {{ VALUES ?languages {{"en" "{lang}"}}. ?item ( wdt:P170 | wdt:P50 | wdt:P57 | wdt:P58 | wdt:P84 | wdt:P86 | wdt:P87 | wdt:P110 | wdt:P676 | wdt:P943 ) wd:{qname} . ?item rdfs:label ?itemLabel . FILTER(lang(?itemLabel) = ?languages ) . MINUS {{ VALUES ?typeOfItem {{ wd:Q3658341 wd:Q187931 wd:Q3375722 }} ?item wdt:P31 ?typeOfItem . }} }} }} }} ORDER BY ASC (?itemLabel)'''

query_for_works = '''
SELECT DISTINCT ?item ?itemLabel ?itemDescription ( COUNT ( DISTINCT ?wikisource ) as ?wikisourceFullWork ) ( COUNT ( DISTINCT ?iaID ) as ?iaDownloads ) ( COUNT ( DISTINCT ?download ) as ?otherDownloads ) 
WHERE 
{{  
  {{ SELECT DISTINCT ?item 
   WHERE
     {{ 
       VALUES ?languages {{ "en" "{lang}" }}.                                                                                                           
       ?item ( wdt:P170 | wdt:P50 | wdt:P57 | wdt:P58 | wdt:P84 | wdt:P86 | wdt:P87 | wdt:P110 | wdt:P676 | wdt:P943 ) wd:{qname} . 
       ?item rdfs:label ?itemLabel .
       FILTER ( lang ( ?itemLabel ) = ?languages ) . 
       MINUS {{ 
         VALUES ?typeOfItem {{ wd:Q3658341 wd:Q187931 wd:Q3375722 }} 
         ?item wdt:P31 ?typeOfItem . }} 
     }} 
  }}   
  OPTIONAL {{ ?item wdt:P724 ?iaID . }}
  OPTIONAL {{ ?item wdt:P953 ?download . }}
  OPTIONAL {{
  ?wikisource schema:about ?item .
  ?wikisource schema:isPartOf <https://en.wikisource.org/> . }}  
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en, {lang}" . }} 
}} 
GROUP BY ?item ?itemLabel ?itemDescription 
ORDER BY ASC ( ?itemLabel )
'''

query_for_countries_by_copyright_term = '''
SELECT ?item ?itemLabel 
WHERE 
{{ 
  VALUES ?term {{ wd:{qname} }} . 
  ?term ( wdt:P1001|wdt:P150 ) ?item . 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }} 
}} 
ORDER BY ASC(?itemLabel)
'''

query_for_country_copyright_term = '''
SELECT DISTINCT ?item ?itemLabel ( GROUP_CONCAT ( DISTINCT ?partLabel; SEPARATOR=", ") AS ?appliesToParts ) 
WHERE 
{{ 
  {{ ?item wdt:P279 wd:Q108698760 . }} 
  UNION 
  {{ ?item wdt:P279 wd:Q108701480 . }} 
  ?item p:P1001 ?countryStatement . 
  ?countryStatement ps:P1001 wd:{qname} . 
  OPTIONAL {{ ?countryStatement pq:P518 ?part . }} 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . 
                            ?item rdfs:label ?itemLabel . 
                            ?part rdfs:label ?partLabel . }} 
}} 
GROUP BY ?item ?itemLabel
'''

query_for_country_of_birth = '''
SELECT DISTINCT ?item ?itemLabel 
WHERE {{ 
  wd:{qname} wdt:P17 ?item . 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }} 
}}
'''

query_for_labels_of_list_of_items = '''
SELECT DISTINCT ?item ?itemLabel 
WHERE {{ 
  VALUES ?item {{ {qnames} }} .  
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} 
}}
'''

query_for_copyright_status_of_work = '''
SELECT DISTINCT ?cstatus ?cstatusLabel ?jurisdiction ?jurisdictionLabel ?jurisdictionIsInstanceOf ?jurisdictionIsInstanceOfLabel 
WHERE {{ 
  VALUES ?jurisdictionIsInstanceOf {{ wd:Q63705939 wd:Q6256 }} . 
  wd:{qname} p:P6216 ?cstatusStatement . 
  ?cstatusStatement ps:P6216 ?cstatus . 
  OPTIONAL {{ ?cstatusStatement pq:P1001 ?jurisdiction . }} 
  ?jurisdiction wdt:P31 ?jurisdictionIsInstanceOf . 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }} 
}}
'''