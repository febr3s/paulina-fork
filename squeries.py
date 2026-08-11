# SPARQL and GraphQL queries module
from flask import current_app
import requests


def retrieve_query(query: str, **kwargs: str) -> list[dict]:
    """Takes a SPARQL query, sends it to the Wikidata Query Service and returns a list of results."""
    query_url_prefix = 'https://query.wikidata.org/sparql?query='
    query = query.format(**kwargs)
    query = requests.utils.quote(query)  # URL encoded
    request_json_format = '&format=json'
    query_url = query_url_prefix + query + request_json_format
    headers = {'user-agent': current_app.config['USER_AGENT']}
    query_results = requests.get(query_url, headers=headers)
    query_results = query_results.json()
    query_results = query_results["results"]["bindings"]
    return query_results


def retrieve_graphql_query(query: str, **kwargs: str):
    """Takes a GraphQL query, makes de API call and returns the results."""
    query_endpoint = "https://www.wikidata.org/w/api.php?action=wbgraphql&format=json"
    query_dict = {}
    query_dict["query"] = query.format(**kwargs)
    headers = {'user-agent': current_app.config['USER_AGENT']}
    query_results = requests.post(query_endpoint, json=query_dict, headers=headers, timeout=5)
    query_results = query_results.json()
    query_results = query_results["data"]
    return query_results


query_for_works_by_an_author = '''
SELECT DISTINCT ?item ?itemLabel ?itemDescription ( COUNT ( DISTINCT ?wikisource ) as ?wikisourceFullWork ) ( COUNT ( DISTINCT ?iaID ) as ?iaDownloads ) ( COUNT ( DISTINCT ?download ) as ?otherDownloads ) 
WHERE 
{{ 
  {{ SELECT DISTINCT ?item 
   WHERE
     {{ 
       VALUES ?languages {{ "{lang}" "mul" "en" }}. 
       ?item ( wdt:P170 | wdt:P50 | wdt:P57 | wdt:P58 | wdt:P84 | wdt:P86 | wdt:P87 | wdt:P110 | wdt:P676 | wdt:P943 | wdt:P175 | wdt:P9191 | wdt:P10837 ) wd:{qname} . 
       ?item rdfs:label ?itemLabel .
       FILTER ( LANG( ?itemLabel ) = ?languages ) . 
       MINUS {{ 
         VALUES ?typeOfItem {{ wd:Q3658341 wd:Q187931 wd:Q3375722 }} 
         ?item wdt:P31 ?typeOfItem . }} 
     }} 
   ORDER BY ASC ( ?itemLabel ) 
   {limit_clause} 
   {offset_clause} 
  }} 
  OPTIONAL {{ ?item wdt:P724 ?iaID . }}
  OPTIONAL {{ ?item wdt:P953 ?download . }}
  OPTIONAL {{
  ?wikisource schema:about ?item .
  ?wikisource schema:isPartOf [ wikibase:wikiGroup "wikisource" ] }} 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}, mul, en" . }} 
}} 
GROUP BY ?item ?itemLabel ?itemDescription 
ORDER BY ASC ( ?itemLabel )
'''

query_for_countries_by_copyright_term = '''
SELECT DISTINCT ?item ?itemLabel ?flag 
WHERE 
{{ 
  wd:{qname} wdt:P527?/wdt:P1001 ?item . 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}, mul, en" . }} 
  OPTIONAL {{ ?item wdt:P41 ?flag . }}
}} 
ORDER BY ?itemLabel
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
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}, mul, en" . 
                            ?item rdfs:label ?itemLabel . 
                            ?part rdfs:label ?partLabel . }} 
}} 
GROUP BY ?item ?itemLabel
'''

