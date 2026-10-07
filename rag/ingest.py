"""rag.ingest —— 把 SKU 知识卡片 (YAML) 与 Markdown 文档切分为检索文本块。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def chunk_sku(sku: dict) -> list[dict]:
    """一张 SKU 卡片 -> 多个检索块 (基本信息/卖点场景/FAQ/售后/易混淆点)。

    FAQ 单独成块: 问答对是最常被检索的内容, 独立成块提高命中精度。
    """
    base = f"{sku['name']}（{sku['id']}，{sku['category']}）"
    blocks = [
        {"text": f"{base} 规格参数: " + "; ".join(f"{k}: {v}" for k, v in sku.get("specs", {}).items()),
         "meta": {"sku": sku["id"], "kind": "specs"}},
        {"text": f"{base} 核心卖点: " + "; ".join(sku.get("selling_points", [])) +
                 "。适用场景: " + "; ".join(sku.get("scenarios", [])),
         "meta": {"sku": sku["id"], "kind": "selling"}},
        {"text": f"{base} 售后政策: " + json.dumps(sku.get("after_sales", {}), ensure_ascii=False),
         "meta": {"sku": sku["id"], "kind": "after_sales"}},
    ]
    for item in sku.get("confusion", []) or []:
        blocks.append({"text": f"{base} 易混淆点: {item}", "meta": {"sku": sku["id"], "kind": "confusion"}})
    for faq in sku.get("faq", []) or []:
        blocks.append({
            "text": f"问: {faq['q']} 答: {faq['a']}",
            "meta": {"sku": sku["id"], "kind": "faq"},
        })
    return blocks


def chunk_markdown(text: str, source: str, window: int = 400, overlap: int = 60) -> list[dict]:
    """Markdown 文档按段落聚合后滑窗切分 (控制在 window 字以内)。"""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    blocks, buf, buf_len = [], [], 0
    for p in paras:
        if buf_len + len(p) > window and buf:
            blocks.append({"text": "\n\n".join(buf), "meta": {"source": source, "kind": "doc"}})
            tail = buf[-1][-overlap:] if buf else ""
            buf, buf_len = [tail], len(tail)
        buf.append(p)
        buf_len += len(p)
    if buf:
        blocks.append({"text": "\n\n".join(buf), "meta": {"source": source, "kind": "doc"}})
    return blocks


def ingest_dir(root: Path) -> list[dict]:
    blocks: list[dict] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for sku in data.get("skus", []):
                blocks.extend(chunk_sku(sku))
        elif path.suffix.lower() == ".md":
            blocks.extend(chunk_markdown(path.read_text(encoding="utf-8"), path.name))
    return blocks


def main() -> int:
    ap = argparse.ArgumentParser(description="LEXY 知识库构建: 文档 -> 检索块")
    ap.add_argument("--input", default="data/skus")
    ap.add_argument("--out", default="kb.json")
    args = ap.parse_args()
    blocks = ingest_dir(Path(args.input))
    Path(args.out).write_text(json.dumps(blocks, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"生成 {len(blocks)} 个检索块 -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
