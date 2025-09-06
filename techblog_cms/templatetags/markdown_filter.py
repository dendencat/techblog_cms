import markdown
from django import template
from django.utils.safestring import mark_safe
import bleach

register = template.Library()

@register.filter
def markdown_to_html(text):
    """
    Convert markdown text to HTML with Pygments for syntax highlighting and bleach for sanitization
    """
    if not text:
        return ''

    # Convert markdown to HTML with Pygments for syntax highlighting
    html = markdown.markdown(text, extensions=[
        'extra',           # Extra features like tables, footnotes, and raw HTML
        'codehilite',      # Code highlighting with Pygments
        'toc',            # Table of contents
        'fenced_code',     # Fenced code blocks
        'nl2br',          # Convert newlines to <br>
    ], extension_configs={
        'codehilite': {
            'linenums': False,  # Disable line numbers
            'guess_lang': True,  # Guess language if not specified
            'css_class': 'highlight',  # CSS class for code blocks
            'pygments_style': 'github-dark',  # Use GitHub-like dark theme
        }
    })

    # Sanitize HTML to prevent XSS attacks
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'code', 'pre', 'ul', 'ol', 'li', 'a', 'img', 'table',
        'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span'
    ]
    allowed_attributes = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title'],
        'code': ['class'],
        'pre': ['class'],
        'div': ['class'],
        'span': ['class'],
        'table': ['class'],
        'th': ['class'],
        'td': ['class'],
        'tr': ['class']
    }

    sanitized_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes, strip=True)

    return mark_safe(sanitized_html)
