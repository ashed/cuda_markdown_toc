Key Fixes and Improvements
Issue	Fix
Caret placement after insertion	insert_block() now returns block_start_index, so the caret is placed on the first TOC line instead of the blank separator line.
Missing i18n	All user-facing strings are wrapped with _() using get_translation(__file__).
Bilingual comments	Every comment and docstring is provided in both English and Russian.
.pot and .po files	Created messages.pot (template) and lang/ru_RU.po (Russian translation).
