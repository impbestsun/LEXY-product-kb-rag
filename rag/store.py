"""rag.store —— 向量库 (numpy 余弦检索, JSON 持久化; 零重型依赖, 可平滑替换 Qdrant/Milvus)。"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


@dataclass
class Hit:
    text: str
    meta: dict
    score: float


class VectorStore:
    def __init__(self, blocks: list[dict]):
        self.blocks = blocks

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        blocks = json.loads(Path(path).read_text(encoding="utf-8"))
        if not blocks or "vec" not in blocks[0]:
            raise ValueError(f"{path} 不是向量化后的知识库 (缺少 vec 字段), 请先运行 rag.embed")
        return cls(blocks)

    def search(self, query_vec: list[float], top_k: int = 5, threshold: float = 0.25) -> list[Hit]:
        scored = [(_cos(query_vec, b["vec"]), b) for b in self.blocks if b.get("vec")]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [Hit(text=b["text"], meta=b.get("meta", {}), score=round(s, 4))
                for s, b in scored[:top_k] if s >= threshold]
