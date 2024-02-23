from textwrap import dedent
from .base import PromptHelper


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
        """
    ).strip("\n")