query_for_all_countries_info = '''
SELECT DISTINCT ?item ?itemLabel ?itemDescription ?flag ( GROUP_CONCAT(DISTINCT ?termLabel; SEPARATOR=", " ) as ?terms ) 
WHERE 
{{ 
  VALUES ?item {{ wd:Q889 wd:Q222 wd:Q262 wd:Q228 wd:Q916 wd:Q781 wd:Q414 wd:Q399 wd:Q408 wd:Q40 wd:Q227 wd:Q398 wd:Q902 wd:Q244 
                              wd:Q184 wd:Q31 wd:Q242 wd:Q962 wd:Q917 wd:Q750 wd:Q225 wd:Q963 wd:Q155 wd:Q921 wd:Q219 wd:Q965 wd:Q967 
                              wd:Q424 wd:Q1009 wd:Q16 wd:Q1011 wd:Q929 wd:Q657 wd:Q298 wd:Q739 wd:Q970 wd:Q800 wd:Q224 wd:Q241 wd:Q229 
                              wd:Q213 wd:Q974 wd:Q35 wd:Q977 wd:Q784 wd:Q786 wd:Q574 wd:Q736 wd:Q79 wd:Q792 wd:Q983 wd:Q986 wd:Q191 
                              wd:Q1050 wd:Q115 wd:Q4628 wd:Q702 wd:Q712 wd:Q33 wd:Q142 wd:Q1000 wd:Q230 wd:Q183 wd:Q117 wd:Q41 wd:Q223 
                              wd:Q769 wd:Q774 wd:Q1006 wd:Q1007 wd:Q734 wd:Q790 wd:Q783 wd:Q28 wd:Q189 wd:Q668 wd:Q252 wd:Q794 wd:Q796 
                              wd:Q801 wd:Q38 wd:Q1008 wd:Q766 wd:Q17 wd:Q810 wd:Q232 wd:Q114 wd:Q710 wd:Q1246 wd:Q817 wd:Q813 wd:Q819 
                              wd:Q211 wd:Q822 wd:Q1013 wd:Q1014 wd:Q1016 wd:Q347 wd:Q37 wd:Q32 wd:Q1019 wd:Q1020 wd:Q833 wd:Q826 wd:Q912 
                              wd:Q233 wd:Q709 wd:Q1025 wd:Q1027 wd:Q96 wd:Q217 wd:Q235 wd:Q711 wd:Q236 wd:Q1028 wd:Q1029 wd:Q836 wd:Q1030 
                              wd:Q697 wd:Q837 wd:Q55 wd:Q664 wd:Q811 wd:Q1032 wd:Q1033 wd:Q423 wd:Q221 wd:Q20 wd:Q842 wd:Q843 wd:Q695 
                              wd:Q804 wd:Q691 wd:Q733 wd:Q148 wd:Q419 wd:Q928 wd:Q36 wd:Q45 wd:Q846 wd:Q27 wd:Q971 wd:Q218 wd:Q159 
                              wd:Q1037 wd:Q763 wd:Q760 wd:Q757 wd:Q683 wd:Q238 wd:Q851 wd:Q1041 wd:Q403 wd:Q1042 wd:Q1044 wd:Q334 wd:Q214 
                              wd:Q215 wd:Q685 wd:Q1045 wd:Q258 wd:Q884 wd:Q958 wd:Q29 wd:Q854 wd:Q219060 wd:Q1049 wd:Q730 wd:Q34 wd:Q39 
                              wd:Q858 wd:Q1039 wd:Q865 wd:Q863 wd:Q924 wd:Q869 wd:Q778 wd:Q1005 wd:Q945 wd:Q678 wd:Q754 wd:Q948 wd:Q43 
                              wd:Q874 wd:Q672 wd:Q1036 wd:Q212 wd:Q878 wd:Q145 wd:Q30 wd:Q77 wd:Q265 wd:Q686 wd:Q237 wd:Q717 wd:Q881 
                              wd:Q805 wd:Q953 wd:Q954 }} 
  OPTIONAL {{ 
    ?term wdt:P279 wd:Q108698760 . 
    ?term wdt:P1001 ?item . }} 
  OPTIONAL {{ ?item wdt:P41 ?flag . }} 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}, mul, en". 
                            ?item rdfs:label ?itemLabel . 
                            ?term rdfs:label ?termLabel . 
                            ?item schema:description ?itemDescription . }} 
}} 
GROUP BY ?item ?itemLabel ?itemDescription ?flag 
ORDER BY ?itemLabel
'''

