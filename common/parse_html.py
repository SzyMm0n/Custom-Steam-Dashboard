import re
import html

async def parse_html_tags(html_string):
    """
    Parses HTML tags from a given HTML string.

    Args:
        html_string (str): The HTML string to parse.
    Returns:
        str: Cleaned text without HTML tags.
    """
    clean = re.sub(r"<[^>]+>", "", html_string)
    clean = html.unescape(clean)
    return clean.strip()