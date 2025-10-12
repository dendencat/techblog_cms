import importlib
import logging
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()
logger = logging.getLogger(__name__)

LINKIFY_EXTENSION = None
try:
    importlib.import_module('markdown.extensions.linkify')
    LINKIFY_EXTENSION = 'markdown.extensions.linkify'
except ModuleNotFoundError:
    logger.warning('markdown.extensions.linkify not available; auto-linking disabled.')

@register.filter
def markdown_to_html(text):
    """
    Convert markdown text to HTML
    """
    if not text:
        return ''

    extensions = [
        'extra',
        'codehilite',
        'toc',
        'fenced_code',
        'nl2br',
    ]
    if LINKIFY_EXTENSION:
        extensions.append(LINKIFY_EXTENSION)

    html = markdown.markdown(text, extensions=extensions, extension_configs={
        'codehilite': {
            'linenums': False,
            'guess_lang': True,
            'css_class': 'highlight',
            'pygments_style': 'github-dark',
        }
    })

    return mark_safe(html)
