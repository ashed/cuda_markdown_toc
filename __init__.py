"""
Markdown Table of Contents plugin for CudaText.
Плагин оглавления Markdown для CudaText.

Managed TOC format / Формат Оглавления:

<!-- MarkdownTOC -->
- [Introduction](#introduction)
  - [Installation](#installation)
<!-- /MarkdownTOC -->

Commands / Команды:

    run()
        Insert a TOC or update an existing TOC.
        Вставить Оглавление или Обновить существующее Оглавление.

    update()
        Update an existing TOC only.
        Обновить существующее Оглавление.

    insert_toc()
        Alias for run().
        Псевдоним run().

    insert_or_update_toc()
        Alias for run().
        Псевдоним run().
"""

import re
import unicodedata
from urllib.parse import quote

from cudatext import (
    ed,
    msg_box,
    msg_status,
    app_log,
    LOG_ADD,
    MB_OK,
    MB_ICONERROR,
)

from cudax_lib import get_translation


_ = get_translation(__file__)


# ----------------------------------------------------------------------
# Module initialization / Инициализация модуля
# ----------------------------------------------------------------------

DEBUG = False

TOC_START = "<!-- MarkdownTOC -->"
TOC_END = "<!-- /MarkdownTOC -->"


app_log(LOG_ADD, "[MarkdownTOC] module loaded")


# ----------------------------------------------------------------------
# Debugging helpers / Вспомогательные функции отладки
# ----------------------------------------------------------------------

def debug(message):
    """
    Write a diagnostic message to the CudaText Output panel.
    Записать диагностическое сообщение в панель вывода CudaText.

    The message is also printed to stdout, which is useful when CudaText
    is started from a terminal.
    Сообщение также выводится в stdout, что полезно при запуске CudaText
    из терминала.
    """
    if not DEBUG:
        return

    text = f"[MarkdownTOC] {message}"

    # CudaText Output panel.
    # Панель вывода CudaText.
    app_log(LOG_ADD, text)

    # Terminal output.
    # Вывод в терминал.
    print(text)


# ----------------------------------------------------------------------
# Markdown parsing helpers / Вспомогательные функции разбора Markdown
# ----------------------------------------------------------------------

# Matches ATX headings / Соответствует заголовкам ATX:

#     # Heading
#     ## Heading
#     ### Heading ###
#
# Up to three leading spaces are allowed.
# Допускается до трёх ведущих пробелов.
ATX_HEADING_RE = re.compile(
    r"^ {0,3}(?P<marks>#{1,6})[ \t]+(?P<title>.+?)[ \t]*$"
)


# Matches fenced code blocks beginning with ``` or ~~~.
# Соответствует блокам кода, начинающимся с ``` или ~~~.
FENCE_RE = re.compile(
    r"^ {0,3}(?P<fence>`{3,}|~{3,})"
)


# Removes prefixes produced by an indexed heading plugin:
# Удаляет префиксы, созданные плагином индексированных заголовков:
#     1. Introduction
#     1.2. Installation
# NUMBER_PREFIX_RE = re.compile(
    # r"^(?:\d+\.)+[ \t]+"
# )


def line_ending(text):
    """
    Return the line-ending sequence used by the document.
    Вернуть последовательность окончания строк, используемую в документе.
    """
    if "\r\n" in text:
        return "\r\n"

    if "\r" in text:
        return "\r"

    return "\n"


