"""Narrow, provenance-preserving external research retrieval adapters."""

from .github import GitHubDiscussionsAdapter, GitHubRestAdapter
from .models import CollectionResult, RetrievalError, RetrievalState, SearchLead, SearchResult, SourceRecord
from .tavily import TavilyAdapter

__all__ = [
    "CollectionResult", "GitHubDiscussionsAdapter", "GitHubRestAdapter",
    "RetrievalError", "RetrievalState", "SearchLead", "SearchResult",
    "SourceRecord", "TavilyAdapter",
]
