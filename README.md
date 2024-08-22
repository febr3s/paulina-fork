# Paulina: Data for the Public Domain
This project aims to build a global and multilingual search interface for authors
and works in the public domain using Wikidata and Python.

## Requirements
* Python 3.10 or later.
* Python modules: flask, Flask-Babel, python-dateutil, requests.
* A basic Flask WSGI webservice. Read more about [how to set it up](https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool#Step_2:_Create_a_basic_Flask_WSGI_webservice).

## Config file
You must copy the `config-sample.py` file to `config.py`. In this file you must uncomment the first line and enter a secret key, e.g.:

`SECRET_KEY = "YourSecretKeyHere"`

The secret key is for the session cookie. The session cookie is necessary so that the language choice is persistent throughout the session.

## Website
The public beta version is available at <https://paulina.toolforge.org/>.

## Help translate Paulina
You can help translate Paulina by going to [our project's translation repository on Weblate](https://hosted.weblate.org/projects/paulina/paulina-app/).

## Credits
Paulina Project is supported by [Ártica - Centro Cultural Online](https://www.articaonline.com), 
[Creative Commons Uruguay](https://www.creativecommons.uy), [Data Uruguay](https://data.org.uy) and 
[Wikimedistas de Uruguay](https://wikimedistas.uy). In June 2024 the project [received support](https://meta.wikimedia.org/wiki/Grants:Programs/Wikimedia_Community_Fund/Rapid_Fund/Fortaleciendo_el_dominio_p%C3%BAblico_con_Wikidata_(ID:_22592697)) 
from the Wikimedia Community Fund.

## License
This software is under a GNU Affero General Public License Version 3.

---
*Documentation under construction. Read more at [Paulina's page on Wikidata](https://www.wikidata.org/wiki/Wikidata:Tools/Paulina).*
