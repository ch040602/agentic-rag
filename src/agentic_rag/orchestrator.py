"""Orchestrator for plan, retrieve, assess, iterate, and synthesize."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .contracts import (
    AnswerStatus,
    ContextAssessment,
    ContextStatus,
    Corpus,
    Drafter,
    GroundedAnswer,
    GroundedCitation,
    IterationTrace,
    Planner,
    QueryRewriter,
    Retriever,
    RunResult,
    Snippet,
    SufficientContextJudge,
    Synthesizer,
)
from .sufficiency import apply_selective_abstention_policy


@dataclass(frozen=True)
class OrchestratorConfig:
    max_iterations: int = 3
    max_snippets: int = 100

    def __post_init__(self) -> None:
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if self.max_snippets < 1:
            raise ValueError("max_snippets must be at least 1")


class AgenticRAGOrchestrator:
    def __init__(
        self,
        *,
        planner: Planner,
        rewriter: QueryRewriter,
        retriever: Retriever,
        drafter: Drafter,
        judge: SufficientContextJudge,
        synthesizer: Synthesizer,
        config: OrchestratorConfig | None = None,
    ) -> None:
        self.planner = planner
        self.rewriter = rewriter
        self.retriever = retriever
        self.drafter = drafter
        self.judge = judge
        self.synthesizer = synthesizer
        self.config = config or OrchestratorConfig()

    def run(self, question: str, corpus_catalog: Sequence[Corpus]) -> RunResult:
        plan = self.planner.plan(question, tuple(corpus_catalog), prior_assessment=None)
        prior_assessment: ContextAssessment | None = None
        snippets_by_id: dict[str, Snippet] = {}
        traces: list[IterationTrace] = []

        for iteration in range(self.config.max_iterations):
            subqueries = tuple(self.rewriter.rewrite(question, plan, prior_assessment, iteration))
            retrieved = self._retrieve_and_dedupe(subqueries, snippets_by_id)
            draft = self.drafter.draft(question, plan, tuple(snippets_by_id.values()))
            assessment = self.judge.assess(question, plan, tuple(snippets_by_id.values()), draft)
            traces.append(
                IterationTrace(
                    iteration=iteration,
                    subqueries=subqueries,
                    snippets=retrieved,
                    draft=draft,
                    assessment=assessment,
                )
            )

            if _enum_value(assessment.status) in {
                ContextStatus.SUFFICIENT.value,
                ContextStatus.IRRELEVANT.value,
                ContextStatus.UNANSWERABLE.value,
            }:
                break
            if not subqueries:
                break

            prior_assessment = assessment

        final_assessment = traces[-1].assessment
        answer = self.synthesizer.synthesize(
            question,
            plan,
            tuple(snippets_by_id.values()),
            final_assessment,
        )
        answer = self._guard_answer(answer, final_assessment, tuple(snippets_by_id.values()))
        return RunResult(
            question=question,
            plan=plan,
            answer=answer,
            iterations=tuple(traces),
            snippets=tuple(snippets_by_id.values()),
        )

    def _retrieve_and_dedupe(
        self,
        subqueries: Sequence,
        snippets_by_id: dict[str, Snippet],
    ) -> tuple[Snippet, ...]:
        retrieved: list[Snippet] = []
        for subquery in subqueries:
            for snippet in self.retriever.retrieve(subquery):
                if snippet.id in snippets_by_id:
                    continue
                if len(snippets_by_id) >= self.config.max_snippets:
                    return tuple(retrieved)
                snippets_by_id[snippet.id] = snippet
                retrieved.append(snippet)
        return tuple(retrieved)

    def _guard_answer(
        self,
        answer: GroundedAnswer,
        assessment: ContextAssessment,
        snippets: tuple[Snippet, ...],
    ) -> GroundedAnswer:
        answer = apply_selective_abstention_policy(answer, assessment)

        known_snippet_ids = {snippet.id for snippet in snippets}
        grounded_citations = tuple(
            GroundedCitation(
                claim=citation.claim,
                snippet_ids=tuple(
                    snippet_id for snippet_id in citation.snippet_ids if snippet_id in known_snippet_ids
                ),
            )
            for citation in answer.citations
            if any(snippet_id in known_snippet_ids for snippet_id in citation.snippet_ids)
        )
        if len(grounded_citations) != len(tuple(answer.citations)):
            return GroundedAnswer(
                answer=answer.answer,
                citations=grounded_citations,
                status=AnswerStatus.PARTIAL,
                missing_facts=tuple(answer.missing_facts) or tuple(assessment.missing_facts),
                sufficiency_score=assessment.sufficiency_score,
                conflicts=tuple(answer.conflicts) or tuple(assessment.conflicts),
            )
        return answer


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)
