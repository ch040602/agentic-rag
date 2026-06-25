"""Run a deterministic Agentic RAG pipeline with two useful corpora and one distractor."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agentic_rag import (
    AgenticRAGPipeline,
    CorpusDescriptor,
    CoverageSufficiencyJudge,
    ExtractiveSynthesizer,
    InMemoryDocument,
    InMemoryKeywordRetriever,
    KeywordPlanner,
    TemplateQueryRewriter,
)


def main() -> None:
    pipeline = AgenticRAGPipeline(
        planner=KeywordPlanner(),
        query_rewriter=TemplateQueryRewriter(),
        retriever=InMemoryKeywordRetriever(
            (
                InMemoryDocument("meds-1", "pharmacy", "Discharge medications include aspirin."),
                InMemoryDocument("notes-1", "clinical", "No allergic reaction or rash was observed."),
                InMemoryDocument("ops-1", "facilities", "The cafeteria menu changed on Monday."),
            )
        ),
        sufficiency_judge=CoverageSufficiencyJudge(),
        synthesizer=ExtractiveSynthesizer(),
        max_iterations=2,
    )

    answer = pipeline.answer(
        "discharge medications and allergic reaction evidence",
        (
            CorpusDescriptor("pharmacy", "Medication orders discharge medication lists prescriptions"),
            CorpusDescriptor("clinical", "Clinical notes allergies adverse events rash observations"),
            CorpusDescriptor("facilities", "Facilities operations maintenance cafeteria menus"),
        ),
    )
    print(answer.answer)
    print(f"status={answer.status} iterations={answer.iterations}")
    for citation in answer.citations:
        print(f"- {citation.claim} -> {', '.join(citation.snippet_ids)}")


if __name__ == "__main__":
    main()
