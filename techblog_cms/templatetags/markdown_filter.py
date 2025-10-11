import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def _resolve_linkify_extension():
    """Return a linkify extension instance if one is available."""
    try:
        from markdown.extensions.linkify import LinkifyExtension

        return LinkifyExtension()
    except ImportError:
        try:
            from pymdownx.magiclink import MagiclinkExtension

            # Magiclink provides linkify behaviour when Markdown's native
            # extension is unavailable.
            return MagiclinkExtension()
        except ImportError:
            return None


@register.filter
def markdown_to_html(text):
    """Convert markdown text to HTML with optional auto-linking."""
    if not text:
        return ""

    extensions = [
        "extra",  # Extra features like tables, footnotes, and raw HTML
        "codehilite",  # Code highlighting with Pygments
        "toc",  # Table of contents
        "fenced_code",  # Fenced code blocks
        "nl2br",  # Convert newlines to <br>
    ]

    linkify_extension = _resolve_linkify_extension()
    if linkify_extension:
        extensions.append(linkify_extension)

    html = markdown.markdown(
        text,
        extensions=extensions,
        extension_configs={
            "codehilite": {
                "linenums": False,  # Disable line numbers
                "guess_lang": True,  # Guess language if not specified
                "css_class": "highlight",  # CSS class for code blocks
                "pygments_style": "github-dark",  # Use GitHub-like dark theme
            }
        },
    )

    return mark_safe(html)
