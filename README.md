# Agentic RAG Skill

Agentic RAG is a Codex-compatible Agent Skill and dependency-free Python scaffold for building RAG systems that can decide whether retrieved context is sufficient, identify missing facts, generate targeted follow-up queries, and produce claim-level citations.

The repository focuses on the product gap between ordinary "retrieve once, answer once" RAG and a more dependable loop:

```text
plan -> route -> rewrite -> retrieve -> draft -> judge sufficiency -> iterate -> synthesize
```

It is intended for enterprise document search, internal knowledge assistants, RAG application developers, and researchers who need auditable evidence coverage rather than confident answers from incomplete context.

## What This Skill Provides

- A Codex `SKILL.md` with activation rules and implementation guidance for Agentic RAG workflows.
- Stable Python contracts for corpus catalogs, retrieval plans, subqueries, snippets, claim citations, context assessments, feedback queries, and grounded answers.
- A portable orchestrator that runs iterative retrieval and refuses to mark unsupported answers as grounded.
- Deterministic in-memory adapters for tests, demos, and provider-adapter contract checks.
- Reference prompts and JSON schemas for planner, query rewriter, sufficiency judge, and synthesizer components.
- Tests covering iterative retrieval, missing evidence feedback, unsupported claim detection, citation completeness, and route-aware retrieval.

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
|       +-- orchestrator.py
|       +-- adapters/
|           +-- llm.py
|           +-- retriever.py
|           +-- in_memory.py
+-- tests/
    +-- test_llm_adapter.py
    +-- test_orchestrator.py
    +-- test_retriever_adapter.py
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
- `ContextAssessment`: sufficiency status, `sufficiency_score`, covered facts, missing facts, unsupported claims, and feedback queries.
- `AnswerabilityLabel`: Sufficient Context answerability labels for sufficient, useful-but-incomplete, insufficient, conflicting, and unanswerable contexts.
- `GroundedAnswer`: answer text, claim-level citations, status, missing facts, and final sufficiency score.
- `IterationTrace`: subqueries, snippets, draft, and assessment for each loop iteration.

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

## Implementation Rules

- Keep provider integrations behind adapters.
- Preserve corpus descriptions and use them as routing metadata.
- Preserve query lineage from original question to final citation.
- Treat sufficiency as a fact-coverage decision, not a vector-score threshold.
- Never return a fully answered result after an insufficient sufficiency check.
- Enforce iteration and cost limits in the orchestrator or adapter layer.

## Current Status

Implemented:

- Portable contracts
- Iterative orchestrator
- Deterministic in-memory adapters
- Claim-level citation output
- Sufficiency scoring
- Missing-fact feedback queries
- Editable package installation through `pyproject.toml`
- GitHub Actions test CI
- Explicit stop behavior when the rewriter produces no subqueries
- Citation guard that rejects snippet ids not present in retrieved evidence
- Structured-output schema registry and dataclass conversion helpers for LLM adapters
- Structured JSON parsing with explicit validation errors for malformed JSON, enum mismatches, field type mismatches, and missing fields
- One-shot structured output repair protocol with injected repair callable and strict revalidation
- Provenance-preserving lexical retriever adapter with routed corpus filtering and snippet spans
- Deterministic lexical retrieval scoring, ordering, and duplicate-document handling
- Sufficient Context answerability labels that preserve the existing context status API
- Unit tests for core loop behavior, structured-output conversion, and lexical retrieval

Improvement TODOs completed in this pass:

