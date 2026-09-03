from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class RerankedResult:
    index: int  # index into the original candidate list
    score: float


class RerankerProvider(ABC):
    @abstractmethod
    async def rerank(self, query: str, documents: List[str], top_k: int) -> List[RerankedResult]:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        raise NotImplementedError
