# Source Map

Use these public sources to verify facts before completing the implementation. This file maps research and product sources to the behavior implemented in this repository.

## Implementation alignment

The current scaffold implements the portable subset of the public Agentic RAG pattern:

- Corpus descriptions are treated as routing metadata.
- Retrieval plans decompose a question into required facts and routes.
- Subqueries preserve fact and iteration lineage.
- Snippets preserve corpus id, document id, score, metadata, and query lineage.
- Sufficiency assessment returns status, `sufficiency_score`, covered facts, missing facts, unsupported claims, and feedback queries.
- The orchestrator stops on sufficient, irrelevant, unanswerable, max iteration, or no-subquery states.
- Final answers are downgraded when sufficiency fails or citations reference snippets that were not retrieved.

## Google Research announcement

URL: https://research.google/blog/unlocking-dependable-responses-with-gemini-enterprise-agent-platforms-agentic-rag/

Key public facts to preserve:

- Published 2026-06-05.
- Describes a Google Research + Google Cloud Agentic RAG framework for Gemini Enterprise Agent Platform.
- Publicly describes a multi-agent workflow that breaks down complex enterprise queries and iteratively searches for sufficient context.
- Publicly listed roles include Orchestrator, Planner Agent, Query Rewriter, Search Fanout/RAG Agent, Sufficient Context Agent, and Synthesis/LLM aggregation.
- Core differentiator is persistence through Sufficient Context checking: the system identifies missing pieces and re-searches instead of stopping after first retrieval.
- Reported public results include up to 34% accuracy improvement versus standard RAG on factuality datasets and 90.1% accuracy in the described cross-corpus FramesQA setting.

Implementation relevance:

- Motivates the multi-agent loop: orchestrator, planner, query rewriter, search fanout, sufficient context agent, and synthesizer.
- Motivates missing-fact feedback and iterative follow-up retrieval.
- Connects Agentic RAG evaluation to FramesQA/FRAMES and cross-corpus routing.

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

Implementation relevance:

- Motivates provider adapters rather than embedding product-specific calls in the orchestrator.
- Motivates high-quality corpus descriptions for cross-corpus routing.
- Remains planned follow-up work for native Google mode.

## Referenced papers

### Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

URL: https://arxiv.org/abs/2005.11401

Key public facts to preserve:

- Introduces the RAG framing that combines parametric generation with non-parametric retrieved memory.
- Establishes the retrieve-then-generate baseline that this project extends with planning, sufficiency checks, iteration, and claim-level provenance.

Implementation relevance:

- Provides the baseline terminology for RAG and retrieved evidence.
- Motivates explicit provenance and updateable external knowledge.

### Sufficient Context: A New Lens on Retrieval Augmented Generation Systems

URL: https://arxiv.org/abs/2411.06037

Key public facts to preserve:

- Defines sufficient context as context that contains enough information to provide a definitive answer.
- Studies a sufficient-context autorater and shows that relevance alone is not enough to decide answerability.
- Motivates using sufficiency signals to reduce hallucinations and guide abstention.

Implementation relevance:

- Directly motivates `ContextAssessment`, `sufficiency_score`, `missing_facts`, `unsupported_claims`, and partial/unanswerable answers.
- Supports the guardrail that a final answer should not be marked answered when context is insufficient.

### Fact, Fetch, and Reason: A Unified Evaluation of Retrieval-Augmented Generation

URL: https://arxiv.org/abs/2409.12941

Key public facts to preserve:

- Introduces FRAMES, a multi-hop RAG evaluation benchmark for factuality, retrieval, and reasoning.
- Evaluates questions that require retrieving and combining facts from multiple sources.

Implementation relevance:

- Motivates future evaluation fixtures for multi-hop and cross-corpus RAG.
- Provides the research basis for FramesQA-style tests mentioned in the Google Research Agentic RAG announcement.

## Agent Skills specification

URL: https://agentskills.io/specification

Key public facts to preserve:

- A skill is a folder containing at minimum `SKILL.md`.
- `SKILL.md` requires YAML frontmatter with `name` and `description`.
- Optional directories include `scripts/`, `references/`, and `assets/`.
- Skills should use progressive disclosure: keep `SKILL.md` focused and load reference files on demand.

Implementation relevance:

- Motivates the repository layout with `SKILL.md`, `references/`, `agents/`, `src/`, and tests.

## Codex Skills docs

URL: https://developers.openai.com/codex/skills

Key public facts to preserve:

- Codex supports Agent Skills with `SKILL.md`, optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`.
- Codex scans `.agents/skills` in the current directory and parent directories up to the repo root for repo-scoped skills.
- Codex can invoke skills explicitly or implicitly based on the description.

Implementation relevance:

- Motivates keeping `SKILL.md` concise and placing detailed guidance in `references/`.
- Motivates `agents/openai.yaml` for Codex-facing skill metadata.
