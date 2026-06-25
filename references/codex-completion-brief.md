# Codex Completion Brief

## Target architecture

```text
src/agentic_rag/
+-- contracts.py       # Stable dataclasses and Protocols
+-- orchestrator.py    # Agentic loop
+-- adapters/
|   +-- llm.py         # TODO-CODEX: provider client + structured output
|   +-- retriever.py   # TODO-CODEX: vector/BM25/SQL retriever adapters
|   +-- google_vertex_rag.py  # TODO-CODEX: native Google Cross-Corpus Retrieval mode
+-- evaluation.py      # TODO-CODEX: multi-hop/cross-corpus eval harness
```

## TODO-CODEX order

1. **Contracts**
   - Review `contracts.py`.
   - Add fields only if required for the selected backend.
   - Current scaffold includes claim citations, missing-fact feedback queries, iteration traces, and `sufficiency_score`.

2. **In-memory deterministic backend**
   - Implement a local fake retriever and fake LLM for tests.
   - This proves loop semantics without network calls.
   - Current scaffold provides dependency-free deterministic components in `src/agentic_rag/adapters/in_memory.py`.

3. **Orchestrator loop**
   - Maintain iteration state.
   - Merge snippets across iterations.
   - Stop on sufficient/unanswerable/max iterations.
   - Return partial answer if insufficient after budget.
   - Current scaffold enforces this portable loop in `src/agentic_rag/orchestrator.py`.

4. **LLM structured outputs**
   - Convert prompts in `prompts-and-schemas.md` to provider-specific schemas.
   - Validate outputs before using them.
   - Retry malformed JSON once with a repair instruction.

5. **Retriever adapters**
   - Add at least one real adapter.
   - Preserve snippet provenance.
   - Include corpus id and document id for every hit.

6. **Sufficient Context Judge**
   - It must inspect original question, plan, snippets, and draft.
   - It must return missing facts and feedback queries when insufficient.

7. **Native Google mode**
   - If using Gemini Enterprise Agent Platform RAG Engine, add an adapter that calls Cross-Corpus Retrieval APIs.
   - Respect location, IAM, project, and corpus-resource requirements.

8. **Evaluation**
   - Add a tiny multi-hop fixture with at least two corpora and one distractor corpus.
   - Verify that routing does not search all corpora unless justified.
   - Verify that one missing fact triggers a targeted follow-up query.

## Acceptance tests to add

- Query requiring two facts in two corpora succeeds after two retrieval iterations.
- Query with no available evidence returns `partial` or `unanswerable` and lists missing facts.
- Draft with an unsupported claim fails sufficiency.
- Conflicting snippets are surfaced rather than silently merged.
- All final claims have snippet ids.
