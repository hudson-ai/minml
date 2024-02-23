from abc import ABC
from contextlib import nullcontext
from pydantic import TypeAdapter
import guidance
from guidance import role, block, gen
from guidance.models import Model, Chat
from guidance._grammar import RawFunction
from minml import gen_type
from minml.types import Type

from textwrap import dedent


class PromptHelper(ABC):
    SYSTEM_MESSAGE: str | None = None
    USER_MESSAGE: str

    def __init__(self, lm: Model):
        self.lm = lm

    def __call__(self, response_type: Type | None = None, **kwds) -> str:
        lm = self.lm + self.function(
            **kwds, response_type=response_type, capture_name="result"
        )
        result = lm["result"]
        if response_type is not None:
            result = TypeAdapter(response_type).validate_json(result)
        return result

    @classmethod
    def function(
        cls, response_type=None, capture_name="response", **kwds
    ) -> RawFunction:

        @guidance(stateless=False, dedent=False)
        def wrapped(lm):
            system = role("system") if isinstance(lm, Chat) else nullcontext
            user = role("user") if isinstance(lm, Chat) else nullcontext
            assistant = role("assistant") if isinstance(lm, Chat) else nullcontext
            if cls.SYSTEM_MESSAGE is not None:
                with system:
                    lm += cls.SYSTEM_MESSAGE.format(**kwds)
            with user:
                lm += cls.USER_MESSAGE.format(**kwds)
            with assistant, block(capture_name):
                if response_type is None:
                    grammar = gen()
                else:
                    # TODO: add type-hints to the user/system bit?
                    grammar = gen_type(response_type)
                lm += grammar
            return lm

        return wrapped()


class DBQPrompt(PromptHelper):
    # Shamelessly stolen from llamaindex
    SYSTEM_MESSAGE = dedent(
        """
        You are an expert Q&A system that is trusted around the world.
        Always answer the query using the provided context information, and not prior knowledge.
        Some rules to follow:
        1. Never directly reference the given context in your answer.
        2. Avoid statements like 'Based on the context, ...' or 'The context information ...' or anything along those lines.
        """
    ).strip("\n")

    # Shamelessly stolen from llamaindex
    USER_MESSAGE = dedent(
        """
        Context information from multiple sources is below.
        ---------------------
        {context_str}
        ---------------------
        Given the information from multiple sources and not prior knowledge, answer the query.
        
        Query: {query_str}
        Answer: 
    """
    ).strip("\n")


# from guidance.models import LlamaCppChat
# from gpts.models import Mistral

# # model = LlamaCppChat(
# #     model=Mistral(context_length=2048).llm,
# #     echo=False,
# # )

# context = """
# Comparative Opinion Summarization

# The problem CoCoSum tackles is the comparative opinion summarization problem: given two sets of reviews for two entities such as hotels, we define contrastive opinions of a target entity A against a counterpart entity B as subjective information that is described only in the set of target entity’s reviews, but not in the counterpart entity’s reviews. We refer to the summary that contains such opinions as a contrastive summary. Similarly, we define common opinions of entities A and B as subjective information that is described in both sets of reviews. We refer to the summary that contains common opinions as a common summary.

# We formalize comparative opinion summarization as a task that generates two sets of contrastive summaries and one common summary from two sets of reviews for a pair of entities A and B (as shown in the Figure 2).

# On top of this formalization, we created the first comparative opinion summarization benchmark dataset, CoCoTrip, which includes 96 human-written contrastive summaries and 48 common summaries. The CoCoTrip dataset is available here: https://github.com/megagonlabs/cocosum
# CoCoSum

# """

# from pydantic import AnyUrl

# question = "What's the url?"


# from pydantic import BaseModel


# class URL(BaseModel):
#     address: str


# # # interface 1
# prompt_func = DBQPrompt(model)
# result1 = prompt_func(context_str=context, query_str=question, response_type=URL)

# # # interface 2
# # m = model + DBQPrompt.function(
# #     context_str=context, query_str=question, capture_name="result", response_type=URL
# # )
# # result2 = m["result"]
