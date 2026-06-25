import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentic_rag.contracts import (  # noqa: E402
    AnswerabilityLabel,
    Claim,
    ContextAssessment,
    ContextStatus,
    DraftAnswer,
    FeedbackQuery,
    RequiredFact,
    RetrievalPlan,
    Route,
    Snippet,
)
from agentic_rag.sufficiency import AutoraterStyleSufficiencyJudge  # noqa: E402


class SufficientContextContractTests(unittest.TestCase):
    def test_answerability_labels_cover_sufficient_context_categories(self):
        self.assertEqual("sufficient", AnswerabilityLabel.SUFFICIENT.value)
        self.assertEqual("useful_but_incomplete", AnswerabilityLabel.USEFUL_BUT_INCOMPLETE.value)
        self.assertEqual("insufficient", AnswerabilityLabel.INSUFFICIENT.value)
        self.assertEqual("conflicting", AnswerabilityLabel.CONFLICTING.value)
        self.assertEqual("unanswerable", AnswerabilityLabel.UNANSWERABLE.value)

    def test_context_assessment_keeps_existing_status_api(self):
        assessment = ContextAssessment(status=ContextStatus.SUFFICIENT, sufficiency_score=1.0)

        self.assertEqual(ContextStatus.SUFFICIENT, assessment.status)
        self.assertEqual(1.0, assessment.confidence)
        self.assertEqual(AnswerabilityLabel.SUFFICIENT, assessment.answerability_label)

    def test_context_assessment_accepts_explicit_answerability_label(self):
        assessment = ContextAssessment(
            status=ContextStatus.INSUFFICIENT,
            sufficiency_score=0.6,
            answerability=AnswerabilityLabel.USEFUL_BUT_INCOMPLETE,
            missing_facts=("Project owner",),
        )

        self.assertEqual(ContextStatus.INSUFFICIENT, assessment.status)
        self.assertEqual(AnswerabilityLabel.USEFUL_BUT_INCOMPLETE, assessment.answerability_label)

    def test_answerability_label_string_is_normalized(self):
        assessment = ContextAssessment(
            status=ContextStatus.INSUFFICIENT,
            sufficiency_score=0.2,
            answerability="conflicting",
        )

        self.assertEqual(AnswerabilityLabel.CONFLICTING, assessment.answerability_label)

    def test_unknown_answerability_label_is_rejected(self):
        with self.assertRaises(ValueError):
            ContextAssessment(
                status=ContextStatus.INSUFFICIENT,
                sufficiency_score=0.0,
                answerability="maybe",
            )


