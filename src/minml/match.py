import pyparsing as pp

CLOSERS = {
    "(": ")",
    "{": "}",
    "[": "]",
}

__all__ = [
    'match',
]

def match(text, opener="(", closer=None):
    if closer is None:
        closer = CLOSERS[opener]
    scanner = pp.original_text_for(pp.nested_expr(opener, closer))
    matches = scanner.search_string(text)
    return [match[0] for match in matches.as_list()]