# keys_for_countries = {
# "Q889": "Afghanistan",
# "Q222": "Albania",
# "Q262": "Algeria",
# "Q228": "Andorra",
# "Q916": "Angola",
# "Q781": "Antigua and Barbuda",
# "Q414": "Argentina",
# "Q399": "Armenia",
# "Q408": "Australia",
# "Q40": "Austria",
# "Q227": "Azerbaijan",
# "Q398": "Bahrain",
# "Q902": "Bangladesh",
# "Q244": "Barbados",
# "Q184": "Belarus",
# "Q31": "Belgium",
# "Q242": "Belize",
# "Q962": "Benin",
# "Q917": "Bhutan",
# "Q750": "Bolivia",
# "Q225": "Bosnia and Herzegovina",
# "Q963": "Botswana",
# "Q155": "Brazil",
# "Q921": "Brunei Darussalam",
# "Q219": "Bulgaria",
# "Q965": "Burkina Faso",
# "Q967": "Burundi",
# "Q424": "Cambodia",
# "Q1009": "Cameroon",
# "Q16": "Canada",
# "Q1011": "Cape Verde",
# "Q929": "Central African Republic",
# "Q657": "Chad",
# "Q298": "Chile",
# "Q739": "Colombia",
# "Q970": "Comoros",
# "Q800": "Costa Rica",
# "Q224": "Croatia",
# "Q241": "Cuba",
# "Q229": "Cyprus",
# "Q213": "Czech Republic",
# "Q974": "Democratic Republic of the Congo",
# "Q35": "Denmark",
# "Q977": "Djibouti",
# "Q784": "Dominica",
# "Q786": "Dominican Republic",
# "Q574": "East Timor",
# "Q736": "Ecuador",
# "Q79": "Egypt",
# "Q792": "El Salvador",
# "Q983": "Equatorial Guinea",
# "Q986": "Eritrea",
# "Q191": "Estonia",
# "Q1050": "Eswatini",
# "Q115": "Ethiopia",
# "Q4628": "Faroe Islands",
# "Q702": "Federated States of Micronesia",
# "Q712": "Fiji",
# "Q33": "Finland",
# "Q142": "France",
# "Q1000": "Gabon",
# "Q230": "Georgia",
# "Q183": "Germany",
# "Q117": "Ghana",
# "Q41": "Greece",
# "Q223": "Greenland",
# "Q769": "Grenada",
# "Q774": "Guatemala",
# "Q1006": "Guinea",
# "Q1007": "Guinea-Bissau",
# "Q734": "Guyana",
# "Q790": "Haiti",
# "Q783": "Honduras",
# "Q28": "Hungary",
# "Q189": "Iceland",
# "Q668": "India",
# "Q252": "Indonesia",
# "Q794": "Iran",
# "Q796": "Iraq",
# "Q801": "Israel",
# "Q38": "Italy",
# "Q1008": "Ivory Coast",
# "Q766": "Jamaica",
# "Q17": "Japan",
# "Q810": "Jordan",
# "Q232": "Kazakhstan",
# "Q114": "Kenya",
# "Q710": "Kiribati",
# "Q1246": "Kosovo",
# "Q817": "Kuwait",
# "Q813": "Kyrgyzstan",
# "Q819": "Laos",
# "Q211": "Latvia",
# "Q822": "Lebanon",
# "Q1013": "Lesotho",
# "Q1014": "Liberia",
# "Q1016": "Libya",
# "Q347": "Liechtenstein",
# "Q37": "Lithuania",
# "Q32": "Luxembourg",
# "Q1019": "Madagascar",
# "Q1020": "Malawi",
# "Q833": "Malaysia",
# "Q826": "Maldives",
# "Q912": "Mali",
# "Q233": "Malta",
# "Q709": "Marshall Islands",
# "Q1025": "Mauritania",
# "Q1027": "Mauritius",
# "Q96": "Mexico",
# "Q217": "Moldova",
# "Q235": "Monaco",
# "Q711": "Mongolia",
# "Q236": "Montenegro",
# "Q1028": "Morocco",
# "Q1029": "Mozambique",
# "Q836": "Myanmar",
# "Q1030": "Namibia",
# "Q697": "Nauru",
# "Q837": "Nepal",
# "Q55": "Netherlands",
# "Q664": "New Zealand",
# "Q811": "Nicaragua",
# "Q1032": "Niger",
# "Q1033": "Nigeria",
# "Q423": "North Korea",
# "Q221": "North Macedonia",
# "Q20": "Norway",
# "Q842": "Oman",
# "Q843": "Pakistan",
# "Q695": "Palau",
# "Q804": "Panama",
# "Q691": "Papua New Guinea",
# "Q733": "Paraguay",
# "Q148": "People's Republic of China",
# "Q419": "Peru",
# "Q928": "Philippines",
# "Q36": "Poland",
# "Q45": "Portugal",
# "Q846": "Qatar",
# "Q27": "Republic of Ireland",
# "Q971": "Republic of the Congo",
# "Q218": "Romania",
# "Q159": "Russia",
# "Q1037": "Rwanda",
# "Q763": "Saint Kitts and Nevis",
# "Q760": "Saint Lucia",
# "Q757": "Saint Vincent and the Grenadines",
# "Q683": "Samoa",
# "Q238": "San Marino",
# "Q851": "Saudi Arabia",
# "Q1041": "Senegal",
# "Q403": "Serbia",
# "Q1042": "Seychelles",
# "Q1044": "Sierra Leone",
# "Q334": "Singapore",
# "Q214": "Slovakia",
# "Q215": "Slovenia",
# "Q685": "Solomon Islands",
# "Q1045": "Somalia",
# "Q258": "South Africa",
# "Q884": "South Korea",
# "Q958": "South Sudan",
# "Q29": "Spain",
# "Q854": "Sri Lanka",
# "Q219060": "State of Palestine",
# "Q1049": "Sudan",
# "Q730": "Suriname",
# "Q34": "Sweden",
# "Q39": "Switzerland",
# "Q858": "Syria",
# "Q1039": "São Tomé and Príncipe",
# "Q865": "Taiwan",
# "Q863": "Tajikistan",
# "Q924": "Tanzania",
# "Q869": "Thailand",
# "Q778": "The Bahamas",
# "Q1005": "The Gambia",
# "Q945": "Togo",
# "Q678": "Tonga",
# "Q754": "Trinidad and Tobago",
# "Q948": "Tunisia",
# "Q43": "Turkey",
# "Q874": "Turkmenistan",
# "Q672": "Tuvalu",
# "Q1036": "Uganda",
# "Q212": "Ukraine",
# "Q878": "United Arab Emirates",
# "Q145": "United Kingdom",
# "Q30": "United States of America",
# "Q77": "Uruguay",
# "Q265": "Uzbekistan",
# "Q686": "Vanuatu",
# "Q237": "Vatican City",
# "Q717": "Venezuela",
# "Q881": "Vietnam",
# "Q805": "Yemen",
# "Q953": "Zambia",
# "Q954": "Zimbabwe"
# }