class AutoraterStyleSufficiencyJudgeTests(unittest.TestCase):
    def test_marks_sufficient_when_all_required_facts_are_supported(self):
        judge = AutoraterStyleSufficiencyJudge()
        plan = _plan(
            RequiredFact(
                "owner",
                "Project Zen owner",
                metadata={"required_terms": ("project zen", "owner", "nina")},
            )
        )
        snippets = (_snippet("s1", "Project Zen owner is Nina."),)
        draft = DraftAnswer(claims=(Claim("Project Zen owner is Nina.", ("s1",)),))

        assessment = judge.assess("Who owns Project Zen?", plan, snippets, draft)

        self.assertEqual(ContextStatus.SUFFICIENT, assessment.status)
        self.assertEqual(AnswerabilityLabel.SUFFICIENT, assessment.answerability_label)
        self.assertEqual(1.0, assessment.sufficiency_score)
        self.assertEqual(("owner",), tuple(fact.fact_id for fact in assessment.covered_facts))
        self.assertEqual((), tuple(assessment.missing_facts))
        self.assertEqual((), tuple(assessment.unsupported_claims))
        self.assertEqual((), tuple(assessment.feedback_queries))

    def test_marks_useful_but_incomplete_with_partial_required_fact_coverage(self):
        judge = AutoraterStyleSufficiencyJudge()
        plan = _plan(
            RequiredFact(
                "project",
                "Alice project",
                metadata={"required_terms": ("alice", "project zen")},
            ),
            RequiredFact(
                "owner",
                "Project Zen owner",
                metadata={"required_terms": ("project zen", "owner", "nina")},
            ),
        )
        snippets = (_snippet("s1", "Alice works on Project Zen."),)
        draft = DraftAnswer(claims=(Claim("Alice works on Project Zen.", ("s1",)),))

        assessment = judge.assess("Who owns Alice's project?", plan, snippets, draft)

        self.assertEqual(ContextStatus.INSUFFICIENT, assessment.status)
        self.assertEqual(AnswerabilityLabel.USEFUL_BUT_INCOMPLETE, assessment.answerability_label)
        self.assertEqual(0.5, assessment.sufficiency_score)
        self.assertEqual(("project",), tuple(fact.fact_id for fact in assessment.covered_facts))
        self.assertEqual(("Project Zen owner",), tuple(assessment.missing_facts))
        self.assertEqual(
            (FeedbackQuery("Project Zen owner", ("docs",), "Evidence for required fact 'owner' was not found.", "owner"),),
            tuple(assessment.feedback_queries),
        )

    def test_marks_insufficient_when_no_required_fact_is_covered(self):
        judge = AutoraterStyleSufficiencyJudge()
        plan = _plan(
            RequiredFact(
                "owner",
                "Project Zen owner",
                metadata={"required_terms": ("project zen", "owner", "nina")},
            )
        )
        snippets = (_snippet("s1", "Project Apollo launch date is archived."),)

        assessment = judge.assess("Who owns Project Zen?", plan, snippets, DraftAnswer())

        self.assertEqual(ContextStatus.INSUFFICIENT, assessment.status)
        self.assertEqual(AnswerabilityLabel.INSUFFICIENT, assessment.answerability_label)
        self.assertEqual(0.0, assessment.sufficiency_score)
        self.assertEqual(("Project Zen owner",), tuple(assessment.missing_facts))
        self.assertEqual("Project Zen owner", assessment.feedback_queries[0].query)

    def test_marks_conflicting_when_required_fact_has_incompatible_evidence(self):
        judge = AutoraterStyleSufficiencyJudge()
        plan = _plan(
            RequiredFact(
                "owner",
                "Project Zen owner",
                metadata={
                    "required_terms": ("project zen", "owner"),
                    "conflict_terms": ("nina", "omar"),
                },
            )
        )
        snippets = (
            _snippet("s1", "Project Zen owner is Nina."),
            _snippet("s2", "Project Zen owner is Omar."),
        )
        draft = DraftAnswer(
            claims=(
                Claim("Project Zen owner is Nina.", ("s1",)),
                Claim("Project Zen owner is Omar.", ("s2",)),
            )
        )

        assessment = judge.assess("Who owns Project Zen?", plan, snippets, draft)

        self.assertEqual(ContextStatus.INSUFFICIENT, assessment.status)
        self.assertEqual(AnswerabilityLabel.CONFLICTING, assessment.answerability_label)
        self.assertEqual(("owner",), tuple(fact.fact_id for fact in assessment.covered_facts))
        self.assertEqual((), tuple(assessment.missing_facts))
        self.assertIn("conflicting evidence", assessment.reason)

    def test_marks_unanswerable_when_required_fact_has_no_route_and_no_evidence(self):
        judge = AutoraterStyleSufficiencyJudge()
        plan = RetrievalPlan(
            question="Who owns Project Zen?",
            required_facts=(
                RequiredFact(
                    "owner",
                    "Project Zen owner",
                    metadata={"required_terms": ("project zen", "owner", "nina")},
                ),
            ),
            routes=(),
        )

        assessment = judge.assess("Who owns Project Zen?", plan, (), DraftAnswer())

        self.assertEqual(ContextStatus.UNANSWERABLE, assessment.status)
        self.assertEqual(AnswerabilityLabel.UNANSWERABLE, assessment.answerability_label)
        self.assertEqual(("Project Zen owner",), tuple(assessment.missing_facts))
        self.assertEqual((), tuple(assessment.feedback_queries))

    def test_reports_unsupported_draft_claims(self):
        judge = AutoraterStyleSufficiencyJudge()
        plan = _plan(
            RequiredFact(
                "owner",
                "Project Zen owner",
                metadata={"required_terms": ("project zen", "owner", "nina")},
            )
        )
        snippets = (_snippet("s1", "Project Zen owner is Nina."),)
        draft = DraftAnswer(claims=(Claim("Project Zen budget is approved.", ("missing",)),))

        assessment = judge.assess("Who owns Project Zen?", plan, snippets, draft)

        self.assertEqual(ContextStatus.INSUFFICIENT, assessment.status)
        self.assertEqual(AnswerabilityLabel.INSUFFICIENT, assessment.answerability_label)
        self.assertEqual(("Project Zen budget is approved.",), tuple(assessment.unsupported_claims))


def _plan(*facts: RequiredFact) -> RetrievalPlan:
    return RetrievalPlan(
        question="question",
        required_facts=facts,
        routes=tuple(Route(fact.id, ("docs",), "Use routed docs.") for fact in facts),
    )


def _snippet(snippet_id: str, text: str) -> Snippet:
    return Snippet(snippet_id, "docs", f"{snippet_id}-doc", text)


if __name__ == "__main__":
    unittest.main()
