import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def markdown_to_html(text):
    """
    Convert markdown text to HTML
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

    return mark_safe(html)
