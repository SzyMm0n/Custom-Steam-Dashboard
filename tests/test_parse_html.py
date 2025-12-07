"""
Unit tests for HTML parsing utilities.
"""
import pytest
from server.services.parse_html import parse_html_tags


class TestParseHTMLTags:
    """Test cases for parse_html_tags function."""

    @pytest.mark.asyncio
    async def test_simple_html_removal(self):
        """Test removal of simple HTML tags."""
        html_input = "<p>This is a test</p>"
        result = await parse_html_tags(html_input)
        assert result == "This is a test"

    @pytest.mark.asyncio
    async def test_nested_html_removal(self):
        """Test removal of nested HTML tags."""
        html_input = "<div><p>Nested <strong>HTML</strong> tags</p></div>"
        result = await parse_html_tags(html_input)
        assert result == "Nested HTML tags"

    @pytest.mark.asyncio
    async def test_html_entities_decoding(self):
        """Test decoding of HTML entities."""
        html_input = "This &amp; that &lt;test&gt;"
        result = await parse_html_tags(html_input)
        assert result == "This & that <test>"

    @pytest.mark.asyncio
    async def test_whitespace_normalization(self):
        """Test normalization of whitespace."""
        html_input = "<p>Too    many   spaces</p>"
        result = await parse_html_tags(html_input)
        assert result == "Too many spaces"

    @pytest.mark.asyncio
    async def test_newline_and_tab_removal(self):
        """Test removal of newlines and tabs."""
        html_input = "<p>Line 1\nLine 2\tTabbed</p>"
        result = await parse_html_tags(html_input)
        assert result == "Line 1 Line 2 Tabbed"

    @pytest.mark.asyncio
    async def test_empty_string(self):
        """Test parsing of empty string."""
        html_input = ""
        result = await parse_html_tags(html_input)
        assert result == ""

    @pytest.mark.asyncio
    async def test_plain_text(self):
        """Test parsing of plain text without HTML."""
        html_input = "Just plain text"
        result = await parse_html_tags(html_input)
        assert result == "Just plain text"

    @pytest.mark.asyncio
    async def test_complex_html(self):
        """Test parsing of complex HTML with multiple elements."""
        html_input = """
        <div class="description">
            <h1>Game Title</h1>
            <p>This is a <strong>great</strong> game with <em>amazing</em> graphics.</p>
            <ul>
                <li>Feature 1</li>
                <li>Feature 2</li>
            </ul>
        </div>
        """
        result = await parse_html_tags(html_input)
        assert "Game Title" in result
        assert "great" in result
        assert "amazing" in result
        assert "Feature 1" in result
        assert "Feature 2" in result

    @pytest.mark.asyncio
    async def test_html_with_attributes(self):
        """Test removal of HTML tags with attributes."""
        html_input = '<a href="https://example.com" class="link">Click here</a>'
        result = await parse_html_tags(html_input)
        assert result == "Click here"

    @pytest.mark.asyncio
    async def test_self_closing_tags(self):
        """Test handling of self-closing tags."""
        html_input = "Before<br/>After<hr/>End"
        result = await parse_html_tags(html_input)
        assert result == "BeforeAfterEnd"

    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test handling of special HTML entities."""
        html_input = "&nbsp;&copy;&reg;&trade;"
        result = await parse_html_tags(html_input)
        # Check that entities are decoded (check for at least one known character)
        assert len(result) > 0
        # Use chr() to avoid encoding issues
        # Check for copyright (©), registered (®), or trademark (™) symbols
        assert '\xa0' in result or ' ' in result or chr(169) in result or chr(174) in result or chr(8482) in result
