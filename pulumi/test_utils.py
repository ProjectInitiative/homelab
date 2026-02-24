from utils import camel_to_snake

def test_camel_to_snake_basic():
    assert camel_to_snake("CamelCase") == "camel_case"
    assert camel_to_snake("camelCase") == "camel_case"

def test_camel_to_snake_acronyms():
    assert camel_to_snake("HTTPResponse") == "http_response"
    assert camel_to_snake("myHTTPResponse") == "my_http_response"
    assert camel_to_snake("JSONData") == "json_data"

def test_camel_to_snake_already_snake():
    assert camel_to_snake("already_snake_case") == "already_snake_case"
    assert camel_to_snake("simple") == "simple"

def test_camel_to_snake_numbers():
    assert camel_to_snake("User123Profile") == "user123_profile"
    assert camel_to_snake("v1Alpha1") == "v1_alpha1"

def test_camel_to_snake_single_char():
    assert camel_to_snake("A") == "a"
    assert camel_to_snake("a") == "a"

def test_camel_to_snake_empty():
    assert camel_to_snake("") == ""

def test_camel_to_snake_mixed_case_with_underscore():
    # Note: the current implementation results in double underscores if an underscore
    # precedes a CamelCase word.
    assert camel_to_snake("some-mixed_Case") == "some-mixed__case"
