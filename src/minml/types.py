from types import UnionType, NoneType
from typing import get_args
from typing_extensions import _AnnotatedAlias
from pydantic import StringConstraints
from guidance import gen, select

__all__ = [
    "gen_bool",
    "gen_int",
    "gen_float",
    "gen_str",
    "gen_type",
]


def _gen_None():
    return "null"


def gen_bool():
    return select(["true", "false"])


def gen_int():
    return gen(regex=r"(\+|\-)?\d+")


def gen_float():
    return gen(regex=r"(\+|\-)?(\d*\.)?\d+")


def gen_str(**kwds):
    return '"' + gen(**kwds, stop='"') + '"'


def gen_type(type):
    if (type is None) or (type is NoneType):
        return _gen_None()
    if type is bool:
        return gen_bool()
    if type is int:
        return gen_int()
    if type is float:
        return gen_float()
    if type is str:
        return gen_str()
    if isinstance(type, _AnnotatedAlias):
        type, *annotations = get_args(type)
        return _gen_annotated_type(type, *annotations)
    if isinstance(type, UnionType):
        types = get_args(type)
        return _gen_union_type(*types)
    raise NotImplementedError("Can't gen type {type!r}")


def _gen_annotated_type(type, *annotations):
    if type is str:
        if len(annotations) == 1 and isinstance(annotations[0], StringConstraints):
            kmap = {"pattern": "regex", "max_length": "max_tokens"}
            try:
                kwds = {
                    kmap[k]: v
                    for k, v in annotations[0].__dict__.items()
                    if v is not None
                }
            except KeyError as e:
                raise NotImplementedError(
                    "String constraints other than 'pattern' and 'max_length' are not supported"
                ) from e
            return gen_str(**kwds)

    raise NotImplementedError("Can't gen type {type!r}")


def _gen_union_type(*types):
    return select([gen_type(type) for type in types])
