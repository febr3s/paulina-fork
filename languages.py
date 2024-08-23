# This module contains a list of languages supported by Wikidata
# and a function to get the locale of the user.

from flask import request, session


SUPPORTED_LANGUAGES = ["aa", "ab", "af", "ak", "am", "an", "ar", "as", "av",
                       "ay", "az", "ba", "be", "bg", "bh", "bi", "bm", "bn",
                       "bo", "br", "bs", "ca", "ce", "ch", "co", "cr", "cs",
                       "cu", "cv", "cy", "da", "de", "dv", "dz", "ee", "el",
                       "en", "eo", "es", "et", "eu", "fa", "ff", "fi", "fj",
                       "fo", "fr", "fy", "ga", "gd", "gl", "gn", "gu", "gv",
                       "ha", "he", "hi", "ho", "hr", "ht", "hu", "hy", "hz",
                       "ia", "id", "ie", "ig", "ii", "ik", "io", "is", "it",
                       "iu", "ja", "jv", "ka", "kg", "ki", "kj", "kk", "kl",
                       "km", "kn", "ko", "kr", "ks", "ku", "kv", "kw", "ky",
                       "la", "lb", "lg", "li", "ln", "lo", "lt", "lv", "mg",
                       "mh", "mi", "mk", "ml", "mn", "mo", "mr", "ms", "mt",
                       "my", "na", "nb", "ne", "ng", "nl", "nn", "no", "nr",
                       "nv", "ny", "oc", "oj", "om", "or", "os", "pa", "pi",
                       "pl", "ps", "pt", "qu", "rm", "rn", "ro", "ru", "rw",
                       "sa", "sc", "sd", "se", "sg", "sh", "si", "sk", "sl",
                       "sm", "sn", "so", "sq", "sr", "ss", "st", "su", "sv",
                       "sw", "ta", "te", "tg", "th", "ti", "tk", "tl", "tn",
                       "to", "tr", "ts", "tt", "tw", "ty", "ug", "uk", "ur",
                       "uz", "ve", "vi", "vo", "wa", "wo", "xh", "yi", "yo",
                       "za", "zh", "zu"]

""" Add more translated languages to this dictionary when new translations become available.
Item key is language 2 letter code. Value is language name in its own language.
English must be the first item of the dictionary. 
Other languages are ordered by alphabetical order."""
TRANSLATED_LANGUAGES = {"en": "English",
                        "es": "Español",
                        "nb": "Norsk bokmål",
                        "pt": "Português"
                        }


def get_locale():
    if "language" in request.args:
        session["language"] = request.args.get("language")
        return session.get("language")
    else:
        browser_language = request.accept_languages.best_match(SUPPORTED_LANGUAGES)
        if browser_language is None:
            return session.get("language", "en")
        else:
            return session.get("language", browser_language)
