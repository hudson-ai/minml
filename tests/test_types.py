import os
import pytest
from typing import Annotated
from guidance import block
from guidance.models import LlamaCpp
from pydantic import BaseModel, TypeAdapter, StringConstraints
from minml import types

MODEL_FILE = os.path.expanduser("~/pkg/mistral/mistral-7b-instruct.gguf")


@pytest.fixture(scope="session")
def model():
    return LlamaCpp(MODEL_FILE, echo=False)


@pytest.fixture(scope="session")
def guy_schema():
    class Guy(BaseModel):
        name: str
        age: int
        pets: list[str]

    return Guy


def test_gen_str(model):
    m = model + "here's my favorite four letter word: "
    with block("str"):
        m += types.gen_str()
    TypeAdapter(str).validate_json(m["str"])

def test_regex(model):
    type = Annotated[str, StringConstraints(pattern=r'[A-Z]\d')]
    m = model + "my favorite steak sauce is "
    with block("str"):
        m += types.gen_type(type)
    o = TypeAdapter(type).validate_json(m['str'])
    assert o == 'A1'

def test_gen_int(model):
    m = model + "9 + 2 = "
    with block("int"):
        m += types.gen_int()
    o = TypeAdapter(int).validate_json(m["int"])
    assert o == 11

def test_gen_float(model):
    m = model + "9.5 + 2 = "
    with block("float"):
        m += types.gen_float()
    o = TypeAdapter(float).validate_json(m["float"])
    assert o == 11.5

def test_gen_bool(model):
    m = model + "Q: 9 == 2, true or false? A: "
    with block("bool"):
        m += types.gen_bool()
    o = TypeAdapter(bool).validate_json(m["bool"])
    assert o == False

def test_gen_schema(model, guy_schema):
    m = model + "A dude: "
    with block("guy"):
        m += types.gen_schema(guy_schema)
    guy_schema.model_validate_json(m["guy"])


def test_gen_schemas(model, guy_schema):
    m = model + "Two dudes (in json format): "
    with block("guys"):
        m += types.gen_type(list[guy_schema])
    objs = TypeAdapter(list[guy_schema]).validate_json(m["guys"])
    assert len(objs) == 2
