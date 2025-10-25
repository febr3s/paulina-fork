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

Maintainer: Jorge Gemetto. Contributors: David Coronel, Mariana Fossatti, Sudhanshu Gautam, Nat Hernández, Carla Toro.

## Awards and Recognitions
Paulina received the [Coolest Tool Award 2025](https://meta.wikimedia.org/wiki/Coolest_Tool_Award/2025) in the category Most Innovative.

## License
This software is under a [GNU Affero General Public License Version 3](https://www.gnu.org/licenses/agpl-3.0.html).
