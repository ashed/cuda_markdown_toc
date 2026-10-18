2026-09-10--20:23:48

Line 32 Col 1: W0611: Unused import sys
Line 82 Col 12: C0209: Formatting a regular string which could be an f-string
Line 267 Col 13: C0209: Formatting a regular string which could be an f-string
Line 278 Col 21: C0209: Formatting a regular string which could be an f-string
Line 292 Col 17: C0209: Formatting a regular string which could be an f-string
Line 312 Col 17: C0209: Formatting a regular string which could be an f-string
Line 319 Col 13: C0209: Formatting a regular string which could be an f-string
Line 372 Col 18: C0209: Formatting a regular string which could be an f-string
Line 407 Col 13: C0209: Formatting a regular string which could be an f-string
Line 555 Col 13: C0209: Formatting a regular string which could be an f-string
Line 561 Col 13: C0209: Formatting a regular string which could be an f-string
Line 587 Col 13: C0209: Formatting a regular string which could be an f-string
Line 600 Col 13: C0209: Formatting a regular string which could be an f-string
Line 629 Col 13: C0209: Formatting a regular string which could be an f-string
Line 636 Col 5: R0914: Too many local variables (18/15)
Line 658 Col 17: C0209: Formatting a regular string which could be an f-string
Line 677 Col 17: C0209: Formatting a regular string which could be an f-string
Line 688 Col 19: W0612: Unused variable 'x2'
Line 688 Col 23: W0612: Unused variable 'y2'
Line 691 Col 17: C0209: Formatting a regular string which could be an f-string
Line 705 Col 17: C0209: Formatting a regular string which could be an f-string
Line 761 Col 13: C0209: Formatting a regular string which could be an f-string

---

Key Refactoring Notes

+ Helper _update_existing_toc(lines, toc_start, toc_end, toc_lines) — handles the "replace in place" branch, returns (new_lines, caret_line).

+ Helper _insert_new_toc(lines, toc_lines) — handles the "insert near caret" branch, returns (new_lines, caret_line) or (None, None) when there is no caret.

+ Functionality is unchanged — behavior of TOC parsing, anchor generation, marker detection, and line-ending preservation is identical.