def clean_heading_title(title):
    """
    Convert a Markdown heading into a clean visible TOC title.
    Преобразовать заголовок Markdown в чистый видимый заголовок Оглавления.

    Examples / Примеры:

        '1. Introduction'          -> 'Introduction'
        'Install [CudaText](url)'  -> 'Install CudaText'
        'Title ###'                -> 'Title'
    """
    # Remove optional closing ATX markers.
    # Удалить необязательные закрывающие маркеры ATX.
    title = re.sub(
        r"[ \t]+#+[ \t]*$",
        "",
        title,
    )

    # Remove an optional numeric prefix.
    # Удалить необязательный числовой префикс.
    # title = NUMBER_PREFIX_RE.sub(
        # "",
        # title,
        # count=1,
    # )

    # Convert Markdown images to their alt text.
    # Преобразовать изображения Markdown в их альтернативный текст.
    title = re.sub(
        r"!\[([^\]]*)\]\([^)]*\)",
        r"\1",
        title,
    )

    # Convert Markdown links to their visible text.
    # Преобразовать ссылки Markdown в их видимый текст.
    title = re.sub(
        r"\[([^\]]+)\]\([^)]*\)",
        r"\1",
        title,
    )

    # Convert reference-style links.
    # Преобразовать ссылки ссылочного стиля.
    title = re.sub(
        r"\[([^\]]+)\]\[[^\]]*\]",
        r"\1",
        title,
    )

    # Remove inline-code markers.
    # Удалить маркеры встроенного кода.
    title = title.replace("`", "")

    # Remove simple HTML tags.
    # Удалить простые HTML-теги.
    title = re.sub(
        r"<[^>]+>",
        "",
        title,
    )

    # Collapse whitespace.
    # Свернуть пробелы.
    title = re.sub(
        r"\s+",
        " ",
        title,
    ).strip()

    return title


def is_fence_start(line):
    """
    Return the fence marker if the line starts a fenced code block.
    Вернуть маркер ограждения, если строка начинает блок кода.
    """
    match = FENCE_RE.match(line)

    if not match:
        return None

    return match.group("fence")


def is_fence_end(line, fence):
    """
    Return True when line closes the active fenced code block.
    Вернуть True, когда строка закрывает активный блок кода.
    """
    if not fence:
        return False

    marker = fence[0]
    minimum_length = len(fence)

    pattern = (
        r"^ {0,3}"
        + re.escape(marker)
        + r"{"
        + str(minimum_length)
        + r",}[ \t]*$"
    )

    return bool(re.match(pattern, line))


def find_headings(lines):
    """
    Find Markdown headings outside fenced code blocks.
    Найти заголовки Markdown вне блоков кода.

    Returns / Возвращает:

        [
            (heading_level, heading_title),
            ...
        ]
    """
    headings = []
    fence = None

    for line_number, line in enumerate(lines):
        debug(f"Scanning line {line_number}: {line!r}")

        # Ignore everything inside a fenced code block.
        # Игнорировать всё внутри блока кода.
        if fence:
            if is_fence_end(line, fence):
                debug(f"Fence closed at line {line_number}")
                fence = None

            continue

        # Detect the beginning of a fenced code block.
        # Обнаружить начало блока кода.
        new_fence = is_fence_start(line)

        if new_fence:
            debug(
                f"Fence opened at line {line_number}: {new_fence!r}"
            )
            fence = new_fence
            continue

        match = ATX_HEADING_RE.match(line)

        if not match:
            continue

        level = len(match.group("marks"))
        title = clean_heading_title(match.group("title"))

        # Do not include empty headings.
        # Не включать пустые заголовки.
        if not title:
            debug(f"Ignoring empty heading at line {line_number}")
            continue

        debug(f"Heading found: level={level}, title={title!r}")

        headings.append((level, title))

    return headings


def make_anchor(title, used_anchors):
    """
    Create a GitHub-like anchor.
    Создать якорь в GitHub-формате.

    Duplicate headings receive a numeric suffix:
    Дублирующиеся заголовки получают числовой суффикс:

        # Configuration -> #configuration
        # Configuration -> #configuration-1
    """
    normalized = unicodedata.normalize(
        "NFKD",
        title,
    )

    # Convert accented characters to ASCII where possible.
    # Преобразовать акцентированные символы в ASCII, если возможно.
    normalized = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    anchor = normalized.lower()

    # Replace punctuation and whitespace with hyphens.
    # Заменить пунктуацию и пробелы на дефисы.
    anchor = re.sub(
        r"[^a-z0-9]+",
        "-",
        anchor,
    )

    anchor = anchor.strip("-")

    if not anchor:
        anchor = "section"

    original_anchor = anchor
    suffix = 1

    while anchor in used_anchors:
        anchor = f"{original_anchor}-{suffix}"
        suffix += 1

    used_anchors.add(anchor)

    # quote() keeps the generated link safe if the anchor is later
    # extended to support non-ASCII characters.
    # quote() сохраняет сгенерированную ссылку безопасной, если якорь
    # позже будет расширен для поддержки не-ASCII символов.
    return quote(
        anchor,
        safe="-",
    )


