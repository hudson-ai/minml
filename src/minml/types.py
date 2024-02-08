from types import UnionType, NoneType, GenericAlias
from typing import get_origin, get_args
from typing_extensions import _AnnotatedAlias
from pydantic import StringConstraints, BaseModel
import guidance
from guidance import gen, select
from guidance._grammar import Select

__all__ = [
    "gen_bool",
    "gen_int",
    "gen_float",
    "gen_str",
    "gen_list",
    "gen_schema",
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


def gen_list(type):
    return _gen_sequence(type, "[", "]")


def gen_schema(schema: BaseModel):
    template = "{"
    items = schema.model_fields.items()
    n = len(items)
    for i, (field, field_info) in enumerate(items):
        annotation = field_info.rebuild_annotation()
        template += f'"{field}": ' + gen_type(annotation)
        if i < n - 1:
            template += ","
    template += "}"
    return template


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
    if issubclass(type, BaseModel):
        return gen_schema(type)
    raise NotImplementedError("Can't gen type {type!r}")


def _gen_sequence(type, opener, closer):
    s = Select([], capture_name=None, recursive=True)
    s.values = [gen_type(type), s + ", " + gen_type(type)]
    return opener + select([closer, s + closer])


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
