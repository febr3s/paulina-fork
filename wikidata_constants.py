import os
from flask_babel import lazy_gettext as _l

# Wikidata property IDs  - Test/Production Mode Configuration

# Check for test mode
WIKIDATA_TEST_MODE = os.environ.get('WIKIDATA_TEST_MODE', 'false').lower() == 'true'

# Property IDs (PIDs)
if WIKIDATA_TEST_MODE:
    PID_INSTANCE_OF = 'P82'
    PID_SEX_OR_GENDER = 'P192'
    PID_COUNTRY_OF_CITIZENSHIP = 'P196'
    PID_DATE_OF_BIRTH = 'P18'
    PID_DATE_OF_DEATH = 'P25'
    PID_PLACE_OF_BIRTH = 'P342'
    PID_OCCUPATION = 'P204'
    PID_ETHNIC_GROUP = 'P84982'
    PID_IMAGE = 'P185'
    PID_OFFICIAL_WEBSITE = 'P206'
    PID_REFERENCE_URL = 'P93'
    PID_RETRIEVED = 'P388'
else:
    PID_INSTANCE_OF = 'P31'
    PID_SEX_OR_GENDER = 'P21'
    PID_COUNTRY_OF_CITIZENSHIP = 'P27'
    PID_DATE_OF_BIRTH = 'P569'
    PID_DATE_OF_DEATH = 'P570'
    PID_PLACE_OF_BIRTH = 'P19'
    PID_OCCUPATION = 'P106'
    PID_ETHNIC_GROUP = 'P172'
    PID_IMAGE = 'P18'
    PID_OFFICIAL_WEBSITE = 'P856'
    PID_REFERENCE_URL = 'P854'
    PID_RETRIEVED = 'P813'

# Item IDs (QIDs)
if WIKIDATA_TEST_MODE:
    QID_HUMAN = 'Q224056'
else:
    QID_HUMAN = 'Q5'
    
    
# Gender QIDs
if WIKIDATA_TEST_MODE:
    FORM_GENDERS = [
        {"qid": "Q216154", "gender_name": _l("Female")},
        {"qid": "Q216156", "gender_name": _l("Male")},
        {"qid": "Q243752", "gender_name": _l("Trans man")},
        {"qid": "Q243753", "gender_name": _l("Trans woman")},
        {"qid": "Q243754", "gender_name": _l("Non-binary")}
    ]
else:
    FORM_GENDERS = [
        {"qid": "Q6581072", "gender_name": _l("Female")},
        {"qid": "Q6581097", "gender_name": _l("Male")},
        {"qid": "Q2449503", "gender_name": _l("Trans man")},
        {"qid": "Q1052281", "gender_name": _l("Trans woman")},
        {"qid": "Q48270", "gender_name": _l("Non-binary")}
    ]

# Work Property PIDs

if WIKIDATA_TEST_MODE:
    PID_AUTHOR = 'P95656'
    PID_DIRECTOR = 'P778'
    PID_SCREENWRITER = 'P99723'
    PID_COMPOSER = 'P96555'
    PID_CREATOR = 'P728'
    PID_LYRICIST = 'P99724' 
    PID_PERFORMER = 'P99740'
    PID_PRODUCER = 'P97838'
    PID_GENRE = 'P99710'
    PID_RECORD_LABEL = 'P95963'
    PID_COUNTRY_OF_PUBLICATION = 'P95361'
    PID_LANGUAGE = 'P94'
    PID_LANGUAGE_FILM = 'P98509'
    PID_COUNTRY_OF_ORIGIN = 'P98508'
    PID_PUBLICATION_DATE = 'P151'
    PID_INCEPTION = 'P85165'
    PID_LOCATION = 'P286'
    PID_FULL_WORK_URL = 'P98210'
    PID_INTERNET_ARCHIVE = 'P99763'
else:
    PID_AUTHOR = 'P50'
    PID_DIRECTOR = 'P57'
    PID_SCREENWRITER = 'P58'
    PID_COMPOSER = 'P86'
    PID_CREATOR = 'P170'
    PID_LYRICIST = 'P676'
    PID_PERFORMER = 'P175'
    PID_PRODUCER = 'P162'
    PID_GENRE = 'P136'
    PID_RECORD_LABEL = 'P264'
    PID_COUNTRY_OF_PUBLICATION = 'P291'
    PID_LANGUAGE = 'P407'
    PID_LANGUAGE_FILM = 'P364'
    PID_COUNTRY_OF_ORIGIN = 'P495'
    PID_PUBLICATION_DATE = 'P577'
    PID_INCEPTION = 'P571'
    PID_LOCATION = 'P276'
    PID_FULL_WORK_URL = 'P953'
    PID_INTERNET_ARCHIVE = 'P724'
    
    
# Work Type QIDs
if WIKIDATA_TEST_MODE:
    QID_LITERARY_WORK = 'Q241784'
    QID_WRITTEN_WORK = 'Q225442'
    QID_EDITION = 'Q243995'
    QID_FILM = 'Q229658'
    QID_AUDIOVISUAL = 'Q243996'
    QID_PAINTING = 'Q853'
    QID_SCULPTURE = 'Q2226'
    QID_VISUAL_ARTWORK = 'Q243997'
    QID_MUSICAL_WORK = 'Q216189'
    QID_ALBUM = 'Q1785'