def build_toc(headings):
    """
    Build the complete managed TOC block.
    Построить полный управляемый блок Оглавления.
    """
    result = [TOC_START]
    used_anchors = set()

    for level, title in headings:
        anchor = make_anchor(
            title,
            used_anchors,
        )

        indentation = "  " * (level - 1)

        result.append(f"{indentation}- [{title}](#{anchor})")

    result.append(TOC_END)

    return result


def find_toc(lines):
    """
    Find the first complete managed TOC block.
    Найти первый полный управляемый блок Оглавления.

    Returns / Вернуть:

        (start_line, end_line)

    or / или:

        (None, None)
    """
    try:
        start = lines.index(TOC_START)
    except ValueError:
        return None, None

    try:
        end = lines.index(
            TOC_END,
            start + 1,
        )
    except ValueError:
        # Do not overwrite a broken or incomplete TOC.
        # Не перезаписывать сломанное или неполное Оглавление.
        debug("TOC start marker found without end marker")
        return None, None

    return start, end


def preserve_document_newline(text, lines, had_final_newline):
    """
    Rebuild document text using its original line-ending style.
    Перестроить текст документа, используя исходный стиль окончания строк.
    """
    newline = line_ending(text)
    new_text = newline.join(lines)

    if had_final_newline:
        new_text += newline

    return new_text


def insert_block(lines, position, block):
    """
    Insert a TOC before the specified line.
    Вставить Оглавление перед указанной строкой.

    Blank lines are added around the block when necessary.
    Добавить вокруг блока пустые строки при необходимости.

    Returns / Вернуть:

        (new_lines, block_start_index)
    """
    before = list(lines[:position])
    after = list(lines[position:])

    if before and before[-1].strip():
        before.append("")

    block_start_index = len(before)

    before.extend(block)

    if after and after[0].strip():
        before.append("")

    before.extend(after)

    return before, block_start_index


# ----------------------------------------------------------------------
# CudaText plugin commands / Команды плагина CudaText
# ----------------------------------------------------------------------

