import guidance
from guidance import select, block
from pydantic import BaseModel
from .types import gen_type

__all__ = [
    "gen_schema",
    "gen_schemas",
]


def _gen_schema(schema: BaseModel):
    template = ""
    items = schema.model_fields.items()
    n = len(items)
    for i, (field, field_info) in enumerate(items):
        annotation = field_info.rebuild_annotation()
        template += f'"{field}": ' + gen_type(annotation)
        if i < n - 1:
            template += ","
    return template


@guidance(stateless=False)
def gen_schema(lm, schema: BaseModel, name=None):
    # Capture whole output as a variable with name `name`
    with block(name):
        lm += "{" + _gen_schema(schema) + "}"
    return lm


@guidance(stateless=False)
def gen_schemas(lm, schema: BaseModel, limit: int, name=None):
    with block(name):
        lm += "[" + select(["]", "{"], name="L")
        if lm["L"] == "]":
            return lm

        for i in range(limit):
            lm += _gen_schema(schema) + "}"
            if i < limit - 1:
                lm += select([",\n{", "]"], name="R")
                if lm["R"] == "]":
                    return lm
            else:
                lm += "]"
    return lm
