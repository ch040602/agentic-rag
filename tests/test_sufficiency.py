import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentic_rag.contracts import AnswerabilityLabel, ContextAssessment, ContextStatus  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
