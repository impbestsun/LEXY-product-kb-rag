"""rag.embed —— Embedding 客户端 (OpenAI 兼容接口, 支持本地 bge-m3 / 部门服务)。"""
from __future__ import annotations

import json
import os
from pathlib import Path

import requests


class Embedder:
    """OpenAI 兼容 embeddings 客户端。

    默认指向本地 bge-m3 (Ollama/vLLM), 可通过环境变量覆盖:
        EMBED_BASE_URL=http://127.0.0.1:11434/v1
        EMBED_MODEL=bge-m3
    """

    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: int = 30):
        self.base_url = (base_url or os.environ.get("EMBED_BASE_URL", "http://127.0.0.1:11434/v1")).rstrip("/")
        self.model = model or os.environ.get("EMBED_MODEL", "bge-m3")
        self.timeout = timeout
        self.dim = int(os.environ.get("EMBED_DIM", "1024"))  # bge-m3 = 1024

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = requests.post(
            f"{self.base_url}/embeddings",
            json={"model": self.model, "input": texts},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        return [sorted(data, key=lambda d: d["index"])[i]["embedding"] for i in range(len(texts))]


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="为检索块补齐向量")
    ap.add_argument("--input", default="kb.json")
    ap.add_argument("--out", default="kb.vec.json")
    args = ap.parse_args()
    blocks = json.loads(Path(args.input).read_text(encoding="utf-8"))
    texts = [b["text"] for b in blocks]
    # 批量 32 条, 避免超长请求
    vecs: list[list[float]] = []
    emb = Embedder()
    for i in range(0, len(texts), 32):
        vecs.extend(emb.embed(texts[i:i + 32]))
        print(f"embedded {min(i + 32, len(texts))}/{len(texts)}")
    for b, v in zip(blocks, vecs):
        b["vec"] = v
    Path(args.out).write_text(json.dumps(blocks, ensure_ascii=False), encoding="utf-8")
    print(f"向量化完成 -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
