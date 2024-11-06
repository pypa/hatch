def on_page_markdown(
    markdown,
    page,
    **kwargs,  # noqa: ARG001
):
    if 'title' in page.meta:
        return

    first_line = markdown.strip().splitlines()[0]
    if first_line.startswith('# '):
        title = first_line[2:].split(' # {:', maxsplit=1)[0].strip()
        page.meta['title'] = title
        page.meta['social'] = {'cards_layout_options': {'title': title}}
