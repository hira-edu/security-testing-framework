"""Wrapper module exposing the injector helpers from bypass-methods."""

from importlib import import_module
from typing import Any

__all__ = ["get_injector_module"]


def get_injector_module() -> Any:
    """Return the upstream injector module."""
    return import_module('src.external.bypass_methods.tools.injector')
