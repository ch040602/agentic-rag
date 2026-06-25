# Source Map

Use these public sources to verify facts before completing the implementation.

## Google Research announcement

URL: https://research.google/blog/unlocking-dependable-responses-with-gemini-enterprise-agent-platforms-agentic-rag/

Key public facts to preserve:

- Published 2026-06-05.
- Describes a Google Research + Google Cloud Agentic RAG framework for Gemini Enterprise Agent Platform.
- Publicly describes a multi-agent workflow that breaks down complex enterprise queries and iteratively searches for sufficient context.
- Publicly listed roles include Orchestrator, Planner Agent, Query Rewriter, Search Fanout/RAG Agent, Sufficient Context Agent, and Synthesis/LLM aggregation.
- Core differentiator is persistence through Sufficient Context checking: the system identifies missing pieces and re-searches instead of stopping after first retrieval.
- Reported public results include up to 34% accuracy improvement versus standard RAG on factuality datasets and 90.1% accuracy in the described cross-corpus FramesQA setting.

## Google Cloud Cross Corpus Retrieval docs

URL: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/rag-engine/cross-corpus-retrieval

Key public facts to preserve:

- Feature is RAG Engine Cross Corpus Retrieval.
- Docs describe `AsyncRetrieveContexts` and `AskContexts` APIs.
- Docs state the system uses an agentic approach across multiple corpora.
- Architecture components include Orchestrator/Router, Planning Agent, Retrieval Engine, Reasoning Agent, and LLM Generator.
- Corpus `description` is important for corpus selection.
- Public docs state the feature is available only in `us-central1` at the time of the referenced page.
- Requires granting Vertex AI User role to the RAG Engine service account.

## Agent Skills specification

URL: https://agentskills.io/specification

Key public facts to preserve:

- A skill is a folder containing at minimum `SKILL.md`.
- `SKILL.md` requires YAML frontmatter with `name` and `description`.
- Optional directories include `scripts/`, `references/`, and `assets/`.
- Skills should use progressive disclosure: keep `SKILL.md` focused and load reference files on demand.

## Codex Skills docs

URL: https://developers.openai.com/codex/skills

Key public facts to preserve:

- Codex supports Agent Skills with `SKILL.md`, optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`.
- Codex scans `.agents/skills` in the current directory and parent directories up to the repo root for repo-scoped skills.
- Codex can invoke skills explicitly or implicitly based on the description.
