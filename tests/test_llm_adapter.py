import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentic_rag.adapters.llm import SchemaValidationError, get_schema, to_dataclass, to_mapping  # noqa: E402
from agentic_rag.contracts import (  # noqa: E402
    ContextAssessment,
    GroundedAnswer,
    QueryRewriteResult,
    RetrievalPlan,
)


class LLMAdapterSchemaTests(unittest.TestCase):
    def test_registry_contains_structured_output_schemas(self):
        self.assertIs(get_schema("RetrievalPlan").target_type, RetrievalPlan)
        self.assertIs(get_schema("QueryRewriteResult").target_type, QueryRewriteResult)
        self.assertIs(get_schema("ContextAssessment").target_type, ContextAssessment)
        self.assertIs(get_schema("GroundedAnswer").target_type, GroundedAnswer)

    def test_converts_retrieval_plan_mapping_to_dataclass_and_back(self):
        raw_plan = {
            "question": "Who owns Alice's project?",
            "required_facts": [
                {"id": "person_project", "description": "Alice project", "priority": "must"},
                {"id": "project_owner", "description": "Project owner", "priority": "must"},
            ],
            "routes": [
                {
                    "fact_id": "person_project",
                    "candidate_corpus_ids": ["directory"],
                    "reason": "Assignments are in directory.",
                }
            ],
            "stop_conditions": ["Stop when owner is known."],
        }

        plan = to_dataclass("RetrievalPlan", raw_plan)

        self.assertIsInstance(plan, RetrievalPlan)
        self.assertEqual("person_project", plan.required_facts[0].id)
        self.assertEqual(("directory",), tuple(plan.routes[0].candidate_corpus_ids))
        self.assertEqual(raw_plan, to_mapping("RetrievalPlan", plan))

    def test_converts_query_rewrite_result_mapping(self):
        result = to_dataclass(
            "QueryRewriteResult",
            {
                "subqueries": [
                    {
                        "id": "q0-0",
                        "fact_id": "project_owner",
                        "query": "Project Zen owner",
                        "target_corpus_ids": ["projects"],
                        "reason": "Project records contain owners.",
                    }
                ]
            },
        )

        self.assertIsInstance(result, QueryRewriteResult)
        self.assertEqual("q0-0", result.subqueries[0].id)

    def test_converts_context_assessment_and_grounded_answer(self):
        assessment = to_dataclass(
            "ContextAssessment",
            {
                "status": "insufficient",
                "sufficiency_score": 0.5,
                "covered_facts": [{"fact_id": "person_project", "snippet_ids": ["s1"]}],
                "missing_facts": ["Project owner"],
                "unsupported_claims": [],
                "feedback_queries": [
                    {
                        "query": "Project owner",
                        "target_corpus_ids": ["projects"],
                        "reason": "Missing required fact.",
                    }
                ],
                "reason": "One fact is missing.",
            },
        )
        answer = to_dataclass(
            "GroundedAnswer",
            {
                "answer": "Partial evidence found.",
                "citations": [{"claim": "person_project", "snippet_ids": ["s1"]}],
                "status": "partial",
                "missing_facts": ["Project owner"],
                "sufficiency_score": 0.5,
            },
        )

        self.assertIsInstance(assessment, ContextAssessment)
        self.assertEqual(("Project owner",), tuple(assessment.missing_facts))
        self.assertEqual("s1", assessment.covered_facts[0].snippet_ids[0])
        self.assertIsInstance(answer, GroundedAnswer)
        self.assertEqual("person_project", answer.citations[0].claim)

    def test_missing_required_field_raises_schema_error(self):
        with self.assertRaises(SchemaValidationError) as error:
            to_dataclass(
                "GroundedAnswer",
                {
                    "answer": "No citations field.",
                    "status": "partial",
                    "missing_facts": [],
                    "sufficiency_score": 0.0,
                },
            )

        self.assertIn("citations", str(error.exception))


if __name__ == "__main__":
    unittest.main()