- `RDD-T-00000002`: Packaging metadata for editable installs.
- `RDD-T-00000003`: GitHub Actions test CI.
- `RDD-T-00000004`: Empty-subquery stop behavior.
- `RDD-T-00000005`: Citation provenance guard.
- `RDD-T-00000006`: README and source-map roadmap alignment.
- `RDD-T-00000013`: Paper implementation TODO roadmap.
- `RDD-T-00000029`: Decomposed paper implementation TODO documentation.
- `RDD-T-00000014`: Structured-output schema registry and dataclass conversion helpers.
- `RDD-T-00000015`: Structured JSON parser and validation errors.
- `RDD-T-00000016`: One-shot structured output repair protocol contract.
- `RDD-T-00000017`: Provenance-preserving lexical retriever adapter.
- `RDD-T-00000018`: Retrieval scoring and deduplication tests.
- `RDD-T-00000019`: Sufficient Context answerability categories.

## Paper Implementation Roadmap

The next implementation backlog is tracked in `.codex/review-driven-development/todos.jsonl` and ordered to follow the referenced papers and public Agentic RAG write-up. Parent TODOs define the paper-aligned milestones; child TODOs define the implementation sequence.

1. `RDD-T-00000007`: Add structured-output LLM adapter contracts and JSON repair. This maps the planner, query rewriter, sufficiency judge, and synthesizer prompts into validated machine-readable outputs.
   - `RDD-T-00000014`: Define schema registry and dataclass conversion helpers for `RetrievalPlan`, `QueryRewriteResult`, `ContextAssessment`, and `GroundedAnswer`.
   - `RDD-T-00000015`: Add structured JSON parser and validation errors for malformed JSON, wrong enum values, wrong field types, and missing fields. Completed.
   - `RDD-T-00000016`: Add one-shot JSON repair protocol contract with an injected repair callable and tests for success and failure. Completed.
2. `RDD-T-00000008`: Add retriever adapter baseline with provenance-preserving lexical retrieval. This follows the original RAG paper's emphasis on retrieved non-parametric memory and provenance.
   - `RDD-T-00000017`: Add provenance-preserving lexical retriever adapter outside the orchestrator. Completed.
   - `RDD-T-00000018`: Add deterministic retrieval scoring, span extraction, and deduplication tests. Completed.
3. `RDD-T-00000009`: Implement Sufficient Context autorater and abstention policy. This follows the Sufficient Context paper by distinguishing answerable, useful-but-incomplete, insufficient, conflicting, and unanswerable contexts.
   - `RDD-T-00000019`: Add answerability categories while preserving the existing context status API. Completed.
   - `RDD-T-00000020`: Implement an autorater-style sufficiency judge that returns missing facts, unsupported claims, covered facts, and feedback queries.
   - `RDD-T-00000021`: Add selective generation abstention policy so insufficient contexts cannot produce fully answered results.
4. `RDD-T-00000010`: Add FRAMES-style multi-hop evaluation harness. This follows the Fact, Fetch, and Reason evaluation framing with fact coverage, fetch coverage, reasoning correctness, citation completeness, and iteration count.
   - `RDD-T-00000022`: Add FRAMES-style fixture format and metrics for facts, retrieval, reasoning, citations, and iterations.
   - `RDD-T-00000023`: Add iterative-vs-single-shot evaluation tests using a tiny multi-hop fixture.
5. `RDD-T-00000011`: Add conflict-aware grounded synthesis. This ensures conflicting snippets are cited and surfaced instead of silently merged.
   - `RDD-T-00000024`: Add conflict evidence contracts that can cite both incompatible snippet groups.
   - `RDD-T-00000025`: Implement conflict-aware judge and synthesis behavior for contradictory evidence.
6. `RDD-T-00000012`: Add Google Cross Corpus Retrieval adapter scaffold. This keeps native Google mode outside the orchestrator while preserving portable mode as the default.
   - `RDD-T-00000026`: Add Google native mode configuration validation for project, location, corpus resources, and service-account assumptions.
   - `RDD-T-00000027`: Add a Google Cross Corpus request adapter seam with injected client/callable tests and no network dependency.
   - `RDD-T-00000028`: Document portable mode versus Google native mode, including default no-SDK import behavior.

Planned follow-up work should be implemented through those RDD TODOs rather than as ad-hoc changes.

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
