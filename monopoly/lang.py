import json

from typing import Dict

from .renderer import RENDER, CSI


DEFAULT_LANG = "english"

LANG_LIST = ["french", "english"]


class Lang:
    def __init__(self, name: int, data: Dict[str, str]):
        self._name = name
        self._data = data
    
    def __getitem__(self, item: str):
        # sourcery skip: assign-if-exp, reintroduce-else
        data = self._data.get(item, f"{self!r}.{item!r}")

        if isinstance(data, dict):
            return Lang(f"{self._name}.'{item}'", data)
        
        return data
    
    def __call__(self, _item: str, **kwargs):
        if _item not in self._data:
            return f"{self!r}.{_item!r}{kwargs!r}"

        data = self._data.get(_item)

        if isinstance(data, dict):
            return Lang(f"{self._name}.'{_item}'", data)

        res = data.format(**{**kwargs, "render": RENDER})

        if CSI in res:
            res += RENDER.reset

        return res

    def __repr__(self):
        return f"<{self.__module__}.{self.__class__.__name__} {self._name}>"

def _loadLang(name: str):  # sourcery skip: instance-method-first-arg-name, raise-from-previous-error
    try:
        with open(f"monopoly/assets/lang/{name}.json", "r", encoding="utf8") as f:
            return Lang(name, json.load(f))
    except FileNotFoundError:
        raise FileNotFoundError(f"Map file '{name}' not found")

def loadLang(name: str):
    lang = _loadLang(DEFAULT_LANG)

    lang._data.update(_loadLang(name)._data)

    lang._name = name

    return lang
