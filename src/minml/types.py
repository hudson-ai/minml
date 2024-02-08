from types import UnionType, NoneType, GenericAlias
from typing import get_origin, get_args
from typing_extensions import _AnnotatedAlias
from pydantic import StringConstraints
import guidance
from guidance import gen, select

__all__ = [
    "gen_bool",
    "gen_int",
    "gen_float",
    "gen_str",
    "gen_list",
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
    delim = '"'
    return delim + gen(**kwds, stop=delim) + delim


def gen_list(type, limit=100):
    return _gen_sequence(type, "[", "]")


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
    if isinstance(type, GenericAlias):
        origin = get_origin(type)
        args = get_args(type)
        return _gen_generic_alias_type(origin, args)
    if isinstance(type, _AnnotatedAlias):
        type, *annotations = get_args(type)
        return _gen_annotated_type(type, annotations)
    if isinstance(type, UnionType):
        types = get_args(type)
        return _gen_union_type(*types)
    raise NotImplementedError("Can't gen type {type!r}")


@guidance(stateless=False)
def _gen_sequence(lm, type, opener, closer, limit=100):
    lm += opener
    _val = gen_type(type)
    for i in range(limit):
        if i == 0:
            val = _val
        else:
            val = f", " + _val
        lm += select([closer, val], name="value")
        if lm["value"] == closer:
            return lm
    lm += closer
    return lm


def _gen_generic_alias_type(origin, args):
    if origin is list and len(args) == 1:
        type = args[0]
        return gen_list(type)
    raise NotImplementedError


def _gen_annotated_type(type, annotations):
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
