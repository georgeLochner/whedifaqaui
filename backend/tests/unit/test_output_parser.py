"""Unit tests for pipe-delimited output parser."""

from app.services.output_parser import parse_pipe_delimited


def test_parse_entity_record():
    """ENTITY|name|type|description parsed correctly."""
    text = "ENTITY|AWS Cognito|system|Authentication service"
    result = parse_pipe_delimited(text)
    assert len(result["entities"]) == 1
    assert result["entities"][0] == {
        "name": "AWS Cognito",
        "type": "system",
        "description": "Authentication service"
    }


def test_parse_relationship_record():
    """REL|source|relation|target|timestamp parsed correctly."""
    text = "REL|Cognito|replaced|Auth0|125"
    result = parse_pipe_delimited(text)
    assert len(result["relationships"]) == 1
    assert result["relationships"][0] == {
        "source": "Cognito",
        "relation": "replaced",
        "target": "Auth0",
        "timestamp": 125.0
    }


def test_parse_speaker_record():
    """SPEAKER|id|name|confidence parsed correctly."""
    text = "SPEAKER|SPEAKER_00|John Smith|0.9"
    result = parse_pipe_delimited(text)
    assert "SPEAKER_00" in result["speakers"]
    assert result["speakers"]["SPEAKER_00"] == {
        "name": "John Smith",
        "confidence": 0.9
    }


def test_parse_frame_record():
    """FRAME|timestamp|reason parsed correctly."""
    text = "FRAME|45.5|Slide transition"
    result = parse_pipe_delimited(text)
    assert len(result["frames"]) == 1
    assert result["frames"][0] == {
        "timestamp": 45.5,
        "reason": "Slide transition"
    }


def test_parse_topic_record():
    """TOPIC|name parsed correctly."""
    text = "TOPIC|Authentication Migration"
    result = parse_pipe_delimited(text)
    assert result["topics"] == ["Authentication Migration"]


def test_skip_comments():
    """Lines starting with # are ignored."""
    text = "# This is a comment\nENTITY|Foo|system|Bar"
    result = parse_pipe_delimited(text)
    assert len(result["entities"]) == 1
    assert result["entities"][0]["name"] == "Foo"


def test_skip_empty_lines():
    """Empty/whitespace lines are ignored."""
    text = "ENTITY|Foo|system|Bar\n\n   \nTOPIC|Auth"
    result = parse_pipe_delimited(text)
    assert len(result["entities"]) == 1
    assert len(result["topics"]) == 1


def test_empty_fields():
    """TYPE|value||value handles empty field gracefully."""
    text = "ENTITY|Cognito|system|"
    result = parse_pipe_delimited(text)
    assert result["entities"][0]["description"] == ""

    text2 = "REL|A|uses|B|"
    result2 = parse_pipe_delimited(text2)
    assert result2["relationships"][0]["timestamp"] is None


def test_mixed_record_types():
    """Multiple record types in one text block."""
    text = """# Header comment
ENTITY|AWS Cognito|system|Auth service
ENTITY|Auth0|system|Old auth
REL|Cognito|replaced|Auth0|125
SPEAKER|SPEAKER_00|John|0.95
FRAME|30.0|Topic change
TOPIC|Authentication
TOPIC|Migration"""
    result = parse_pipe_delimited(text)
    assert len(result["entities"]) == 2
    assert len(result["relationships"]) == 1
    assert len(result["speakers"]) == 1
    assert len(result["frames"]) == 1
    assert len(result["topics"]) == 2
