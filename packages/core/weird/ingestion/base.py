from __future__ import annotations

from abc import ABC, abstractmethod

from weird.ingestion import NormalizedItem


class SourceAdapter(ABC):
    name: str
    source_type: str

    @abstractmethod
    def fetch(self) -> list[NormalizedItem]:
        raise NotImplementedError