class Command:
    """
    CudaText commands for Markdown TOC generation.
    Команды CudaText для генерации Оглавления Markdown.
    """

    @staticmethod
    def debug(message):
        """
        Write a diagnostic message through the module debug function.
        Записать диагностическое сообщение через модульную функцию debug.
        """
        debug(message)

    @staticmethod
    def show_info(message):
        """
        Display an informational message.
        Показать информационное сообщение.
        """
        msg_box(
            message,
            MB_OK,
        )

    @staticmethod
    def show_error(message):
        """
        Display an error message.
        Показать сообщение об ошибке.
        """
        msg_box(
            message,
            MB_OK | MB_ICONERROR,
        )

    def _read_document(self):
        """
        Read the active document.
        Прочитать активный документ.

        Returns / Возвращает:

            text,
            lines,
            had_final_newline
        """
        text = ed.get_text_all()

        had_final_newline = text.endswith(
            ("\n", "\r")
        )

        lines = text.splitlines()

        self.debug(f"Document length: {len(text)}")
        self.debug(f"Document line count: {len(lines)}")

        return (
            text,
            lines,
            had_final_newline,
        )

    def _generate_toc(self):
        """
        Parse the document and create a TOC block.
        Разобрать документ и создать блок Оглавления.
        """
        text, lines, had_final_newline = self._read_document()

        if not text.strip():
            self.debug("Document is empty")
            self.show_info(_("Document is empty"))
            return None

        headings = find_headings(lines)

        self.debug(f"Heading count: {len(headings)}")

        if not headings:
            self.debug("No Markdown headings found")
            self.show_info(_("No Markdown headings found"))
            return None

        toc_lines = build_toc(headings)

        self.debug(f"Generated TOC line count: {len(toc_lines)}")

        return (
            text,
            lines,
            had_final_newline,
            toc_lines,
        )

    def _write_document(
        self,
        text,
        lines,
        had_final_newline,
    ):
        """
        Write the modified document back to CudaText.
        Записать изменённый документ обратно в CudaText.
        """
        new_text = preserve_document_newline(
            text,
            lines,
            had_final_newline,
        )

        self.debug(f"New document length: {len(new_text)}")

        ed.set_text_all(new_text)

    def _update_existing_toc(self, lines, toc_start, toc_end, toc_lines):
        """
        Replace the existing managed TOC block in place.
        Заменить существующий управляемый блок Оглавления на месте.

        Returns / Возвращает:

            (new_lines, caret_line)
        """
        self.debug(
            f"Updating existing TOC: lines {toc_start}-{toc_end}"
        )

        new_lines = (
            lines[:toc_start]
            + toc_lines
            + lines[toc_end + 1:]
        )

        return new_lines, toc_start

    def _insert_new_toc(self, lines, toc_lines):
        """
        Insert a fresh TOC block near the caret.
        Вставить новый блок Оглавления рядом с кареткой.

        Returns / Возвращает:

            (new_lines, caret_line) or (None, None) on failure.
            (new_lines, caret_line) или (None, None) при ошибке.
        """
        carets = ed.get_carets()

        self.debug(f"Caret count: {len(carets)}")

        if not carets:
            self.show_error(
                _("Could not determine the caret position")
            )
            return None, None

        # Only the caret's line index is needed.
        # Нужен только индекс строки каретки.
        caret_y = carets[0][1]

        self.debug(f"Caret line: y={caret_y}")

        # Keep the insertion line within the document.
        # Удерживать строку вставки в пределах документа.
        position = max(
            0,
            min(caret_y, len(lines)),
        )

        self.debug(f"Inserting TOC before line {position}")

        new_lines, block_start = insert_block(
            lines,
            position,
            toc_lines,
        )

        return new_lines, block_start

    def run(self):
        """
        Insert a TOC or update an existing TOC.
        Вставить Оглавление или Обновить существующее Оглавление.

        If a managed TOC exists, it is replaced in place.
        Если управляемое Оглавление существует, оно заменяется на месте.
        Otherwise, the TOC is inserted before the current caret line.
        В противном случае Оглавление вставляется перед текущей строкой каретки.
        """
        self.debug("run() entered")

        generated = self._generate_toc()

        if generated is None:
            return

        text, lines, had_final_newline, toc_lines = generated
        toc_start, toc_end = find_toc(lines)

        if toc_start is not None:
            new_lines, caret_line = self._update_existing_toc(
                lines,
                toc_start,
                toc_end,
                toc_lines,
            )
            status_text = _("Markdown TOC updated")
        else:
            new_lines, caret_line = self._insert_new_toc(
                lines,
                toc_lines,
            )

            if new_lines is None:
                return

            status_text = _("Markdown TOC inserted")

        self._write_document(
            text,
            new_lines,
            had_final_newline,
        )

        # Move the caret to the TOC start.
        # Переместить каретку в начало Оглавления.
        ed.set_caret(
            0,
            caret_line,
        )

        self.debug(status_text)
        msg_status(status_text)

    def update(self):
        """
        Update an existing TOC only.
        Обновить только существующее Оглавление.

        No TOC is inserted when the marker block is absent.
        Оглавление не вставляется, если блок маркеров отсутствует.
        """
        self.debug("update() entered")

        generated = self._generate_toc()

        if generated is None:
            return

        text, lines, had_final_newline, toc_lines = generated
        toc_start, toc_end = find_toc(lines)

        if toc_start is None:
            self.debug("No complete managed TOC found")
            self.show_info(
                _("Managed Markdown TOC markers were not found")
            )
            return

        self.debug(f"Replacing TOC lines {toc_start}-{toc_end}")

        new_lines = (
            lines[:toc_start]
            + toc_lines
            + lines[toc_end + 1:]
        )

        self._write_document(
            text,
            new_lines,
            had_final_newline,
        )

        ed.set_caret(
            0,
            toc_start,
        )

        msg_status(_("Markdown TOC updated"))

    def insert_toc(self):
        """
        Alias for run().
        Псевдоним run().
        """
        self.run()

    def insert_or_update_toc(self):
        """
        Alias for run().
        Псевдоним run().
        """
        self.run()
