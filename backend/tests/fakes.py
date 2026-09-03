"""
Fake implementations of every provider interface, used across tests so
retrieval/ingestion logic can be verified without any network access.
"""
from typing import Any, Dict, List, Optional

from app.core.exceptions import ProviderUnavailableError
from app.services.embeddings.base import EmbeddingProvider
from app.services.environment.base import EnvironmentalReading, EnvironmentDataProvider
from app.services.llm.base import LLMProvider, LLMResponse
from app.services.rerank.base import RerankedResult, RerankerProvider
from app.services.vectorstore.base import VectorRecord, VectorSearchResult, VectorStore


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic fake: embedding = [len(text), num_words, 0.0, ...] padded to `dim`."""

    def __init__(self, dim: int = 8):
        self.dim = dim

    def _embed_one(self, text: str) -> List[float]:
        vec = [float(len(text)), float(len(text.split()))]
        vec += [0.0] * (self.dim - len(vec))
        return vec[: self.dim]

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(t) for t in texts]

    async def embed_query(self, text: str) -> List[float]:
        return self._embed_one(text)

    async def health_check(self) -> bool:
        return True


class FakeVectorStore(VectorStore):
    """In-memory store; search returns everything matching the filter, ranked
    by naive vector-length similarity so tests are deterministic."""

    def __init__(self):
        self._points: Dict[str, VectorRecord] = {}
        self.collection_ensured = False

    async def ensure_collection(self) -> None:
        self.collection_ensured = True

    async def upsert(self, records: List[VectorRecord]) -> None:
        for r in records:
            self._points[r.id] = r

    async def search(
        self, query_vector: List[float], top_k: int, metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        candidates = list(self._points.values())
        if metadata_filter:
            candidates = [
                r for r in candidates
                if all(r.payload.get(k) == v for k, v in metadata_filter.items())
            ]

        def score(record: VectorRecord) -> float:
            # crude cosine-ish similarity stand-in, good enough to rank deterministically
            dot = sum(a * b for a, b in zip(record.vector, query_vector))
            return dot

        ranked = sorted(candidates, key=score, reverse=True)[:top_k]
        return [
            VectorSearchResult(id=r.id, score=score(r), payload=r.payload) for r in ranked
        ]

    async def delete(self, ids: List[str]) -> None:
        for i in ids:
            self._points.pop(i, None)

    async def health_check(self) -> bool:
        return True


class FakeReranker(RerankerProvider):
    """Reranks by simple text length proximity to the query length — deterministic, no network."""

    async def rerank(self, query: str, documents: List[str], top_k: int) -> List[RerankedResult]:
        scored = sorted(
            range(len(documents)),
            key=lambda i: -abs(len(documents[i]) - len(query)),
        )
        return [RerankedResult(index=i, score=1.0 / (rank + 1)) for rank, i in enumerate(scored[:top_k])]

    async def health_check(self) -> bool:
        return True


class FakeLLMProvider(LLMProvider):
    """Stand-in for GroqProvider — returns a canned or templated response
    without making any network call."""

    def __init__(self, canned_text: str = "fake grounded answer", model: str = "fake-model"):
        self._canned_text = canned_text
        self._model = model
        self.last_system_prompt = None
        self.last_user_prompt = None

    async def generate(self, system_prompt, user_prompt, **kwargs) -> LLMResponse:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return LLMResponse(text=self._canned_text, model=self._model)

    async def health_check(self) -> bool:
        return True


class _FakeExecuteResult:
    def __init__(self, data):
        self.data = data


class _FakeQueryBuilder:
    """Minimal stand-in for the postgrest-py query builder used by
    supabase-py, supporting only the operations our repositories call:
    select / eq / gte / lte / limit / insert / upsert / execute."""

    def __init__(self, table: "FakeSupabaseTable"):
        self._table = table
        self._filters = []  # list of (op, column, value)
        self._limit = None
        self._pending_insert = None
        self._pending_upsert = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, column, value):
        self._filters.append(("eq", column, value))
        return self

    def gte(self, column, value):
        self._filters.append(("gte", column, value))
        return self

    def lte(self, column, value):
        self._filters.append(("lte", column, value))
        return self

    def limit(self, n):
        self._limit = n
        return self

    def insert(self, record):
        self._pending_insert = record
        return self

    def upsert(self, record):
        self._pending_upsert = record
        return self

    def _matches(self, row: dict) -> bool:
        for op, column, value in self._filters:
            row_value = row.get(column)
            if op == "eq" and row_value != value:
                return False
            if op == "gte" and not (row_value is not None and row_value >= value):
                return False
            if op == "lte" and not (row_value is not None and row_value <= value):
                return False
        return True

    def execute(self):
        if self._pending_insert is not None:
            import uuid

            record = dict(self._pending_insert)
            record.setdefault("id", str(uuid.uuid4()))
            self._table.rows.append(record)
            return _FakeExecuteResult([record])

        if self._pending_upsert is not None:
            import uuid

            record = dict(self._pending_upsert)
            record.setdefault("id", str(uuid.uuid4()))
            self._table.rows.append(record)
            return _FakeExecuteResult([record])

        results = [row for row in self._table.rows if self._matches(row)]
        if self._limit is not None:
            results = results[: self._limit]
        return _FakeExecuteResult(results)


class FakeSupabaseTable:
    def __init__(self):
        self.rows: list = []


class FakeSupabaseClient:
    """Stand-in for the supabase-py Client — enough surface area for
    SupabaseRepository subclasses to be tested without a real project."""

    def __init__(self):
        self._tables: Dict[str, FakeSupabaseTable] = {}

    def seed(self, table_name: str, rows: list) -> None:
        self._tables.setdefault(table_name, FakeSupabaseTable()).rows.extend(rows)

    def table(self, name: str) -> _FakeQueryBuilder:
        table = self._tables.setdefault(name, FakeSupabaseTable())
        return _FakeQueryBuilder(table)


class FakeEnvironmentProvider(EnvironmentDataProvider):
    """Stand-in for SoilGridsProvider/NasaPowerProvider."""

    def __init__(self, name: str = "FakeProvider", reading: Optional[EnvironmentalReading] = None,
                 fail: bool = False):
        self.name = name
        self._reading = reading
        self._fail = fail
        self.calls: List[tuple] = []

    async def fetch(self, latitude: float, longitude: float) -> Optional[EnvironmentalReading]:
        self.calls.append((latitude, longitude))
        if self._fail:
            raise ProviderUnavailableError(f"{self.name} unreachable")
        return self._reading

    async def health_check(self) -> bool:
        return not self._fail
