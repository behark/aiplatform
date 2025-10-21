# LLM Config Audit (Aug 22, 2025)

This repo was scanned for local LLM initializations where the following llama.cpp-style configuration would apply:

- model_path=model_path
- n_ctx=model_n_ctx
- callbacks=callbacks
- verbose=False
- n_threads=16

## Findings

- No direct uses of llama.cpp-based models found:
  - No occurrences of LlamaCpp, llama_cpp, ctransformers, or GPT4All initializations in the project sources.
- Current LLM usage:
  - OpenAI-compatible client via `data/external.py` (OpenAI API; parameters like `n_ctx`/`n_threads` do not apply).
  - Configuration and references for Ollama are present (via env vars and deployment manifests), but usage is over HTTP (Chat/Ollama connectors) rather than direct llama.cpp bindings.
  - Example `ChatOpenAI()` appears only in a docstring example (`src/retrieval.py`) and is not an actual runtime init.

## Conclusion

- There are no LlamaCpp (llama.cpp) inits to update, so no code changes were needed.
- If you plan to add a llama.cpp-backed LLM, use this exact configuration:

```python
from langchain_community.llms import LlamaCpp

llm = LlamaCpp(
    model_path=model_path,
    n_ctx=model_n_ctx,
    callbacks=callbacks,
    verbose=False,
    n_threads=16,
)
```

Optionally, centralize LLM creation to ensure these flags are always applied when llama.cpp is used.
Alternatively, you can now import the included factory helper to standardize this across the codebase:

```python
from src.llm_factory import create_llama_cpp

llm = create_llama_cpp(
  model_path=model_path,
  model_n_ctx=model_n_ctx,
  callbacks=callbacks,
)
```

## Notes

- Ollama models are managed via HTTP (see OLLAMA_BASE_URL in docker compose and k8s manifests). Threads/ctx are configured in Ollama server/model settings, not here.
- Embedding and reranking models use `sentence_transformers` and do not accept llama.cpp params.

## Pointers

- OpenAI client init: `data/external.py`
- Retrieval utilities and docstring: `src/retrieval.py`
- Ollama env wiring: `docker-compose.*.yml`, `deployment/webui-deployment.yaml`, `Dockerfile.railway.*`
