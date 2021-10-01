from mars.action import EnumPriorityInterface
from enum import Enum
import json
from typing import Any, Dict
import re


def serialize(obj: object, form: str = "json", database: bool = False) -> str:
    """function to serialize a mars object

    Args:
        obj (object): object to serialize
        form (str, optional): format . Defaults to "json".
        database (bool, optional): for database storage if true,
            for network transfert else. Defaults to False.

    Returns:
        str: string describing the objet under asking format
    """

    so = to_dict(obj, database)

    if form == "json":
        return json.dumps(so)


def to_dict(obj: object, database: bool = False) -> Dict:
    """ transform object to dictionnary

    Args:
        obj (object): [description]
        database (bool, optional): database storage format if true,
            network transfert format else. Defaults to False.

    Returns:
        Dict: dictionnary describing the objet
    """

    if obj.__class__.__module__ == 'builtins':
        if type(obj) == list:
            lt = []
            for va in obj:
                lt.append(to_dict(va, database))
            return lt
        elif type(obj) == dict:
            d = {}
            for key, val in obj.items():
                k = re.sub('^_{1,2}', '', key)
                v = to_dict(val, database)
                d[k] = v
            return d
        else:
            return __cast_val(obj)

    elif getattr(obj, 'to_dict', None):
        return to_dict(obj.to_dict(), database)

    elif EnumPriorityInterface in obj.__class__.__bases__ or\
            Enum in obj.__class__.__bases__:
        if database:
            return obj.name
        else:
            return obj.value
    else:
        so = {}
        for key, val in obj.__dict__.items():
            k = key.replace('_{}'.format(obj.__class__.__name__), '')
            k = re.sub('^_{1,2}', '', k)
            v = to_dict(val, database)
            so[k] = v
        return so


def __cast_val(val: Any) -> Any:
    """private function to manage the numeric cast

    Args:
        val (Any): variable to cast

    Returns:
        Any: if numeric the variable cast to int or float,
            else the actual value.
    """

    if isinstance(val, str) and val.isnumeric():
        return int(val) if val.isdecimal() else float(val)
    else:
        return val
