from textwrap import dedent
from pydantic import BaseModel, TypeAdapter
from minml.types import Type
from .base import PromptHelper, Response


class GrepPrompt(PromptHelper):
    SYSTEM_MESSAGE = "Pay close attention to the schema and type of object the user is looking for. If there are no objects of the type the user is looking for, return an empty list."

    # Shamelessly stolen from llamaindex
    USER_MESSAGE = dedent(
        """
        Please find each `{type}` in the text below.
        ---------------------
        {text}
        ---------------------
        """
    ).strip("\n")

    def __call__(self, name: str, object_schema: Type | type, text: str) -> Response:
        return super().__call__(object_schema=list[object_schema], type=name, text=text)
