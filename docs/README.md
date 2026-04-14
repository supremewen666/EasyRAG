# Docs

The EasyRAG documentation is organized around the main learning path, with separate sections for methods and implementation details.

At a glance:

- Mainline: learn by stage
- Principles: learn by method
- Engineering: learn by implementation

Current status:

- `overview` focuses on stage-level mental models, inputs and outputs, and suggested learning paths
- `principles` focuses on general methods, without tying itself to specific file paths or repeating notebook navigation
- `engineering` focuses on implementation points, module relationships, and extension hooks, without repeating long method discussions
- Most pages under `principles` and `engineering` are still `draft/placeholder` pages, but they already follow the same template, which makes future expansion easier

## Mainline docs

- [00-overview.md](00-overview.md): project overview and best entry point
- [01-rag-basics.md](01-rag-basics.md): core RAG concepts and key objects, docs-only
- [02-data-loading-overview.md](02-data-loading-overview.md): loading and normalization before data enters the system
- [03-indexing-overview.md](03-indexing-overview.md): indexing stage overview
- [04-retrieval-overview.md](04-retrieval-overview.md): retrieval stage overview
- [05-generation-overview.md](05-generation-overview.md): generation stage overview
- [06-evaluation-overview.md](06-evaluation-overview.md): evaluation and problem diagnosis
- [07-optimization-overview.md](07-optimization-overview.md): optimization roadmap, currently docs-only
- [08-system-architecture-overview.md](08-system-architecture-overview.md): a system-level look back across the full stack

Notes:

- `01-rag-basics` remains a docs-only glossary and foundation page
- `07-optimization-overview` remains a docs-only roadmap
- `06-evaluation-overview` is part of the main path now, not just a supplemental section
- Several overview pages now explicitly include common production ideas such as normalization, metadata filtering, hybrid retrieval, reranking, latency/cost tradeoffs, and fallback

## Principles

- [10-query-preprocessing.md](principles/10-query-preprocessing.md)
- [11-chunking-strategies.md](principles/11-chunking-strategies.md)
- [12-vector-index-principles.md](principles/12-vector-index-principles.md)
- [13-hybrid-retrieval-and-fusion.md](principles/13-hybrid-retrieval-and-fusion.md)
- [14-reranking-and-selection.md](principles/14-reranking-and-selection.md)
- [15-knowledge-graph-for-rag.md](principles/15-knowledge-graph-for-rag.md)
- [16-storage-backends-and-tradeoffs.md](principles/16-storage-backends-and-tradeoffs.md)
- [17-top-k-and-candidate-selection.md](principles/17-top-k-and-candidate-selection.md)
- [18-context-assembly-and-packing.md](principles/18-context-assembly-and-packing.md)
- [19-prompting-and-answer-synthesis.md](principles/19-prompting-and-answer-synthesis.md)
- [20-generation-failures-and-guardrails.md](principles/20-generation-failures-and-guardrails.md)
- [21-evaluation-and-debugging.md](principles/21-evaluation-and-debugging.md)

Notes:

- `principles` follows the path from input to answer, then into evaluation and optimization
- generation-related topics are grouped together, with evaluation placed at the end so the reading path stays linear

## Engineering

- [20-code-map.md](engineering/20-code-map.md)
- [21-indexing-pipeline.md](engineering/21-indexing-pipeline.md)
- [22-retrieval-pipeline.md](engineering/22-retrieval-pipeline.md)
- [23-generation-pipeline.md](engineering/23-generation-pipeline.md)
- [24-graph-curation-pipeline.md](engineering/24-graph-curation-pipeline.md)
- [25-local-vs-production-backends.md](engineering/25-local-vs-production-backends.md)
- [26-extension-guide.md](engineering/26-extension-guide.md)

Notes:

- `engineering` starts with a code-level overview, then follows the runtime path, then covers system boundaries, and ends with extension points
- [20-code-map.md](engineering/20-code-map.md) is the main entry point for the engineering section, and the later pages assume you start there

## Teaching anchors

Current interfaces:

- `EasyRAG`
- `QueryParam`
- `ChunkingConfig`
- `QueryResult`

For now, downstream generation and answer-shaping work is still led mainly by the docs and notebooks rather than a built-in public API.
