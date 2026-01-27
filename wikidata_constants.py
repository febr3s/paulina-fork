import os
from flask_babel import lazy_gettext as _l

# Wikidata property IDs  - Test/Production Mode Configuration

# Check for test mode
WIKIDATA_TEST_MODE = os.environ.get('WIKIDATA_TEST_MODE', 'false').lower() == 'true'

# Property IDs (PIDs)
if WIKIDATA_TEST_MODE:
    # Test Wikidata properties (from test.wikidata.org)
    PID_INSTANCE_OF = 'P82'           # instance of
    PID_SEX_OR_GENDER = 'P192'         # sex or gender
    PID_COUNTRY_OF_CITIZENSHIP = 'P196' # country of citizenship
    PID_DATE_OF_BIRTH = 'P18'         # date of birth
    PID_DATE_OF_DEATH = 'P25'        # date of death
    PID_PLACE_OF_BIRTH = 'P342'       # place of birth
    PID_OCCUPATION = 'P204'           # occupation
    PID_ETHNIC_GROUP = 'P84982'         # ethnic group
    PID_IMAGE = 'P185'                # image
    PID_OFFICIAL_WEBSITE = 'P206'     # official website
    PID_REFERENCE_URL = 'P93'        # reference URL
    PID_TITLE = 'P77107'                # title
    PID_RETRIEVED = 'P388'            # retrieved
else:
    # Production Wikidata properties
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
    PID_TITLE = 'P1476'
    PID_RETRIEVED = 'P813'

# Item IDs (QIDs)
if WIKIDATA_TEST_MODE:
    # Test Wikidata items
    QID_HUMAN = 'Q224056'
else:
    # Production Wikidata items
    QID_HUMAN = 'Q5'
    
# Work QIDS

if WIKIDATA_TEST_MODE:
    # Test Wikidata properties (add to existing list)
    PID_AUTHOR = 'P65773'           # author
    PID_LANGUAGE = 'P94'           # language of work or name
    PID_COUNTRY_OF_ORIGIN = 'P98508' # country of origin
    PID_PUBLICATION_DATE = 'P151'     # publication date
    PID_INCEPTION = 'P85165'       # inception/creation date
    PID_FULL_WORK_URL = 'P98210'   # full work available at URL
    PID_INTERNET_ARCHIVE = 'P99674'  #Internet Archive ID
else:
    # Production Wikidata properties (add to existing list)
    PID_AUTHOR = 'P50'                # author
    PID_LANGUAGE = 'P407'             # language of work or name
    PID_COUNTRY_OF_ORIGIN = 'P495'    # country of origin
    PID_PUBLICATION_DATE = 'P577'     # publication date
    PID_INCEPTION = 'P571'            # inception/creation date
    PID_FULL_WORK_URL = 'P953'        # full work available at URL
    PID_INTERNET_ARCHIVE = 'P724'     # Internet Archive ID

    
    
# Gender QIDs
if WIKIDATA_TEST_MODE:
    # Test Wikidata QIDs for genders
    FORM_GENDERS = [
        {"qid": "Q216154", "gender_name": _l("Female")},
        {"qid": "Q216156", "gender_name": _l("Male")},
        {"qid": "Q243752", "gender_name": _l("Trans man")},
        {"qid": "Q243753", "gender_name": _l("Trans woman")},
        {"qid": "Q243754", "gender_name": _l("Non-binary")}
    ]
else:
    # Production Wikidata QIDs for genders
    FORM_GENDERS = [
        {"qid": "Q6581072", "gender_name": _l("Female")},
        {"qid": "Q6581097", "gender_name": _l("Male")},
        {"qid": "Q2449503", "gender_name": _l("Trans man")},
        {"qid": "Q1052281", "gender_name": _l("Trans woman")},
        {"qid": "Q48270", "gender_name": _l("Non-binary")}
    ]
    