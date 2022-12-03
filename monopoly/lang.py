import json


DEFAULT_LANG = "english"

LANG_LIST = ["french", "english"]


def _loadLang(name: str):  # sourcery skip: raise-from-previous-error
    try:
        with open(f"monopoly/assets/lang/{name}.json", "r", encoding="utf8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Map file '{name}' not found")

def loadLang(name: str):
    defaultLang = _loadLang(DEFAULT_LANG)

    lang = _loadLang(name)

    defaultLang.update(lang)

    return defaultLang
