# Paulina: Data for the Public Domain
This project aims to build a global and multilingual search interface for authors
and works in the public domain using Wikidata and Python.

## Requirements
* Python 3.11 or later.
* Python modules: flask, Flask-Babel, Flask-Caching, python-dateutil, requests.
* A basic Flask WSGI webservice. Read more about [how to set it up](https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool#Step_2:_Create_a_basic_Flask_WSGI_webservice).

## Config file
You must copy the `config-sample.py` file to `config.py`. In this file you must uncomment the first line and enter a secret key, e.g.:

`SECRET_KEY = "YourSecretKeyHere"`

The secret key is for the session cookie. The session cookie is necessary so that the language choice is persistent throughout the session.

If you'd like to run application in DEBUG mode, uncomment the second line and set it to `True`, i.e.:

`DEBUG = True`

By default, `DEBUG` is set to `False`.


## Setting Up OAuth for Local Development

To test Wikidata editing features locally, you need to create your own OAuth consumer credentials.

### Step 1: Register Your OAuth Consumer

1. **Go to the OAuth Consumer Registration page:**
   
   https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose

2. **Fill out the registration form:**

   - **Application name:**  
     `Paulina Local Dev - YourWikimediaUsername`  
     (Replace `YourWikimediaUsername` with your actual username)

   - **Application version:**  
     `1.0`

   - **Application description:**  
     `Local development instance of Paulina for testing Wikidata editing features`

   - **This consumer is for use only by [username]:**  
     **Leave this UNCHECKED** (This callback URL field only appears after leaving it unchecked)

   - **OAuth protocol version:**  
     Select **`OAuth 1.0a`**

   - **OAuth "callback" URL:**  
     `http://localhost:5000/oauth-callback`  

   - **Applicable grants:**  
     Check these boxes:
     - Basic rights
     - Edit existing pages
     - Create, edit, and move pages

3. **Click "Propose consumer"**

### Step 2: Copy Your Credentials

After registration, you'll see a confirmation page with your credentials:

**Important:** Copy both tokens immediately. The secret is only shown once. Test consumers expire after 30 days. Create a new one when needed.

### Step 3: Configure Your Local Environment

1. **Copy the sample configuration:**
 
Update the config.py file with the copied tokens:

CONSUMER_KEY = "paste-your-consumer-token-here"
CONSUMER_SECRET = "paste-your-secret-token-here"

### Step 4: Test Your OAuth Setup

## Complete documentation
If you'd like to learn more about the software:
- [User documentation](https://www.wikidata.org/wiki/Wikidata:Tools/Paulina)
- [Complete technical documentation](https://www.wikidata.org/wiki/Wikidata:Tools/Paulina/Software_Documentation)

## Website
The public beta version is available at <https://paulina.toolforge.org/>.

## Contribute to the project
**Translations**: You can [help translate Paulina](https://hosted.weblate.org/projects/paulina/paulina-app/) on Weblate.

**Issues**: Request a feature, report a bug or suggest other tasks on the Paulina [Phabricator project](https://phabricator.wikimedia.org/project/profile/7320/).

## Credits
Paulina Project is supported by [Ártica - Centro Cultural Online](https://www.articaonline.com), 
[Creative Commons Uruguay](https://www.creativecommons.uy), [Data Uruguay](https://data.org.uy) and 
[Wikimedistas de Uruguay](https://wikimedistas.uy). The project received support from the Wikimedia Community Fund [in 2024](https://meta.wikimedia.org/wiki/Grants:Programs/Wikimedia_Community_Fund/Rapid_Fund/Fortaleciendo_el_dominio_p%C3%BAblico_con_Wikidata_(ID:_22592697)) and [2025](https://meta.wikimedia.org/wiki/Grants:Programs/Wikimedia_Community_Fund/General_Support_Fund/Fortaleciendo_el_dominio_p%C3%BAblico_latinoamericano_con_Wikidata).

Project Lead: Jorge Gemetto

Maintainers: David Coronel, Jorge Gemetto, Nat Hernández Clavijo.

Contributors: David Coronel, Dipanshu Vishwakarma, Jorge Gemetto, Kimbrene Kakande, Mariana Fossatti, Nat Hernández Clavijo, Nurah Wakili, Shreya Bhagat, Sudhanshu Gautam, Tunde-Ajayi Olamiposi.

Translators: Adolfo Jayme Barrientos, Allan Nordhøy, AtaZh, Bodhisattwa Mandal, ButterflyOfFire, EdoAug, Hubaishan, Jorge Gemetto, Juan Sebastian Quintero Santacruz, Nathan, Nemoralis, Phlostically, S. H., Steven Sun, Supaplex, Susanna Ånäs, Yunus Emre Bayraktar.

Community advisors: Alex Stinson, Carla Toro, Diego de la Hera.

Paulina logo designer: Gonzalo Saavedra.

## Awards and Recognitions
Paulina received the [Coolest Tool Award 2025](https://meta.wikimedia.org/wiki/Coolest_Tool_Award/2025) in the category Most Innovative.

## License
This software is under a [GNU Affero General Public License Version 3](https://www.gnu.org/licenses/agpl-3.0.html).
