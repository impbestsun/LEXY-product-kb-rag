"""rag.qa —— RAG 问答链: 检索 -> grounding 生成 -> 带引用返回。

通过环境变量配置 OpenAI 兼容的 LLM 服务 (默认本机回环地址):
    export LLM_BASE_URL=http://127.0.0.1:8080/v1
    export LLM_MODEL=qwen3.6-35b-a3b
红线: 无检索命中必须回答「未找到相关资料」并建议转人工, 禁止编造参数。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

from .embed import Embedder
from .store import Hit, VectorStore

SYSTEM_PROMPT = """你是莱克电气产品知识库问答助手。规则:
1. 只能基于【参考资料】回答问题, 禁止使用记忆或编造参数;
2. 答案末尾必须列出引用的 SKU/文档;
3. 参考资料不足以回答时, 明确回答「未找到相关资料, 建议转人工」, 不得猜测;
4. 价格以电商后台实时价为准, 知识库中的 price_note 不得当成报价;
5. 语气专业简洁, 面向客服场景, 可直接转发客户。"""


def _llm_chat(prompt: str) -> str:
    base = os.environ.get("LLM_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL", "qwen3.6-35b-a3b")
    resp = requests.post(
        f"{base}/chat/completions",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_prompt(question: str, hits: list[Hit]) -> str:
    ctx = "\n---\n".join(f"[{i + 1}] ({h.meta.get('sku', h.meta.get('source', 'doc'))}) {h.text}" for i, h in enumerate(hits))
    return f"【参考资料】\n{ctx}\n\n【问题】{question}\n\n请按规则作答。"


def answer(question: str, store: VectorStore, embedder: Embedder, top_k: int = 5) -> dict:
    qv = embedder.embed([question])[0]
    hits = store.search(qv, top_k=top_k)
    if not hits:
        return {"answer": "未找到相关资料, 建议转人工。", "citations": [], "hits": 0}
    reply = _llm_chat(build_prompt(question, hits))
    citations = [{"sku": h.meta.get("sku"), "kind": h.meta.get("kind"), "score": h.score} for h in hits]
    return {"answer": reply, "citations": citations, "hits": len(hits)}


def main() -> int:
    ap = argparse.ArgumentParser(description="LEXY 产品知识库问答")
    ap.add_argument("--kb", default="kb.vec.json")
    ap.add_argument("--q", help="单次提问")
    ap.add_argument("--eval", help="评测问答集 YAML 路径")
    args = ap.parse_args()

    store = VectorStore.load(args.kb)
    embedder = Embedder()

    if args.q:
        print(json.dumps(answer(args.q, store, embedder), ensure_ascii=False, indent=1))
        return 0

    if args.eval:
        import yaml

        cases = yaml.safe_load(Path(args.eval).read_text(encoding="utf-8")).get("cases", [])
        ok = 0
        for c in cases:
            r = answer(c["q"], store, embedder)
            hit = c.get("expect_sku", "") in json.dumps(r["citations"], ensure_ascii=False)
            ok += hit
            print(f"[{'PASS' if hit else 'FAIL'}] {c['q']} -> cites={r['citations'][:2]}")
        print(f"通过 {ok}/{len(cases)}")
        return 0 if ok == len(cases) else 1

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
