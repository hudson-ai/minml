from types import UnionType, NoneType, GenericAlias
from typing import get_origin, get_args
from collections.abc import Collection
from typing_extensions import _AnnotatedAlias
from annotated_types import GroupedMetadata
from pydantic import StringConstraints, BaseModel
from guidance import gen, select
from guidance._grammar import Byte, GrammarFunction, Join, Select, string

__all__ = [
    "gen_bool",
    "gen_int",
    "gen_float",
    "gen_str",
    "gen_list",
    "gen_pydantic",
    "gen_type",
]

_QUOTE = Byte(b'"')
_OPEN_BRACE = Byte(b"{")
_CLOSE_BRACE = Byte(b"}")
_OPEN_BRACKET = Byte(b"[")
_CLOSE_BRACKET = Byte(b"]")
_COMMA = Byte(b",")
_COLON = Byte(b":")

Type = type | NoneType | UnionType | GenericAlias | _AnnotatedAlias | BaseModel


def gen_None() -> GrammarFunction:
    return string("null")


def gen_bool() -> GrammarFunction:
    return select(["true", "false"])


def gen_int() -> GrammarFunction:
    return gen(regex=r"(\+|\-)?\d+")


def gen_float() -> GrammarFunction:
    return gen(regex=r"(\+|\-)?(\d*\.)?\d+")


def gen_str(**kwds) -> GrammarFunction:
    return Join([_QUOTE, gen(**kwds, stop='"'), _QUOTE])


def gen_list(type: Type) -> GrammarFunction:
    s = Select([], capture_name=None, recursive=True)
    s.values = [gen_type(type), Join([s, _COMMA, gen_type(type)])]
    return _OPEN_BRACKET + select([_CLOSE_BRACKET, Join([s, _CLOSE_BRACKET])])


def gen_pydantic(schema: BaseModel) -> GrammarFunction:
    grammar = _OPEN_BRACE
    model_fields = schema.model_fields.items()
    for i, (field, field_info) in enumerate(model_fields):
        annotation = field_info.rebuild_annotation()
        field_grammar = Join(
            [_QUOTE, string(field), _QUOTE, _COLON, gen_type(annotation)]
        )
        if i == 0:
            grammar = Join([grammar, field_grammar])
        else:
            grammar = Join([grammar, _COMMA, field_grammar])
    grammar = Join([grammar, _CLOSE_BRACE])
    return grammar


def gen_type(type: Type | None) -> GrammarFunction:
    if (type is None) or (type is NoneType):
        return gen_None()
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
        return gen_pydantic(type)
    raise NotImplementedError(f"Can't gen type {type!r}")


def _gen_generic_alias_type(origin: Type, args: Collection[Type]) -> GrammarFunction:
    if origin is list and len(args) == 1:
        type = args[0]
        return gen_list(type)
    raise NotImplementedError


def _gen_annotated_type(
    type: Type, annotations: Collection[GroupedMetadata]
) -> GrammarFunction:
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

    raise NotImplementedError(f"Can't gen type {type!r}")


def _gen_union_type(*types: Type) -> GrammarFunction:
    return select([gen_type(type) for type in types])
