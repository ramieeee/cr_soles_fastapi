# cr_soles_fastapi

## Project Structure

```text
cr_soles_fastapi
├── alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── app/
│   ├── clients/
│   │   ├── embedding_client.py
│   │   ├── ollama_client.py
│   │   └── vllm_client.py
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── logger.py
│   │   └── security.py
│   ├── enums/
│   │   ├── common.py
│   │   ├── multimodal_extraction.py
│   │   └── paper_review.py
│   ├── langgraph/
│   │   ├── cr_extraction/
│   │   │   ├── graph.py
│   │   │   ├── nodes/
│   │   │   │   ├── next_page_node.py
│   │   │   │   ├── reduce_node.py
│   │   │   │   └── validation_node.py
│   │   │   └── state.py
│   │   └── multimodal_extraction/
│   │       ├── graph.py
│   │       ├── nodes/
│   │       │   ├── bibliographic_info_node.py
│   │       │   ├── embedding_node.py
│   │       │   └── ocr_node.py
│   │       └── state.py
│   ├── main.py
│   ├── models/
│   │   ├── agents_logs.py
│   │   ├── evaluations.py
│   │   ├── extractions.py
│   │   ├── papers_staging.py
│   │   └── papers.py
│   ├── prompts/
│   │   ├── common.py
│   │   ├── cr_extraction.py
│   │   └── multimodal_extraction.py
│   ├── repositories/
│   │   ├── agents_logs_repository.py
│   │   ├── evaluations_repository.py
│   │   ├── extractions_repository.py
│   │   ├── papers_repository.py
│   │   └── papers_staging_repository.py
│   ├── routers/
│   │   ├── cr_extraction_route.py
│   │   ├── multimodal_extraction_route.py
│   │   └── paper_review_route.py
│   ├── schemas/
│   │   ├── common.py
│   │   └── cr_extraction.py
│   ├── services/
│   │   ├── cr_extraction.py
│   │   ├── multimodal_extraction.py
│   │   └── paper_review.py
│   └── utils/
│       └── embedding.py
├── cloud_model_script.md
├── db_creation.sql
├── docker-compose.yaml
├── Dockerfile
├── logs/
│   └── app.log
├── pyproject.toml
├── README.md
├── requirements.txt
├── supabase/
│   └── config.toml
└── uv.lock
```

### Summary of Key Directories/Files

- `app/`: FastAPI Application
- `app/clients/`: External Service Clients (e.g., VLLM, Ollama)
- `app/utils/`: Shared Utility Functions
- `app/core/`: Core Application Logic (Config, DB, Logging, Prompts, Security)
- `app/enums/`: Enums for Different Modules
- `app/routers/`: API Endpoints
- `app/services/`: Business Logic
- `app/repositories/`: DB Access Layer
- `app/models/`: SQLAlchemy Models
- `app/schemas/`: Pydantic Schemas for DTO Validation
- `app/core/`: Configuration, DB, Logging, Security
- `app/langgraph/`: LangGraph Based Logic (Graphs, Nodes and States)
- `app/prompts/`: Prompt Templates for LLMs for each service
- `alembic/`, `alembic.ini`: DB Migration(Alembic)
- `docker-compose.yaml`, `Dockerfile`: Docker Container Ochestration
- `supabase/`: Supabase Related Files
- `logs/`: Application Logs

## VLLM Model Serving

So far we are using VLM (8B Qwen3-VL-8B-Instruct) for the multimodal extraction pipeline, Qwen3-Embedding-0.6B for embedding.

To serve VLLM models, see information below:

1. Platforms

- Runpod or vast.ai for GPU instances
- Choose GPU A40 (48GB) or better GPUs than A40. We need at least 48GB GPU memory

2. Install vLLM

- `pip install vllm`

3. Hugging Face Authentication

- `hf auth login`
- Use your Hugging Face token for authentication

4. Serve models, embedding model first

- For Qwen3-Embedding-0.6B:
  ```
  # For single GPU with limited memory usage:
  CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen3-Embedding-0.6B --port 8008 --gpu-memory-utilization 0.15
  ```
  ```
  # For multiple GPUs with tensor parallelism:
  CUDA_VISIBLE_DEVICES=0,1,2,3 vllm serve Qwen/Qwen3-Embedding-0.6B --port 8008 --gpu-memory-utilization 0.15 --tensor-parallel-size 4
  ```
- For Qwen3-VL-8B-Instruct:

  ```
  # For single GPU with limited memory usage:
  CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen3-VL-8B-Instruct --max-model-len 200000 --gpu-memory-util 0.8 --port 8000
  ```

  ```
  # For multiple GPUs with tensor parallelism:
  CUDA_VISIBLE_DEVICES=0,1,2,3 vllm serve Qwen/Qwen3-VL-8B-Instruct --max-model-len 200000 --tensor-parallel-size 4 --gpu-memory-util 0.8 --port 8000
  ```
