
check the imports

python3 -c "
import sys
sys.path.insert(0, '$HOME/.config/cudatext/py')
import cuda_markdown_toc
print('plugin import OK')
"

---

compile plugin

python3 -m py_compile ~/.config/cudatext/py/cuda_markdown_toc/cuda_markdown_toc.py

