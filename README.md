# LEXY 产品知识库与售前智能问答 (product-kb-rag)

莱克电气 品牌部 —— 莱克 / 碧云泉 / 咖博士全 SKU 产品知识库，基于 RAG（检索增强生成）的售前智能问答，服务电商客服、直播话术辅助与新员工产品培训。

目标：在售 SKU 知识覆盖 **100%**；客服首次响应时间 **5 分钟 → 30 秒**；重复性售前咨询转人工率 **-50%**。

## AI 工具与技术栈

| 环节 | 工具/模型 | 说明 |
|---|---|---|
| 文档解析与切分 | Python（YAML/Markdown 结构化 + 滑动窗口切分） | SKU 卡片 / 参数表 / 售后政策 |
| Embedding | bge-m3（本地 vLLM/Ollama 部署）或 OpenAI 兼容接口 | 1024 维稠密向量 |
| 向量检索 | 本地 numpy 余弦检索（零外部依赖，可替换 Qdrant/Milvus） | Top-K + 相似度阈值 |
| 答案生成 | Qwen3.6-35B-A3B（部门 RISC-V AI 服务器 llama.cpp 部署，OpenAI 兼容接口） | 检索结果 grounding + 引用来源 |
| 评测 | 抽样问答集 + 人工抽检 | 准确率/拒答率统计 |

## 目录结构

```
├── data/skus/
│   └── catalog.example.yaml     # SKU 知识卡片 (示例 3 款, 按此模板扩充至全量 SKU)
├── rag/
│   ├── ingest.py                # YAML/MD -> 文本块 (chunk)
│   ├── embed.py                 # Embedding 客户端 (本地 bge-m3 或 OpenAI 兼容)
│   ├── store.py                 # 向量库 (numpy 余弦, JSON 持久化)
│   └── qa.py                    # RAG 问答链 (检索 + grounding 生成 + 引用)
├── eval/
│   └── sample_qa.yaml           # 评测问答集
└── requirements.txt
```

## 快速开始

```bash
pip install -r requirements.txt

# 1. 构建知识库 (默认读取 data/skus/, 输出 kb.json)
python -m rag.ingest --input data/skus --out kb.json
python -m rag.embed  --input kb.json --out kb.vec.json

# 2. 问答 (默认连部门 Qwen 服务器, 可用环境变量覆盖)
export LLM_BASE_URL=http://192.168.7.176:8080/v1   # 部门 RISC-V 服务器 llama.cpp
export LLM_MODEL=qwen3.6-35b-a3b
python -m rag.qa --kb kb.vec.json --q "碧云泉C5 Plus的滤芯多久换一次"

# 3. 评测
python -m rag.qa --kb kb.vec.json --eval eval/sample_qa.yaml
```

## 知识卡片规范（data/skus/catalog.example.yaml）

每个 SKU 一张卡片：规格参数 / 核心卖点 / 适用场景 / 常见问题 FAQ / 售后政策 / 易混淆点。
**FAQ 与易混淆点是问答准确率的关键字段，必填。**

## 与客服系统集成

- 客服工作台：`rag.qa.answer()` 返回答案 + 引用 SKU 卡片，客服一键转发/编辑
- 直播话术辅助：同一知识库驱动「卖点速查」浮层
- 新员工培训：按卡片生成产品知识测验题

## 红线

- 答案必须带引用来源（SKU 卡片），无检索命中时明确回答「未找到相关资料」并转人工，**禁止编造参数**
