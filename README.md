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
- [Quick Start](#quick-start)
- [Expected Output Shape](#expected-output-shape)
- [Implementation Rules](#implementation-rules)
- [Skill Packaging](#skill-packaging)
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
+-- agents/
|   +-- openai.yaml
+-- references/
|   +-- agentic-rag-behavior.md
|   +-- agentic-rag-behavior-summary.md
|   +-- codex-completion-brief.md
|   +-- prompts-and-schemas.md
|   +-- source-map.md
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

## Quick Start

This scaffold has no runtime dependencies beyond Python 3.11+.

Install from a source checkout:

```bash
python -m pip install -e .
```

Run the tests:

```bash
python -m unittest discover -s tests -v
```

When running ad-hoc scripts without installing the package, set `PYTHONPATH=src` before importing `agentic_rag`.

Use the deterministic in-memory components:

```python
from agentic_rag.adapters.in_memory import (
    EvidenceCoverageJudge,
    FeedbackAwareQueryRewriter,
    InMemoryDocument,
    InMemoryRetriever,
    RuleBasedSynthesizer,
    ScriptedPlanner,
    SnippetDrafter,
)
from agentic_rag.contracts import Corpus, RequiredFact, RetrievalPlan, Route
from agentic_rag.orchestrator import AgenticRAGOrchestrator, OrchestratorConfig

plan = RetrievalPlan(
    question="Who owns Alice's project?",
    required_facts=(
        RequiredFact(
            id="person_project",
            description="Alice's project name",
            metadata={"required_terms": ("alice", "project zen")},
        ),
        RequiredFact(
            id="project_owner",
            description="Project Zen owner",
            metadata={"required_terms": ("project zen", "owner", "nina")},
        ),
    ),
    routes=(
        Route("person_project", ("directory",), "People records contain assignments."),
        Route("project_owner", ("projects",), "Project records contain owners."),
    ),
)

retriever = InMemoryRetriever(
    (
        InMemoryDocument("directory", "people-1", "Alice works on Project Zen."),
        InMemoryDocument("projects", "project-1", "Project Zen owner is Nina."),
    )
)

orchestrator = AgenticRAGOrchestrator(
    planner=ScriptedPlanner(plan),
    rewriter=FeedbackAwareQueryRewriter(initial_fact_ids=("person_project",)),
    retriever=retriever,
    drafter=SnippetDrafter(),
    judge=EvidenceCoverageJudge(),
    synthesizer=RuleBasedSynthesizer(),
    config=OrchestratorConfig(max_iterations=2),
)

result = orchestrator.run(
    "Who owns Alice's project?",
    (
        Corpus("directory", "Employee directory and project assignments."),
        Corpus("projects", "Project ownership records."),
    ),
)

print(result.answer.status)
print(result.answer.sufficiency_score)
print(result.answer.citations)
```

## Expected Output Shape

Final answers should be grounded by snippet ids:

```python
GroundedAnswer(
    answer="project_owner: [projects:project-1:q1-0]",
    citations=(
        GroundedCitation(
            claim="project_owner",
            snippet_ids=("projects:project-1:q1-0",),
        ),
    ),
    status=AnswerStatus.ANSWERED,
    missing_facts=(),
    sufficiency_score=1.0,
)
```

When evidence is missing, the assessment returns targeted follow-up queries:

```python
ContextAssessment(
    status=ContextStatus.INSUFFICIENT,
    sufficiency_score=0.5,
    missing_facts=("Project Zen owner",),
    feedback_queries=(
        FeedbackQuery(
            query="Project Zen owner",
            target_corpus_ids=("projects",),
            reason="Evidence for required fact 'project_owner' was not found.",
        ),
    ),
)
```

When evidence conflicts, the answer stays partial and cites both incompatible groups:

```python
GroundedAnswer(
    answer="Conflicting evidence prevents a definitive grounded answer.",
    citations=(
        GroundedCitation("owner:nina", ("projects:project-1:q0-0",)),
        GroundedCitation("owner:omar", ("projects:project-2:q0-0",)),
    ),
    status=AnswerStatus.PARTIAL,
    sufficiency_score=0.5,
)
```

## Implementation Rules

- Keep provider integrations behind adapters.
- Preserve corpus descriptions and use them as routing metadata.
- Preserve query lineage from original question to final citation.
- Treat sufficiency as a fact-coverage decision, not a vector-score threshold.
- Never return a fully answered result after an insufficient sufficiency check.
- Enforce iteration and cost limits in the orchestrator or adapter layer.

## Skill Packaging

This repository is packaged as an Agent Skill:

- `SKILL.md` is the skill entrypoint with YAML frontmatter, activation guidance, workflow steps, implementation rules, and anti-patterns.
- `agents/openai.yaml` provides Codex-facing display metadata and allows implicit invocation.
- `references/` contains progressively loaded background material, prompt contracts, source mapping, and completion guidance.
- `src/agentic_rag/` is an optional Python scaffold that agents can reuse when a task needs executable contracts or tests.
- `tests/` verifies the scaffold behavior without network access or provider credentials.

The skill can be used directly from this folder by clients that scan skill directories, or its Python scaffold can be installed in editable mode for local development.

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