query_for_country_of_birth = '''
SELECT DISTINCT ?item ?itemLabel 
WHERE {{ 
  wd:{qname} wdt:P17 ?item . 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}, mul, en" . }} 
}}
'''

graphql_query_for_country_of_birth = '''
query {{
  item(id: "{qname}") {{
    country: statements(propertyId: "P17") {{
      value {{
        ... on ItemValue {{
          id
          labelWithLanguageFallback(languageCode: "{lang}") {{
            languageCode
            value
          }}
        }}
      }}
    }}
  }}
}}
'''

query_for_copyright_status_of_work = '''
SELECT DISTINCT ?cstatus ?cstatusLabel ?jurisdiction ?jurisdictionLabel ?jurisdictionIsInstanceOf ?jurisdictionIsInstanceOfLabel 
WHERE {{ 
  wd:{qname} p:P6216 ?cstatusStatement . 
  ?cstatusStatement ps:P6216 ?cstatus . 
  OPTIONAL {{ 
  VALUES ?jurisdictionIsInstanceOf {{ wd:Q63705939 wd:Q6256 }} . 
  ?cstatusStatement pq:P1001 ?jurisdiction . 
  ?jurisdiction wdt:P31 ?jurisdictionIsInstanceOf . }} 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}, mul, en" . }} 
}}
'''

graphql_query_for_copyright_status_of_work = '''
query copyrightStatusOfWork {{
  item(id: "{qname}") {{
    copyrightStatus: statements(propertyId: "P6216") {{
      value {{
        ... on ItemValue {{
          id
          labelWithLanguageFallback(languageCode: "{lang}") {{
            languageCode
            value
          }}
        }}
      }}
      jurisdiction: qualifiers(propertyId: "P1001") {{
        value {{
          ... on ItemValue {{
            id
            labelWithLanguageFallback(languageCode: "{lang}") {{
              languageCode
              value
            }}
          }}
        }}
      }}
    }}
  }}
}}
'''

query_for_copyright_status_of_author = '''
SELECT DISTINCT ?cstatus ?cstatusLabel ?jurisdiction ?jurisdictionLabel ?jurisdictionIsInstanceOf ?jurisdictionIsInstanceOfLabel 
WHERE {{ 
  wd:{qname} p:P7763 ?cstatusStatement . 
  ?cstatusStatement ps:P7763 ?cstatus . 
  OPTIONAL {{ 
  VALUES ?jurisdictionIsInstanceOf {{ wd:Q63705939 wd:Q6256 wd:Q82794 wd:Q1140229 }} . 
  ?cstatusStatement pq:P1001 ?jurisdiction . 
  ?jurisdiction wdt:P31 ?jurisdictionIsInstanceOf . }} 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}, mul, en" . }} 
}}
'''

