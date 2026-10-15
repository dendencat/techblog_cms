import hashlib
import html as html_lib
import importlib
import logging
import re
import markdown
import nh3
from django import template
from django.conf import settings
from django.core.cache import cache
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from markdown.extensions.toc import slugify_unicode

register = template.Library()
logger = logging.getLogger(__name__)

LINKIFY_EXTENSION = None
try:
    importlib.import_module('markdown.extensions.linkify')
    LINKIFY_EXTENSION = 'markdown.extensions.linkify'
except ModuleNotFoundError:
    try:
        # Fallback when Markdown's native linkify is unavailable.
        importlib.import_module('pymdownx.magiclink')
        LINKIFY_EXTENSION = 'pymdownx.magiclink'
    except ModuleNotFoundError:
        logger.warning(
            'Neither markdown.extensions.linkify nor pymdownx.magiclink available; '
            'falling back to plain-URL rewriter.'
        )

IMG_TAG_SRC_PATTERN = re.compile(r'(<img[^>]+src=")([^"]+)(")')
RELATIVE_URI_PATTERN = re.compile(r'^(?:[a-z][a-z0-9+.-]*:|/)', re.IGNORECASE)
PLAIN_URL_PATTERN = re.compile(r'(?<![\"=])(https?://[^\s<]+)')


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


def _linkify_plain_urls(html: str) -> str:
    if LINKIFY_EXTENSION or not html:
        return html

    def _replace(match: re.Match) -> str:
        url = match.group(1).rstrip('.,)')
        trailing = match.group(1)[len(url):]
        return f'<a href="{url}">{url}</a>{trailing}'

    return PLAIN_URL_PATTERN.sub(_replace, html)


# Rendered Markdown is sanitized with an allowlist before it is marked safe, so raw
# HTML in an article (e.g. <script>, onerror=, javascript: links) can never reach
# readers' browsers, even if an author account is compromised.
ALLOWED_TAGS = {
    'a', 'abbr', 'blockquote', 'br', 'code', 'dd', 'del', 'div', 'dl', 'dt', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'img', 'ins', 'li', 'ol', 'p', 'pre',
    'span', 'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead',
    'tr', 'ul',
}
_HEADING_ATTRS = {'id'}
ALLOWED_ATTRIBUTES = {
    'a': {'href', 'title', 'id', 'class'},
    'abbr': {'title'},
    'code': {'class'},
    'div': {'class', 'id'},
    'h1': _HEADING_ATTRS, 'h2': _HEADING_ATTRS, 'h3': _HEADING_ATTRS,
    'h4': _HEADING_ATTRS, 'h5': _HEADING_ATTRS, 'h6': _HEADING_ATTRS,
    'img': {'src', 'alt', 'title'},
    'li': {'id'},
    'ol': {'class'},
    'pre': {'class'},
    'span': {'class'},
    'sup': {'id', 'class'},
    'td': {'style'},
    'th': {'style'},
}
ALLOWED_URL_SCHEMES = {'http', 'https', 'mailto'}
ALLOWED_STYLE_PROPERTIES = {'text-align'}


def sanitize_html(html: str) -> str:
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        filter_style_properties=ALLOWED_STYLE_PROPERTIES,
        link_rel='noopener noreferrer',
    )


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
            'guess_lang': False,
            'css_class': 'highlight',
            'pygments_style': 'github-dark',
        },
        'toc': {
            # Keep Japanese headings addressable (the default slugify drops non-ASCII).
            'slugify': slugify_unicode,
            'permalink': '#',
            'permalink_class': 'headerlink',
            'permalink_title': 'この見出しへのリンク',
        },
    })

    html = _linkify_plain_urls(html)
    return mark_safe(sanitize_html(_rewrite_image_sources(html)))


HEADING_PATTERN = re.compile(r'<h([23]) id="([^"]+)">(.*?)</h\1>', re.DOTALL)
HEADERLINK_PATTERN = re.compile(r'<a class="headerlink"[^>]*>.*?</a>', re.DOTALL)
PRE_BLOCK_PATTERN = re.compile(r'<pre[\s>].*?</pre>|<div class="highlight">.*?</div>', re.DOTALL)
WHITESPACE_PATTERN = re.compile(r'\s+')


def extract_toc(html: str):
    """Return ``[{'level', 'id', 'text'}]`` for the h2/h3 headings of rendered article HTML."""
    entries = []
    for level, anchor, inner in HEADING_PATTERN.findall(str(html or '')):
        text = html_lib.unescape(strip_tags(HEADERLINK_PATTERN.sub('', inner))).strip()
        if text:
            entries.append({'level': int(level), 'id': anchor, 'text': text})
    return entries


def markdown_to_plain_text(text, max_length=None):
    """Readable plain text of a Markdown document (code blocks dropped), for summaries."""
    if not text:
        return ''
    cache_key = 'md_plain:v1:' + hashlib.sha256(text.encode('utf-8')).hexdigest()
    plain = cache.get(cache_key)
    if plain is None:
        rendered = PRE_BLOCK_PATTERN.sub(' ', str(markdown_to_html(text)))
        rendered = HEADERLINK_PATTERN.sub('', rendered)
        plain = WHITESPACE_PATTERN.sub(' ', html_lib.unescape(strip_tags(rendered))).strip()
        cache.set(cache_key, plain, timeout=60 * 60 * 24)
    if max_length and len(plain) > max_length:
        return plain[:max_length].rstrip() + '…'
    return plain


def bind_inline_images(html: str, inline_images) -> str:
    """Point bare-filename image references at *this* article's uploads.

    ``![x](diagram.png)`` resolves to ``/media/articles/diagram.png``; when two articles
    upload a file with the same name the storage renames the second one, so the bare
    name would show the other article's image. Rewrite those references to the URL of
    the matching image attached to the article being rendered.
    """
    by_name = {}
    for inline_image in inline_images:
        by_name.setdefault(inline_image.filename, inline_image.image.url)
    if not html or not by_name:
        return html
    media_url = getattr(settings, 'MEDIA_URL', '/media/').rstrip('/') or '/media'
    bare_prefix = f'{media_url}/articles/'

    def _replace(match: re.Match) -> str:
        prefix, src, suffix = match.groups()
        if src.startswith(bare_prefix):
            name = src[len(bare_prefix):]
            if '/' not in name and name in by_name:
                src = by_name[name]
        return f'{prefix}{src}{suffix}'

    return mark_safe(IMG_TAG_SRC_PATTERN.sub(_replace, str(html)))
