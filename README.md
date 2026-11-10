# LEXY Product Knowledge Base and RAG

A small retrieval-augmented question-answering reference implementation for product support. It includes sample LEXY product cards, document chunking, embedding requests, JSON-backed cosine retrieval, and an answer-generation client.

## Status and scope

This is a starter implementation with sample data, not a complete product catalog or a validated production support service. Product facts and after-sales information must be checked against current authoritative documentation before use.

The answer prompt requires grounding in retrieved material and source citations. When retrieval returns no hits, the code returns a fixed "not found; refer to a human" response. The included evaluation checks whether an expected SKU appears in retrieved citations; it does not establish factual answer accuracy.

## Components

| Path | Purpose |
|---|---|
| `data/skus/catalog.example.yaml` | Example product cards |
| `rag/ingest.py` | YAML/Markdown documents to retrieval chunks |
| `rag/embed.py` | Embedding client for an OpenAI-compatible endpoint |
| `rag/store.py` | Cosine search and JSON persistence |
| `rag/qa.py` | Retrieval, answer generation, and citation metadata |
| `eval/sample_qa.yaml` | Sample SKU-retrieval checks |

## Quick start

Use Python 3.10 or newer and install the existing dependencies:

```bash
python -m pip install -r requirements.txt
```

Run your own embedding and chat services before embedding documents or generating answers. The URLs and model IDs below are local examples; set them to match the services you operate.

```bash
export EMBED_BASE_URL=http://127.0.0.1:11434/v1
export EMBED_MODEL=bge-m3
export LLM_BASE_URL=http://127.0.0.1:8080/v1
export LLM_MODEL=qwen3.6-35b-a3b

# Build and embed the sample knowledge base.
python -m rag.ingest --input data/skus --out kb.json
python -m rag.embed --input kb.json --out kb.vec.json

# Ask a question grounded in the retrieved cards.
python -m rag.qa --kb kb.vec.json --q "碧云泉C5 Plus的滤芯多久换一次"

# Run the included SKU-retrieval checks.
python -m rag.qa --kb kb.vec.json --eval eval/sample_qa.yaml
```

Embedding and chat requests are sent to the configured endpoints. The code defaults to local loopback endpoints; it contains no deployment-specific server address. Model access, endpoint availability, and any provider costs are the operator's responsibility.

## Product-card guidance

Keep specifications, selling points, applicable scenarios, FAQs, after-sales policies, and commonly confused details in each card. Preserve source references and review the sample content before expanding it.

Do not invent specifications or treat a historical price note as a current quote. Human review remains necessary for customer-facing answers.

## 中文说明

本仓库是产品知识库与问答链的参考实现，附带示例数据。通过 `EMBED_BASE_URL`、`EMBED_MODEL`、`LLM_BASE_URL` 和 `LLM_MODEL` 配置自己使用的服务；默认地址为本机回环地址。

检索未命中时返回「未找到相关资料，建议转人工」。示例评测只检查期望 SKU 是否出现在引用中，不代表答案事实准确率或生产环境验收结果。产品和品牌名称在示例中保留其真实含义。
