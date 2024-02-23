#!/usr/bin/env python

import sys
import argparse
import json
from pydantic import RootModel, create_model
from pydantic.json_schema import to_jsonable_python
from pydantic.fields import PydanticUndefined

from gpts import Mistral
from guidance.models import LlamaCppChat
from minml.prompt.grep import GrepPrompt


def dumps(obj):
    return json.dumps(obj, default=to_jsonable_python)


def get_model():
    from minml.util import suppress_stdout_stderr

    with suppress_stdout_stderr():
        model = Mistral(verbose=False)
    return LlamaCppChat(model.llm, echo=False)


def parse_args(argv):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument("irregex")
    parser.add_argument("--schema", type=str)
    parser.add_argument("file", nargs="?")
    args = parser.parse_args(argv)

    if args.file is None:
        file = sys.stdin
    else:
        file = open(args.file)
    text = file.read()

    if args.schema:
        schema = {}
        for item in args.schema.split(","):
            item = item.replace(" ", "")
            name, *ta = item.split("=")
            assert len(ta) <= 1
            if not ta:
                ta = str
            else:
                ta = eval(ta[0])
            schema[name] = (ta, PydanticUndefined)
        Schema = create_model(args.irregex.capitalize(), **schema)
    else:
        Schema = create_model(
            args.irregex.capitalize(), root=(str, PydanticUndefined), __base__=RootModel
        )
    return argparse.Namespace(text=text, irregex=args.irregex, schema=Schema)


def main(argv=None):
    args = parse_args(argv)

    model = get_model()
    prompt = GrepPrompt(model)
    response = prompt(text=args.text, object_schema=args.schema, name=args.irregex)
    # print("\n".join(dumps(c) for c in response.object))
    print(response.prompt_with_completion)


if __name__ == "__main__":
    main(sys.argv[1:])
