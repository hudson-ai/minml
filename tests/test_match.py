import pytest
import minml

def test_nested():
    thing = """
        Hey boss sure thing, I can get you some json. Here it is! 
        {'hello': 'there'}
        I can also give you some more if you'd like
        {'this': 'is useful'}
    """
    matches = minml.match(thing, '{')
    assert len(matches) == 2
    assert matches[0] == "{'hello': 'there'}"
    assert matches[1] == "{'this': 'is useful'}"
