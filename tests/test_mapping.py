import pytest
import json
from main import cleanup_text, parse_person_name, try_parse_json_list, map_to_schema_org

def test_cleanup_text_html_tags():
    html_input = "<div class=\"row\">Hello <br> world! <p>This is a test.</p></div>"
    expected = "Hello world! This is a test."
    assert cleanup_text(html_input) == expected

def test_cleanup_text_newlines():
    newline_input = "Line 1\r\nLine 2\nLine 3"
    expected = "Line 1 Line 2 Line 3"
    assert cleanup_text(newline_input) == expected

def test_cleanup_text_entities():
    entity_input = "Me &amp; You &quot;Test&quot;"
    expected = 'Me & You "Test"'
    assert cleanup_text(entity_input) == expected

def test_cleanup_text_spaces():
    space_input = "  Too    many    spaces   "
    expected = "Too many spaces"
    assert cleanup_text(space_input) == expected

def test_parse_person_name_simple():
    res = parse_person_name("John Doe")
    assert res == {"name": "John Doe", "givenName": "John", "familyName": "Doe"}

def test_parse_person_name_middle():
    res = parse_person_name("John Middle Doe")
    assert res == {"name": "John Middle Doe", "givenName": "John Middle", "familyName": "Doe"}

def test_parse_person_name_single():
    res = parse_person_name("John")
    assert res == {"name": "John", "givenName": "John"}

def test_parse_person_name_empty():
    assert parse_person_name("") == {}
    assert parse_person_name(None) == {}

def test_try_parse_json_list_valid():
    json_str = '[{"name": "A"}, {"name": "B"}]'
    res = try_parse_json_list(json_str)
    assert len(res) == 2
    assert res[0]["name"] == "A"

def test_try_parse_json_list_dict():
    json_str = '{"name": "A"}'
    res = try_parse_json_list(json_str)
    assert len(res) == 1
    assert res[0]["name"] == "A"

def test_try_parse_json_list_invalid():
    assert try_parse_json_list("not json") == []
    assert try_parse_json_list(None) == []

def test_map_to_schema_org():
    mock_ckan = {
        "title": "Test Dataset",
        "notes": "Description with <p>tags</p>",
        "id": "123",
        "name": "test-dataset",
        "license_title": "MIT",
        "metadata_created": "2024-01-01",
        "tags": [{"display_name": "Tag1"}],
        "author": '[{"author_name": "Jane Smith", "author_email": "jane@example.com"}]',
        "resources": [
            {
                "name": "Resource 1",
                "url": "http://res.url",
                "format": "CSV"
            }
        ]
    }
    res = map_to_schema_org(mock_ckan)
    assert res["@type"] == "Dataset"
    assert res["name"] == "Test Dataset"
    assert res["description"] == "Description with tags"
    assert res["creator"][0]["givenName"] == "Jane"
    assert res["creator"][0]["familyName"] == "Smith"
    assert res["distribution"][0]["contentUrl"] == "http://res.url"
