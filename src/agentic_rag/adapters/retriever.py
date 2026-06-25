"""Dependency-free retriever adapters with preserved snippet provenance."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from agentic_rag.contracts import Snippet, Subquery


@dataclass(frozen=True)
class LexicalDocument:
    corpus_id: str
    document_id: str
    text: str
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class _TokenMatch:
    token: str
    start: int
    end: int


class LexicalRetriever:
    """Simple lexical retriever for local tests, demos, and adapter baselines."""

    def __init__(self, documents: Sequence[LexicalDocument], *, per_query_limit: int = 5) -> None:
        self.documents = tuple(documents)
        self.per_query_limit = per_query_limit
        self.calls: list[Subquery] = []

    def retrieve(self, subquery: Subquery) -> Sequence[Snippet]:
        self.calls.append(subquery)
        query_terms = _tokens(subquery.query)
        if not query_terms:
            return ()

        matches: list[Snippet] = []
        for document in self.documents:
            if document.corpus_id not in subquery.target_corpus_ids:
                continue
            token_matches = _token_matches(document.text)
            document_terms = {match.token for match in token_matches}
            overlap = query_terms & document_terms
            phrase_span = _phrase_span(document.text, subquery.query)
            if not overlap and phrase_span is None:
                continue

            score = float(len(overlap)) + (2.0 if phrase_span is not None else 0.0)
            span = phrase_span or _overlap_span(token_matches, overlap)
            matches.append(
                Snippet(
                    id=f"{document.corpus_id}:{document.document_id}:{subquery.id}",
                    corpus_id=document.corpus_id,
                    document_id=document.document_id,
                    text=document.text,
                    score=score,
                    metadata=document.metadata,
                    span=span,
                    query_id=subquery.id,
                    fact_id=subquery.fact_id,
                )
            )

        return tuple(sorted(matches, key=lambda snippet: snippet.score, reverse=True)[: self.per_query_limit])


def _tokens(text: str) -> set[str]:
    return {match.group(0).lower() for match in re.finditer(r"[a-z0-9]+", text.lower())}


def _token_matches(text: str) -> tuple[_TokenMatch, ...]:
    return tuple(
        _TokenMatch(match.group(0).lower(), match.start(), match.end())
        for match in re.finditer(r"[a-z0-9]+", text.lower())
    )


def _phrase_span(text: str, phrase: str) -> tuple[int, int] | None:
    if not phrase.strip():
        return None
    start = text.lower().find(phrase.lower())
    if start < 0:
        return None
    return (start, start + len(phrase))


def _overlap_span(token_matches: Sequence[_TokenMatch], overlap: set[str]) -> tuple[int, int] | None:
    overlapping = tuple(match for match in token_matches if match.token in overlap)
    if not overlapping:
        return None
    return (overlapping[0].start, overlapping[-1].end)
