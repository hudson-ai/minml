from abc import ABC
from contextlib import nullcontext
from typing import Generic, TypeVar
from textwrap import dedent

from pydantic import TypeAdapter, BaseModel, ValidationError

import guidance
from guidance import role, block, gen
from guidance.models import Model, Chat
from guidance._grammar import RawFunction

from ..types import Type, gen_type
from ..util import resolve_refs


T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    prompt_with_completion: str
    completion: str
    object: T | None
    error: str | None


class PromptHelper(ABC):
    SYSTEM_MESSAGE: str | None = None
    USER_MESSAGE: str

    def __init__(self, lm: Model):
        self.lm = lm

    def __call__(self, object_schema: Type | None = None, **kwds) -> Response:
        lm = self.lm + self.function(
            **kwds, response_type=object_schema, capture_name="result"
        )
        result = lm["result"]
        if object_schema is not None:
            try:
                object = TypeAdapter(object_schema).validate_json(result)
            except ValidationError as e:
                error = str(e)
                object = None
            else:
                error = None

        return Response[object_schema](
            prompt_with_completion=str(lm),
            completion=lm["result"],
            object=object,
            error=error,
        )

    @classmethod
    def function(
        cls, response_type: Type | None = None, capture_name: str = "response", **kwds
    ) -> RawFunction:
        return _prompt_with_system_and_user_message(
            system_message=cls.SYSTEM_MESSAGE,
            user_message=cls.USER_MESSAGE,
            response_type=response_type,
            capture_name=capture_name,
            **kwds,
        )


@guidance(stateless=False)
def _prompt_with_system_and_user_message(
    lm: Model,
    system_message: str,
    user_message: str,
    capture_name: str | None,
    response_type: Type | None,
    **kwds,
):
    system = role("system") if isinstance(lm, Chat) else nullcontext
    user = role("user") if isinstance(lm, Chat) else nullcontext
    assistant = role("assistant") if isinstance(lm, Chat) else nullcontext
    if system_message is not None:
        with system:
            lm += system_message.format(**kwds)
    with user:
        lm += user_message.format(**kwds)
        if response_type is not None:
            lm += "\n" + _formatting_instructions(response_type)
    with assistant, block(capture_name):
        if response_type is None:
            grammar = gen()
        else:
            # TODO: add type-hints to the user/system bit?
            grammar = gen_type(response_type)
        lm += grammar
    return lm


def _formatting_instructions(type):
    # Shamelessly stolen from langchain
    return dedent(
        """
        The output should be formatted as a JSON instance that conforms to the JSON schema below.
        
        As an example, for the schema {{"properties": {{"foo": {{"title": "Foo", "description": "a list of strings", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
        the object {{"foo": ["bar", "baz"]}} is a well-formatted instance of the schema. The object {{"properties": {{"foo": ["bar", "baz"]}}}} is not well-formatted.
        
        Here is the output schema:
        ```
        {schema}
        ```
        """
    ).format(schema=TypeAdapter(type).json_schema())
