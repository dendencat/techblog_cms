import importlib
import logging
import re
import markdown
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()
logger = logging.getLogger(__name__)

LINKIFY_EXTENSION = None
try:
    importlib.import_module('markdown.extensions.linkify')
    LINKIFY_EXTENSION = 'markdown.extensions.linkify'
except ModuleNotFoundError:
    logger.warning('markdown.extensions.linkify not available; auto-linking disabled.')

IMG_TAG_SRC_PATTERN = re.compile(r'(<img[^>]+src=")([^"]+)(")')
RELATIVE_URI_PATTERN = re.compile(r'^(?:https?:|data:|/)', re.IGNORECASE)


def _resolve_image_source(src: str) -> str:
    """Translate a user-provided Markdown image reference into a public media URL."""
    if not src:
        return ''
    candidate = src.strip()
    if not candidate or RELATIVE_URI_PATTERN.match(candidate):
        return candidate

    media_url = getattr(settings, 'MEDIA_URL', '/media/').rstrip('/') or '/media'
    if candidate.startswith('articles/'):
        path = candidate
    else:
        path = f"articles/{candidate.lstrip('/')}"
    return f"{media_url}/{path}"


def _rewrite_image_sources(html: str) -> str:
    if not html:
        return html

    def _replace(match: re.Match) -> str:
        prefix, src, suffix = match.groups()
        return f'{prefix}{_resolve_image_source(src)}{suffix}'

    return IMG_TAG_SRC_PATTERN.sub(_replace, html)

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

    return mark_safe(_rewrite_image_sources(html))
