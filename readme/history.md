2026-09-10--20:04:42

+ initial release.

Key Fixes and Improvements:
Issue	Fix
+ Caret placement after insertion	insert_block() now returns block_start_index, so the caret is placed on the first TOC line instead of the blank separator line.
+ Missing i18n	All user-facing strings are wrapped with _() using get_translation(__file__).
+ Bilingual comments	Every comment and docstring is provided in both English and Russian.
+ .pot and .po files	Created messages.pot (template) and lang/ru_RU.po (Russian translation).

Key Refactoring Notes:
+ Helper _update_existing_toc(lines, toc_start, toc_end, toc_lines) — handles the "replace in place" branch, returns (new_lines, caret_line).
+ Helper _insert_new_toc(lines, toc_lines) — handles the "insert near caret" branch, returns (new_lines, caret_line) or (None, None) when there is no caret.
+ Functionality is unchanged — behavior of TOC parsing, anchor generation, marker detection, and line-ending preservation is identical.
