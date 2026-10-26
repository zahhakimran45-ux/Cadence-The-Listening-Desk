#!/usr/bin/env python3
"""Bundle src/ into one self-contained index.html (works even as a plain file)."""
import json, os
here = os.path.dirname(os.path.abspath(__file__))
s = lambda p: open(os.path.join(here, "src", p), encoding="utf-8").read()
tpl = open(os.path.join(here, "src", "template.html"), encoding="utf-8").read()
catalog = open(os.path.join(here, "src", "catalog.json"), encoding="utf-8").read()
catalog = catalog.replace("<", "\\u003c").replace("&", "\\u0026")
out = (tpl.replace("__STYLES__", s("styles.css"))
          .replace("__CATALOG__", catalog)
          .replace("__APP__", s("app.js")))
path = os.path.join(here, "index.html")
open(path, "w", encoding="utf-8").write(out)
print("built", path, os.path.getsize(path), "bytes")
