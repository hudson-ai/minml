from typing import Literal, Generic, TypeVar, Callable, Any
from pydantic import TypeAdapter, BaseModel, create_model
import inspect

class PositionalOnly(BaseModel):
    json_schema: dict[str, Any]

class PositionalOrKeyword(BaseModel):
    name: str
    json_schema: dict[str, Any]

class VarArgs(BaseModel):
    json_schema: dict[str, Any]

class KeywordOnly(BaseModel):
    name: str
    json_schema: dict[str, Any]

class VarKwargs(BaseModel):
    json_schema: dict[str, Any]

_parameter_kinds = {
    inspect._ParameterKind.POSITIONAL_ONLY: PositionalOnly,
    inspect._ParameterKind.POSITIONAL_OR_KEYWORD: PositionalOrKeyword,
    inspect._ParameterKind.VAR_POSITIONAL: VarArgs,
    inspect._ParameterKind.KEYWORD_ONLY: KeywordOnly,
    inspect._ParameterKind.VAR_KEYWORD: VarKwargs,   
}

class Signature(BaseModel):
    positional: tuple
    keyword: dict[str, Any]


class SignatureSchema(BaseModel):
    positional_only: list[PositionalOnly]
    positional_or_keyword: list[PositionalOrKeyword]
    keyword_only: list[KeywordOnly]
    var_args: VarArgs | None = None
    var_kwargs: VarKwargs | None = None

    @classmethod
    def from_callable(cls, func: Callable) -> "SignatureSchema":
        signature = inspect.signature(func)
        parameters = signature.parameters

        schema = {
            'positional_only': [],
            'positional_or_keyword': [],
            'keyword_only': [],
        }
        for name, param in parameters.items():
            data = {}

            if param.annotation != param.empty:
                json_schema = TypeAdapter(param.annotation).json_schema()
            else:
                # TODO?
                json_schema = {"type": "any"}

            # Useful?
            if param.default != param.empty:
                json_schema['default'] = param.default

            data = {
                'name': name,
                'json_schema': json_schema
            }
            
            parameter_kind = _parameter_kinds[param.kind]
            parameter = parameter_kind.model_validate(data)

            if parameter_kind == PositionalOnly:
                schema['positional_only'].append(parameter)
            elif parameter_kind == PositionalOrKeyword:
                schema['positional_or_keyword'].append(parameter)
            elif parameter_kind == VarArgs:
                schema['var_args'] = parameter
            elif parameter_kind == KeywordOnly:
                schema['keyword_only'].append(parameter)
            elif parameter_kind == VarKwargs:
                schema['var_kwargs'] = parameter
            
        return __class__.model_validate(schema)

    def gen(self):
        return _signature_gen(self)

import guidance
from guidance._json_schema_to_grammar import json_schema_to_grammar
from guidance import select, zero_or_more, one_or_more, char_range
import json

_SAFE_NAME = one_or_more(select([char_range('A', 'Z'), char_range('a', 'z'), '_'])) + zero_or_more(select([char_range('A', 'Z'), char_range('a', 'z'), '_', char_range('0', '9')]))

@guidance(stateless=True)
def _signature_gen(lm, signature_schema: SignatureSchema):
    for arg in signature_schema.positional_only:
        lm += json_schema_to_grammar(json.dumps(arg.json_schema)) + ','
    for arg in signature_schema.positional_or_keyword:
        if signature_schema.var_args is not None:
            # no kwargs before var_args
            lm += json_schema_to_grammar(json.dumps(arg.json_schema)) + ','
        else:
            lm += arg.name + '=' + json_schema_to_grammar(json.dumps(arg.json_schema)) + ','
    if signature_schema.var_args is not None:
        arg = signature_schema.var_args
        lm += (json_schema_to_grammar(json.dumps(arg.json_schema)) + ',')
    for arg in signature_schema.keyword_only:
        lm += arg.name + '=' + json_schema_to_grammar(json.dumps(arg.json_schema)) + ','
    if signature_schema.var_kwargs is not None:
        arg = signature_schema.var_kwargs
        lm += (_SAFE_NAME+'='+json_schema_to_grammar(json.dumps(arg.json_schema)))
    return lm


def foo(a:bool,b:int,c:list[int], /, d:float,e:bool,f:int=8, *args:bool, g:int,h:bool,i:bool=False, **kwds:bool):
    print(args)

signature_schema = SignatureSchema.from_callable(foo)
print(signature_schema.model_dump_json(indent=2))

from guidance.models import Mock
try: 
    model
except NameError:
    model = Mock()

m = model + 'foo('+signature_schema.gen()+')'