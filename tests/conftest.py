"""
conftest.py — stubs crewai and other heavy deps so financial logic
can be tested without installing the full agent framework.
"""

import sys
import types
import logging
from unittest.mock import MagicMock


class _AutoMock(types.ModuleType):
    """Module stub that returns MagicMock for any attribute access."""
    def __getattr__(self, name):
        mock = MagicMock()
        setattr(self, name, mock)
        return mock


def _make_base_tool():
    from pydantic import BaseModel

    class BaseTool(BaseModel):
        name: str = ""
        description: str = ""
        args_schema: type = type(None)

        model_config = {"arbitrary_types_allowed": True}

        def _run(self, *args, **kwargs):
            raise NotImplementedError

        def run(self, *args, **kwargs):
            return self._run(*args, **kwargs)

    return BaseTool


def _install_crewai_stub():
    BaseTool = _make_base_tool()

    tools_mod = types.ModuleType("crewai.tools")
    tools_mod.BaseTool = BaseTool
    tools_mod.tool = lambda f: f

    crewai_mod = types.ModuleType("crewai")
    crewai_mod.Agent = MagicMock()
    crewai_mod.Crew = MagicMock()
    crewai_mod.Task = MagicMock()
    crewai_mod.tools = tools_mod

    crewai_tools_mod = types.ModuleType("crewai_tools")
    crewai_tools_mod.tool = lambda f: f

    sys.modules["crewai"] = crewai_mod
    sys.modules["crewai.tools"] = tools_mod
    sys.modules["crewai_tools"] = crewai_tools_mod


def _install_optional_stubs():
    optional = [
        "chromadb",
        "pdfplumber",
        "camelot",
        "sentence_transformers",
        "plotly",
        "plotly.graph_objects",
        "plotly.io",
        "kaleido",
        "pptx",
        "pptx.util",
        "pptx.dml",
        "pptx.dml.color",
        "pptx.enum",
        "pptx.enum.text",
        "reportlab",
        "reportlab.lib",
        "reportlab.lib.pagesizes",
        "reportlab.lib.styles",
        "reportlab.lib.units",
        "reportlab.lib.colors",
        "reportlab.lib.enums",
        "reportlab.platypus",
        "weasyprint",
    ]
    for mod_name in optional:
        if mod_name not in sys.modules:
            sys.modules[mod_name] = _AutoMock(mod_name)

    # loguru: provide a real stdlib logger so log calls don't error
    loguru_mod = types.ModuleType("loguru")
    loguru_mod.logger = logging.getLogger("ib_agents_test")
    sys.modules.setdefault("loguru", loguru_mod)


_install_crewai_stub()
_install_optional_stubs()
