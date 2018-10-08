import re

import markdown_code_blocks
import markupsafe


ID_RE = re.compile(r'\[\]\(#([a-z0-9-]+)\)')
SPECIAL_CHARS_RE = re.compile('[^a-z0-9 _-]')


ROW = '=r='
COL = '    =c= '
INDENT = ' ' * 8


def _render_table(code: str) -> str:
    """Renders our custom "table" type

    ```table
    =r=
        =c= col1
        =c= col2
    =r=
        =c= col3
        =c= col4
    ```

    renders to

    <table class="table table-bordered">
        <tbody>
            <tr><td>col1</td><td>col2</td></tr>
            <tr><td>col3</td><td>col4</td></tr>
        </tbody>
    </table>
    """
    output = ['<table class="table table-bordered"><tbody>']
    in_row = False
    col_buffer = None

    def _maybe_end_col() -> None:
        nonlocal col_buffer
        if col_buffer is not None:
            output.append(f'<td>{md(col_buffer)}</td>')
            col_buffer = None

    def _maybe_end_row() -> None:
        nonlocal in_row
        if in_row:
            output.append('</tr>')
            in_row = False

    for line in code.splitlines(True):
        if line.startswith(ROW):
            _maybe_end_col()
            _maybe_end_row()
            in_row = True
            output.append('<tr>')
        elif line.startswith(COL):
            _maybe_end_col()
            col_buffer = line[len(COL):]
        elif col_buffer is not None:
            if line == '\n':
                col_buffer += line
            else:
                assert line.startswith(INDENT), line
                col_buffer += line[len(INDENT):]
        else:
            raise AssertionError(line)

    _maybe_end_col()
    _maybe_end_row()
    output.append('</tbody></table>')
    return ''.join(output)


class Renderer(markdown_code_blocks.CodeRenderer):
    def header(self, text: str, level: int, raw: str) -> str:
        match = ID_RE.search(raw)
        if match:
            h_id = match.group(1)
        else:
            h_id = SPECIAL_CHARS_RE.sub('', raw.lower()).replace(' ', '-')
        return (
            f'<h{level} id="{h_id}">'
            f'    {text} <small><a href="#{h_id}">¶</a></small>'
            f'</h{level}> '
        )

    def block_code(self, code: str, lang: str) -> str:
        if lang == 'table':
            return _render_table(code)
        else:
            return super().block_code(code, lang)


def md(s: str) -> str:
    html = markdown_code_blocks.highlight(s, Renderer=Renderer)
    # manually bless the highlighted output.
    return markupsafe.Markup(html)
