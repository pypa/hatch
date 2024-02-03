def on_page_content(
    html,  # noqa: ARG001
    page,
    **kwargs,  # noqa: ARG001
):
    if title := page._title_from_render:  # noqa: SLF001
        page.meta['title'] = title
