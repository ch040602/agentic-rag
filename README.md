# Agentic RAG Skill

[![CI](https://github.com/ch040602/agentic-rag/actions/workflows/tests.yml/badge.svg)](https://github.com/ch040602/agentic-rag/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Agentic RAG is a Codex-compatible Agent Skill and dependency-free Python scaffold for building RAG systems that can decide whether retrieved context is sufficient, identify missing facts, generate targeted follow-up queries, and produce claim-level citations.

The repository focuses on the product gap between ordinary "retrieve once, answer once" RAG and a more dependable loop:

```text
plan -> route -> rewrite -> retrieve -> draft -> judge sufficiency -> iterate -> synthesize
```

It is intended for enterprise document search, internal knowledge assistants, RAG application developers, and researchers who need auditable evidence coverage rather than confident answers from incomplete context.

## Contents

- [What This Skill Provides](#what-this-skill-provides)
- [Repository Layout](#repository-layout)
- [How It Works](#how-it-works)
- [Core Contracts](#core-contracts)
- [Implementation Rules](#implementation-rules)
- [Install and Use](#install-and-use)
- [Validate and Publish](#validate-and-publish)
- [Referenced Papers](#referenced-papers)
- [Sources](#sources)

## What This Skill Provides

- A Codex `SKILL.md` with activation rules and implementation guidance for Agentic RAG workflows.
- Stable Python contracts for corpus catalogs, retrieval plans, subqueries, snippets, claim citations, context assessments, feedback queries, and grounded answers.
- A portable orchestrator that runs iterative retrieval and refuses to mark unsupported answers as grounded.
- A deterministic autorater-style sufficient-context judge for offline tests and adapter baselines.
- FRAMES-style evaluation fixtures and metrics for fact, fetch, reasoning, citation, and iteration checks.
- Conflict-aware synthesis that surfaces contradictory snippets with citations for both incompatible evidence groups.
- Deterministic in-memory adapters for tests, demos, and provider-adapter contract checks.
- Reference prompts and JSON schemas for planner, query rewriter, sufficiency judge, and synthesizer components.
- Tests covering iterative retrieval, missing evidence feedback, unsupported claim detection, conflict-aware citation, citation completeness, and route-aware retrieval.

## Repository Layout

```text
.
+-- SKILL.md
+-- README.md
+-- AGENTS.md
+-- agents/
|   +-- openai.yaml
+-- references/
|   +-- agentic-rag-behavior.md
|   +-- agentic-rag-behavior-summary.md
|   +-- codex-completion-brief.md
|   +-- prompts-and-schemas.md
|   +-- source-map.md
+-- scripts/
|   +-- validate_skill.py
+-- pyproject.toml
+-- .github/workflows/tests.yml
+-- src/
|   +-- agentic_rag/
|       +-- contracts.py
|       +-- evaluation.py
|       +-- orchestrator.py
|       +-- sufficiency.py
|       +-- adapters/
|           +-- llm.py
|           +-- retriever.py
|           +-- in_memory.py
+-- tests/
    +-- test_llm_adapter.py
    +-- test_evaluation.py
    +-- test_orchestrator.py
    +-- test_retriever_adapter.py
    +-- test_skill_metadata.py
    +-- test_sufficiency.py
```

## How It Works

The scaffold separates orchestration from provider-specific implementation:

1. A `Planner` decomposes the original question into required facts and routes each fact to candidate corpora.
2. A `QueryRewriter` creates targeted subqueries for each routed fact.
3. A `Retriever` returns snippets with provenance.
4. A `Drafter` creates an intermediate answer only from retrieved snippets.
5. A `SufficientContextJudge` checks required-fact coverage, unsupported draft claims, and missing facts.
6. If context is insufficient and the iteration budget remains, the next iteration uses judge feedback queries.
7. A `Synthesizer` emits a grounded answer with claim-level citations, or returns partial/unanswerable diagnostics.

The orchestrator preserves:

- Original question
- Plan items
- Rewritten subqueries
- Retrieved snippets
- Sufficiency assessments
- Missing fact feedback queries
- Final grounded citations

## Core Contracts

Important contracts live in `src/agentic_rag/contracts.py`:

- `Corpus`: corpus id, description, and metadata used for routing.
- `RequiredFact`: a fact that must, should, or may be answered.
- `RetrievalPlan`: required facts, routes, and stop conditions.
- `Subquery`: rewritten query with target corpus ids and lineage fields.
- `Snippet`: retrieved evidence with corpus id, document id, score, metadata, and optional span.
- `ConflictEvidence`: incompatible evidence groups for one required fact, with snippet ids for each side of the conflict.
- `ContextAssessment`: sufficiency status, `sufficiency_score`, covered facts, missing facts, unsupported claims, conflict evidence, and feedback queries.
- `AnswerabilityLabel`: Sufficient Context answerability labels for sufficient, useful-but-incomplete, insufficient, conflicting, and unanswerable contexts.
- `GroundedAnswer`: answer text, claim-level citations, status, missing facts, final sufficiency score, and optional conflict evidence.
- `IterationTrace`: subqueries, snippets, draft, and assessment for each loop iteration.

`src/agentic_rag/sufficiency.py` provides `AutoraterStyleSufficiencyJudge`, a deterministic judge that verifies required-fact coverage, reports covered facts and missing facts, detects unsupported draft claims, emits targeted feedback queries, surfaces conflicting evidence groups, and assigns Sufficient Context answerability labels. It also provides `apply_selective_abstention_policy`, which maps answerability labels to final answered, partial, or unanswerable outputs before citation validation. Fact matching uses `RequiredFact.metadata["required_terms"]`; optional `conflict_terms` mark incompatible evidence.

`src/agentic_rag/evaluation.py` provides FRAMES-style fixture and report dataclasses for multi-hop RAG evaluation. It records bridge facts, expected fetches, expected answer terms, expected citations, and distractor corpora, then reports fact coverage, fetch coverage, reasoning correctness, citation completeness, and iteration count for a `RunResult`. It also compares baseline and candidate runs so single-shot and iterative retrieval strategies can be evaluated side by side.

## Implementation Rules

- Keep provider integrations behind adapters.
- Preserve corpus descriptions and use them as routing metadata.
- Preserve query lineage from original question to final citation.
- Treat sufficiency as a fact-coverage decision, not a vector-score threshold.
- Never return a fully answered result after an insufficient sufficiency check.
- Enforce iteration and cost limits in the orchestrator or adapter layer.

## Install and Use

This repository is the canonical distribution package for the `agentic-rag` skill. It contains `SKILL.md`, `references/`, `agents/` metadata, validation scripts, tests, and the optional Python scaffold in one repo.

### Codex

Install as a personal Codex skill:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/ch040602/agentic-rag.git ~/.codex/skills/agentic-rag
```

Use it in Codex CLI or IDE:

```text
$agentic-rag design a multi-hop RAG pipeline that checks sufficient context before answering
```

Codex can also activate the skill automatically when your task matches the `description` in `SKILL.md`. If the skill does not appear, restart Codex or open the skill selector with `/skills`.

For a repository-scoped install, place it under the repo:

```bash
mkdir -p .codex/skills
git clone https://github.com/ch040602/agentic-rag.git .codex/skills/agentic-rag
```

### Claude Code

Install as a personal Claude Code skill:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/ch040602/agentic-rag.git ~/.claude/skills/agentic-rag
```

Use it in Claude Code:

```text
/agentic-rag Design a RAG workflow that retries retrieval when context is insufficient.
```

Claude Code can also load the skill automatically when the request is relevant. The command name comes from the installed directory name, so keep the folder named `agentic-rag`.

For a project-scoped install, place it under the repo:

```bash
mkdir -p .claude/skills
git clone https://github.com/ch040602/agentic-rag.git .claude/skills/agentic-rag
```

### Optional Python Scaffold

The Python scaffold is dependency-free and useful for local tests or adapter development:

```bash
python -m pip install -e ~/.codex/skills/agentic-rag
python -m unittest discover -s ~/.codex/skills/agentic-rag/tests -v
```

If you installed the skill somewhere else, replace the path with that location.

### Legacy Skill Compatibility (Merged From Agentic-RAG-Skill)

This repository now includes the legacy `Agentic-RAG-Skill` compatibility surface while keeping the modern contracts. `Agentic-RAG-Skill` is no longer managed as a separate distribution repo.

- `AgenticRAGPipeline` for the legacy-style iterative `answer(...)` API.
- Compatibility adapters (`KeywordPlanner`, `TemplateQueryRewriter`, `InMemoryKeywordRetriever`, `CoverageSufficiencyJudge`, `ExtractiveSynthesizer`).
- Structured output helper layer (`structured.py`) for legacy JSON output adapters.
- `VertexRagCrossCorpusRetriever` adapter in `adapters/vertex_rag.py`.
- Root-level exports in `agentic_rag.__init__` so old import patterns keep working.

You can run a deterministic baseline demo:

```bash
python examples/in_memory_pipeline.py
```

## Validate and Publish

Before publishing a change, run both checks from the repository root:

```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -v
```

`scripts/validate_skill.py` verifies that the repo root is installable as a skill package:

- `SKILL.md` has only the runtime frontmatter fields `name` and `description`.
- Required references, agent metadata, and scaffold files exist.
- The installed directory name matches the skill name.
- `SKILL.md` stays concise and uses `references/` for detailed guidance.

The GitHub Actions workflow runs the same validation and unit tests on pushes and pull requests to `main`.

## Referenced Papers

The design is grounded in the following papers and public research artifacts:

- **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks**  
  Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim Rocktaschel, Sebastian Riedel, and Douwe Kiela. NeurIPS 2020.  
  This is the foundational RAG paper behind the general retrieve-then-generate framing used throughout this project.  
  Link: https://arxiv.org/abs/2005.11401

- **Sufficient Context: A New Lens on Retrieval Augmented Generation Systems**  
  Hailey Joren, Jianyi Zhang, Chun-Sung Ferng, Da-Cheng Juan, Ankur Taly, and Cyrus Rashtchian. ICLR 2025.  
  This paper motivates the explicit `sufficiency_score`, unsupported-claim checks, and missing-fact feedback queries in the scaffold.  
  Link: https://arxiv.org/abs/2411.06037

- **Fact, Fetch, and Reason: A Unified Evaluation of Retrieval-Augmented Generation**  
  Satyapriya Krishna, Kalpesh Krishna, Anhad Mohananey, Steven Schwarcz, Adam Stambler, Shyam Upadhyay, and Manaal Faruqui. arXiv 2024.  
  This paper introduces FRAMES, the multi-hop RAG evaluation benchmark referenced by Google's Agentic RAG write-up and related FramesQA experiments.  
  Link: https://arxiv.org/abs/2409.12941

## Sources

This project summarizes public Agentic RAG behavior from Google Research and Google Cloud documentation. The Google Research Agentic RAG announcement connects the system to Sufficient Context and FramesQA/FRAMES evaluation, and the Google Cloud documentation describes the Cross Corpus Retrieval product surface. See `references/source-map.md` for source URLs, referenced papers, and implementation alignment notes.

## License

MIT. See `LICENSE`.
