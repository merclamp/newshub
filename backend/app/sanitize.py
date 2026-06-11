import nh3

ALLOWED_TAGS = {
    "a", "p", "br", "hr",
    "strong", "em", "b", "i", "u", "s", "sub", "sup",
    "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "blockquote", "pre", "code",
    "img", "figure", "figcaption",
    "table", "thead", "tbody", "tr", "td", "th",
    "span", "div",
}

ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title", "loading"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
}


def sanitize_html(raw: str) -> str:
    if not raw:
        return ""
    return nh3.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        # h1 — это заголовок статьи: он уже показан отдельно, убираем вместе с текстом,
        # чтобы не дублировался (trafilatura включает title в начало HTML).
        clean_content_tags={"h1"},
        url_schemes={"http", "https"},
        link_rel="noopener noreferrer",
    ).strip()