else:
    QID_LITERARY_WORK = 'Q7725634'
    QID_WRITTEN_WORK = 'Q47461344'
    QID_EDITION = 'Q3331189'
    QID_FILM = 'Q11424'
    QID_AUDIOVISUAL = 'Q2431196'
    QID_PAINTING = 'Q3305213'
    QID_SCULPTURE = 'Q860861'
    QID_VISUAL_ARTWORK = 'Q4502142'
    QID_MUSICAL_WORK = 'Q105543609'
    QID_ALBUM = 'Q482994'


# Work Types 
WORK_TYPES = [
    # Literary Works
    {
        "qid": QID_LITERARY_WORK,
        "type_name": _l("Literary work"),
        "category": "literary",
        "creator_property": "author",
        "creator_pid": PID_AUTHOR, 
        "fields": {
            "required": ["author"],  
            "optional": ["language", "country", "imageUrl", "fullWorkUrl", "internetArchiveId", "publicationDate", "externalLinks"]
        }
    },
    {
        "qid": QID_WRITTEN_WORK,
        "type_name": _l("Written work (not literary)"),
        "category": "literary",
        "creator_property": "author",
        "creator_pid": PID_AUTHOR,  
        "fields": {
            "required": ["author"],  
            "optional": ["language", "publicationDate", "country", "imageUrl", "fullWorkUrl", "internetArchiveId", "externalLinks"]
        }
    },
    {
        "qid": QID_EDITION,
        "type_name": _l("Edition of a written work"),
        "category": "literary",
        "creator_property": "author",
        "creator_pid": PID_AUTHOR, 
        "fields": {
            "required": ["author"],  
            "optional": ["language", "country", "imageUrl", "fullWorkUrl", "internetArchiveId", "publicationDate", "externalLinks"]
        }
    },
    
    # Audiovisual Works
    {
        "qid": QID_FILM,
        "type_name": _l("Film"),
        "category": "audiovisual",
        "creator_property": "director",
        "creator_pid": PID_DIRECTOR, 
        "fields": {
            "required": ["director"],  
            "optional": ["screenwriter", "composer", "publicationDate", "languageFilm", "country", "imageUrl", "fullWorkUrl", "internetArchiveId", "externalLinks"]
        }
    },
    {
        "qid": QID_AUDIOVISUAL,
        "type_name": _l("Audiovisual work (other)"),
        "category": "audiovisual",
        "creator_property": "director",
        "creator_pid": PID_DIRECTOR,  
        "fields": {
            "required": ["director"],  
            "optional": ["screenwriter", "composer", "publicationDate", "languageFilm", "country", "imageUrl", "fullWorkUrl", "internetArchiveId", "externalLinks"]
        }
    },
    
    # Visual Arts
    {
        "qid": QID_PAINTING,
        "type_name": _l("Painting"),
        "category": "visual",
        "creator_property": "creator",
        "creator_pid": PID_CREATOR, 
        "fields": {
            "required": ["creator"],  
            "optional": ["creationDate", "location", "country", "imageUrl", "externalLinks", "fullWorkUrl", "internetArchiveId"]
        }
    },
    {
        "qid": QID_SCULPTURE,
        "type_name": _l("Sculpture"),
        "category": "visual",
        "creator_property": "creator",
        "creator_pid": PID_CREATOR,  
        "fields": {
            "required": ["creator"],  
            "optional": ["creationDate", "location", "country", "imageUrl", "externalLinks", "fullWorkUrl", "internetArchiveId"]
        }
    },
    {
        "qid": QID_VISUAL_ARTWORK,
        "type_name": _l("Visual artwork (other)"),
        "category": "visual",
        "creator_property": "creator",
        "creator_pid": PID_CREATOR,  
        "fields": {
            "required": ["creator"], 
            "optional": ["creationDate", "location", "country", "imageUrl", "externalLinks", "fullWorkUrl", "internetArchiveId"]
        }
    },
    
    # Music
    {
        "qid": QID_MUSICAL_WORK,
        "type_name": _l("Musical work/composition"),
        "category": "music",
        "creator_property": "composer",
        "creator_pid": PID_COMPOSER,  
        "fields": {
            "required": ["composer"],  
            "optional": ["lyricist", "publicationDate", "language", "country", "imageUrl", "fullWorkUrl", "externalLinks", "internetArchiveId"]
        }
    },
    # Album
    {
        "qid": QID_ALBUM,
        "type_name": _l("Album"),
        "category": "music",
        "creator_property": "performer",
        "creator_pid": PID_PERFORMER,
        "fields": {
            "required": ["performer"],
            "optional": ["composer", "producer", "genre", "publicationDate", "countryOfPublication", "language", "recordLabel", "imageUrl", "fullWorkUrl", "externalLinks", "internetArchiveId"]
        }
    }
]
