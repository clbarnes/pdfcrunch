# pdfcrunch

Yet another wrapper around PyPDF2 for simple, composable operations.

pdfcrunch attempts to sidestep some of PyPDF2's undefined behaviour around re-using readers and pages by writing intermediate products to temporary files.
Therefore, you can chain operations like

```python
from pdfcruncher import Cruncher

with Cruncher("my_document.pdf") as original:
    afterword = original[-5:]
    shrink = afterword.crop_to(xmax=500, ymin=800).scale_by(0.5)
    rotate = afterword.crop_to(xmin=500, ymax=800).rotate90cw(3)
    final = afterword.join(shrink, rotate)
    final.write("output.pdf")
```

Developed using [poetry](https://python-poetry.org/).
