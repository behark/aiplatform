
"""
LLM factory utilities.

Provides a single place to construct local llama.cpp-backed models with
consistent defaults across the codebase.
"""
from __future__ import annotations

from typing import Optional, Sequence, Union

# Callback typing kept lightweight to avoid importing heavy managers;
# langchain callback handlers typically subclass BaseCallbackHandler
try:  # Optional import for type hints only
    from langchain_core.callbacks.base import \
        BaseCallbackHandler  # type: ignore
except Exception:  # pragma: no cover - types only
    class BaseCallbackHandler:  # type: ignore
        ...

try:
    from langchain_community.llms import LlamaCpp
except Exception as e:  # pragma: no cover
    LlamaCpp = None  # type: ignore
    _LLAMACPP_IMPORT_ERROR = e
else:
    _LLAMACPP_IMPORT_ERROR = None


def create_llama_cpp(
    *,
    model_path: str,
    model_n_ctx: int,
    callbacks: Optional[Union[BaseCallbackHandler, Sequence[BaseCallbackHandler]]] = None,
    verbose: bool = False,
    n_threads: int = 16,
    **kwargs,
):
    """
    Create a llama.cpp-backed LLM with the required defaults.

    Required defaults enforced:
    - model_path=model_path
    - n_ctx=model_n_ctx
    - callbacks=callbacks
    - verbose=False (unless explicitly overridden)
    - n_threads=16 (unless explicitly overridden)

    Additional keyword arguments are passed through to LlamaCpp.
    """
    if LlamaCpp is None:  # pragma: no cover
        raise ImportError(
            "langchain-community LlamaCpp is not available. Install with: "
            "pip install langchain-community llama-cpp-python"
        ) from _LLAMACPP_IMPORT_ERROR

    # Normalize callbacks to a list if a single handler is provided
    if callbacks is not None and not isinstance(callbacks, (list, tuple)):
        callbacks = [callbacks]

    params = {
        "model_path": model_path,
        "n_ctx": model_n_ctx,
        "callbacks": callbacks,
        "verbose": verbose,
        "n_threads": n_threads,
    }
    params.update(kwargs)
    return LlamaCpp(**params)  # type: ignore[misc]