graphql_query_for_copyright_status_of_author = '''
query copyrightStatusOfAuthor {{
  item(id: "{qname}") {{
    copyrightStatus: statements(propertyId: "P7763") {{
      value {{
        ... on ItemValue {{
          id
          labelWithLanguageFallback(languageCode: "{lang}") {{
            languageCode
            value
          }}
        }}
      }}
      jurisdiction: qualifiers(propertyId: "P1001") {{
        value {{
          ... on ItemValue {{
            id
            labelWithLanguageFallback(languageCode: "{lang}") {{
              languageCode
              value
            }}
          }}
        }}
      }}
    }}
  }}
}}
'''

graphql_query_for_jurisdictions_are_instances_of = '''
query jurisdictionsAreInstancesOf {{
  itemsById(ids: {qlist}) {{
    id
    instanceOf: statements(propertyId: "P31") {{
      value {{
        ... on ItemValue {{
          id
        }}
      }}
    }}
  }}
}}
'''

query_for_authors_of_a_work = '''
SELECT DISTINCT ?typeOfAuthor ?typeOfAuthorLabel ?author ?authorLabel 
WHERE 
{{ 
  VALUES ?typeOfAuthor {{ wd:P170 wd:P50 wd:P57 wd:P58 wd:P84 wd:P86 wd:P87 wd:P110 wd:P676 wd:P943 }} . 
  ?typeOfAuthor wikibase:directClaim ?typeOfAuthorProp . 
  wd:{qname} ?typeOfAuthorProp ?author . 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}, mul, en". }} 
}}
'''

graphql_query_for_authors_of_a_work = '''
fragment statementFragment on Statement {{
  property {{
    id
    labelWithLanguageFallback(languageCode: "{lang}") {{
      languageCode
      value
    }}
  }}
  value {{
    ... on ItemValue {{
      id
      labelWithLanguageFallback(languageCode: "{lang}") {{
        languageCode
        value
      }}
    }}
  }}
}}query authorsOfAWork {{
  item(id: "{qname}") {{
    creator: statements(propertyId: "P170") {{
      ...statementFragment
    }}
    author: statements(propertyId: "P50") {{
      ...statementFragment
    }}
    director: statements(propertyId: "P57") {{
      ...statementFragment
    }}
    screenwriter: statements(propertyId: "P58") {{
      ...statementFragment
    }}
    architect: statements(propertyId: "P84") {{
      ...statementFragment
    }}
    composer: statements(propertyId: "P86") {{
      ...statementFragment
    }}
    librettist: statements(propertyId: "P87") {{
      ...statementFragment
    }}
    illustrator: statements(propertyId: "P110") {{
      ...statementFragment
    }}
    lyricsBy: statements(propertyId: "P676") {{
      ...statementFragment
    }}
    programmer: statements(propertyId: "P943") {{
      ...statementFragment
    }}
  }}
}}
'''

# keys_for_types_of_author = {
#     "creator": "P170",
#     "author": "P50",
#     "director": "P57",
#     "screenwriter": "P58",
#     "architect": "P84",
#     "composer": "P86",
#     "librettist": "P87",
#     "illustrator": "P110",
#     "lyrics_by": "P676",
#     "programmer": "P943"
# }


query_for_number_of_works_in_public_domain_from_a_country = '''
SELECT ?item ?itemLabel ( COUNT ( DISTINCT ?work_in_pd ) as ?works_in_pd ) 
WHERE 
{{ 
  VALUES ?item {{ wd:Q11424 wd:Q7725634 wd:Q105543609 wd:Q3305213 wd:Q860861 }} . 
  ?work_in_pd wdt:P31 ?item . 
  ?work_in_pd wdt:P6216 wd:Q19652 . 
  ?work_in_pd wdt:P495 wd:{qname} . 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang},mul,en". }} 
}} 
GROUP BY ?item ?itemLabel 
ORDER BY ASC ( ?itemLabel )
'''


# Not used at this moment. Needs optimization for better performance
query_for_number_of_authors_from_a_country = '''
SELECT ?item ?itemLabel ( COUNT ( DISTINCT ?author ) as ?authors ) ( COUNT ( DISTINCT ?author_pd ) as ?authors_pd ) 
WHERE 
{{ 
  VALUES ?item {{ wd:Q36180 wd:Q1028181 wd:Q2526255 wd:Q639669 }}. 
  {{ 
    ?author wdt:P106 ?item . 
    ?author wdt:P27 wd:{qname} . 
  }} 
  UNION 
  {{ 
    ?author_pd wdt:P106 ?item . 
    ?author_pd wdt:P27 wd:{qname} . 
    ?author_pd wdt:P7763 wd:Q71887839 . 
  }} 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang}, mul, en". }} 
}} 
GROUP BY ?item ?itemLabel
ORDER BY ASC (?itemLabel)
'''
