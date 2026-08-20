# Paulina: Data for the Public Domain

This project aims to build a global and multilingual search interface for authors
and works in the public domain using Wikidata and Python.

## Requirements

* Python 3.13 or later.
* Python modules: flask, Flask-Babel, Flask-Caching, Flask-Limiter, python-dateutil, requests, requests-oauthlib.
* A basic Flask WSGI webservice. Read more about [how to set it up](https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool#Step_2:_Create_a_basic_Flask_WSGI_webservice).

## Config file

By default, `config.py` looks for [environment variables](https://en.wikipedia.org/wiki/Environment_variable) and, if it doesn't find them, it fallbacks to dummy values. You can set your own values in your environment (for example, using an `.env` file) or you can modify your `config.py` file locally (if you choose this last option, please don't push you modified `config.py` file to the repository!).

The only mandatory variables in the `config.py` file are `SECRET KEY` and `USER_AGENT`:

`SECRET_KEY = "YourSecretKeyHere"`

The secret key is for the session cookie. The session cookie is necessary so that the language choice is persistent throughout the session. Replace `YourSecretKeyHere` with an actual key.

`USER_AGENT = "Paulina/1.0 (https://paulina.toolforge.org/; your-email@example.com)"`

The user agent is for the Wikimedia API calls made by the tool. Replace the placeholder email with your actual contact email.

If you'd like to run the application in DEBUG mode, set:

`DEBUG = True`

### Setting Up OAuth for Local Development

Paulina uses OAuth 2.0 to authenticate users and make edits to Wikidata. To test Wikidata editing features locally, you need to create your own OAuth consumer credentials.

#### Step 1: Register Your OAuth Consumer

1. **Go to the OAuth Consumer Registration page:**
   
  https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose/oauth2

2. **Fill out the registration form:**

   - **Application name:**  
     `Paulina Local Dev - YourWikimediaUsername`  
     (Replace `YourWikimediaUsername` with your actual username)

   - **Application version:**  
     `2.0`

   - **Application description:**  
     `Local development instance of Paulina for testing Wikidata editing features`

   - **This consumer is for use only by [username]:**  
     **Leave this UNCHECKED** (This callback URL field only appears after leaving it unchecked)

   - **OAuth "callback" URL:**  
     `http://localhost:5000/oauth-callback`  

   - **Applicable grants:**  
     Check these boxes:
     - Basic rights
     - Edit existing pages
     - Create, edit, and move pages

3. **Click "Propose consumer"**

#### Step 2: Copy Your Credentials

After registration, you'll see a confirmation page with your credentials:

**Important:** Copy both tokens immediately. The secret is only shown once. Test consumers expire after 30 days. Create a new one when needed.

#### Step 3: Update config.py

Update the config.py file with the copied tokens:

`CLIENT_ID = "paste-your-client-application-key-here"`

`CLIENT_SECRET = "paste-your-client-application-secret-here"`

Update the redirect URL:

`REDIRECT_URL = "http://localhost:5000/oauth-callback"`


## Running Paulina: Test vs Production
Paulina can run in test mode or production mode using a single configuration file.

- Test mode (recommended for local development): uses test.wikidata.org
 to safely test edits without affecting real data. For test mode run: 

  `python app.py test`

- Production mode: uses wikidata.org for live data. For production mode run:

  `python app.py`


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

Project Lead: Jorge Gemetto.

Maintainers: David Coronel, Jorge Gemetto, Nat Hernández Clavijo.

Contributors: Adaobi Chuma-Okeke, Adebawojo Mosopefoluwa, Ademola Omosanya, Anba Nguyen, Aradhya Yadav, David Coronel, Dipanshu Vishwakarma, Jorge Gemetto, Josef Anthony, Kimbrene Kakande, Mariana Fossatti, Nat Hernández Clavijo, Nurah Wakili, Shreya Bhagat, Sudhanshu Gautam, Tunde-Ajayi Olamiposi.

Translators: Adolfo Jayme Barrientos, Allan Nordhøy, AtaZh, Bodhisattwa Mandal, ButterflyOfFire, EdoAug, Hubaishan, Jorge Gemetto, Juan Sebastian Quintero Santacruz, Nathan, Nemoralis, Phlostically, S. H., Steven Sun, Supaplex, Susanna Ånäs, Yunus Emre Bayraktar.

Community advisors: Alex Stinson, Carla Toro, Diego de la Hera, Mariana Fossatti.

Paulina logo designer: Gonzalo Saavedra.

## Awards and Recognitions
Paulina received the [Coolest Tool Award 2025](https://meta.wikimedia.org/wiki/Coolest_Tool_Award/2025) in the category Most Innovative.

## License
This software is under a [GNU Affero General Public License Version 3](https://www.gnu.org/licenses/agpl-3.0.html).
