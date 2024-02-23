import os
import sys


def resolve_refs(schema, defs=None):
    new_schema = {}
    defs = defs or schema.get("$defs", {})
    for k, v in schema.items():
        if k == "$defs":
            continue
        if k == "$ref":
            return defs[v[len("#/$defs/") :]]
        if isinstance(v, dict):
            v = resolve_refs(v, defs)
        new_schema[k] = v
    return new_schema
