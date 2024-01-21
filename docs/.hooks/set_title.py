from __future__ import annotations

from markdown.preprocessors import Preprocessor


class TitleMetadataPreprocessor(Preprocessor):
    def run(self, lines):  # noqa: PLR6301
        front_matter_indices = []
        page_title: str | None = None
        page_title_index = 0
        for i, line in enumerate(lines):
            if line.startswith('---'):
                front_matter_indices.append(i)
            elif line.startswith('# '):
                page_title_index = i
                page_title = line[2:]
                break

        if page_title is None:
            return lines

        if not front_matter_indices:
            return [
                '---',
                f'title: {page_title}',
                '---',
                '',
                *lines,
            ]

        front_matter_start = front_matter_indices[0] + 1
        for i in range(front_matter_start, front_matter_indices[1]):
            if i > page_title_index:
                return lines

            line = lines[i]
            if line.startswith('title: '):
                return lines

        new_lines = list(lines)
        new_lines.insert(front_matter_start, f'title: {page_title}')
        return new_lines
