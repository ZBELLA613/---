from __future__ import annotations

import jinja2
import jinja2.ext
from markupsafe import Markup, escape


def patch_flask_jinja_compat() -> None:
    if not hasattr(jinja2, "escape"):
        jinja2.escape = escape
    if not hasattr(jinja2, "Markup"):
        jinja2.Markup = Markup
    if not hasattr(jinja2.ext, "autoescape"):
        class _AutoEscapeCompatExtension(jinja2.ext.Extension):
            pass

        jinja2.ext.autoescape = _AutoEscapeCompatExtension
    if not hasattr(jinja2.ext, "with_"):
        class _WithCompatExtension(jinja2.ext.Extension):
            pass

        jinja2.ext.with_ = _WithCompatExtension
