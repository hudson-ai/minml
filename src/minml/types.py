from types import UnionType, NoneType, GenericAlias
from typing_extensions import _AnnotatedAlias
import json
from pydantic import TypeAdapter, BaseModel

from guidance._json_schema_to_grammar import json_schema_to_grammar
from .util import resolve_refs

__all__ = [
    "gen_type",
]


Type = type | NoneType | UnionType | GenericAlias | _AnnotatedAlias | BaseModel


def gen_type(type: Type):
    t = TypeAdapter(type)
    schema = t.json_schema()
    schema = resolve_refs(schema)
    return json_schema_to_grammar(json.dumps(schema))
