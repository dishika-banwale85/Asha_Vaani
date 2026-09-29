# ASHA VAANi — Production Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ASHA WORKER (PWA)                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │   Chat UI   │  │ Voice Pipeline│  │ Offline Triage│  │  Profile/Dash  │   │
│  │  (Streaming) │  │  (STT→LLM→TTS)│  │  (Deterministic)│  │  (GPS/Map)    │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘   │
│         │                │                │                   │            │
│         └────────────────┼────────────────┼───────────────────┘            │
│                          ▼                                                │
│              ┌─────────────────────┐                                     │
│              │  Service Worker     │                                     │
│              │  (Cache + Sync)     │                                     │
│              └──────────┬──────────┘                                     │
└─────────────────────────┼────────────────────────────────────────────────┘
                          │ HTTPS / WSS
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (FastAPI)                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐   │
│  │  Auth    │ │  Chat    │ │  Voice   │ │  Admin   │ │  Geo/Location  │   │
│  │  (JWT)   │ │  (SSE)   │ │  (WS)    │ │  (RBAC)  │ │  (OSM/Govt)    │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬────────┘   │
│       │            │            │            │                │            │
│       └────────────┼────────────┼────────────┼────────────────┘            │
│                    ▼            ▼            ▼                             │
│         ┌─────────────────────────────────────────────┐                   │
│         │           SERVICE LAYER                      │                   │
│         │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │                   │
│         │  │  RAG    │ │  Triage │ │  Audit  │        │                   │
│         │  │ Service │ │ Engine  │ │ Service │        │                   │
│         │  └────┬────┘ └────┬────┘ └────┬────┘        │                   │
│         └───────┼───────────┼───────────┼──────────────┘                   │
└─────────────────┼───────────┼───────────┼──────────────────────────────────┘
                  │           │           │
        ┌─────────┘    ┌──────┘    ┌─────┘
        ▼              ▼           ▼
┌───────────────┐ ┌─────────┐ ┌──────────────┐
│  Vector DB    │ │ SQLite  │ │  Audit Log   │
│  (Chroma/Mil- │ │ (Encrypted)│  (Append-only)│
│   vus)        │ │         │ │  (WAL + Sig) │
└───────────────┘ └─────────┘ └──────────────┘
```

## Core Components

### 1. Security & Privacy Layer
- **Encryption**: AES-256-GCM for PII at rest; TLS 1.3 in transit
- **Key Management**: AWS KMS / HashiCorp Vault / local Fernet for dev
- **Consent**: Explicit opt-in per data category (patient, audio, analytics)
- **RBAC**: Roles = `asha`, `supervisor`, `admin` with scoped permissions
- **Audit**: Append-only WAL + HMAC-SHA256 chaining; tamper-evident

### 2. RAG Pipeline (Online)
```
Query → Query Expansion (Hindi/Hinglish) → Hybrid Retrieval (BM25 + Semantic)
                                              │
                                              ▼
                                    CrossEncoder Rerank (top-50 → top-8)
                                              │
                                              ▼
                              Confidence Scoring (retrieval + LLM + rules)
                                              │
                                              ▼
                              Context Assembly (token budget + citations)
                                              │
                                              ▼
                              LLM (Groq primary, Gemini fallback) → Streaming
```

### 3. Offline-First Architecture
- **Service Worker**: App shell + assets + quantized vector index (ONNX, ~5MB)
- **IndexedDB**: Offline logs, pending referrals, patient notes, triage results
- **Background Sync**: `BackgroundSync API` + custom conflict resolution
- **Local Triage**: Deterministic decision tree (protocol_engine.js) — zero-LLM

### 4. Voice Pipeline (Target: <1.5s STT, <500ms TTS start)
```
Mic → WebRTC/VAD → STT (Whisper.cpp on-device OR Groq cloud fallback)
                                    │
                                    ▼
                              Intent Detection → RAG → LLM (streaming)
                                    │
                                    ▼
                              TTS (Piper/Coqui on-device OR ElevenLabs cloud)
                                    │
                                    ▼
                              Audio Stream → Speaker
```

### 5. Data Models

#### User (Encrypted PII)
```python
User: {
  id: UUID (PK),
  username_hash: str,          # bcrypt
  email_hash: str,             # SHA-256 salted
  role: Enum[asha, supervisor, admin],
  profile_enc: bytes,          # AES-256-GCM encrypted JSON
  consent_version: int,
  consent_flags: ConsentFlags, # patient_data, audio, analytics
  created_at: datetime,
  last_login: datetime,
  pin_hash: str | None,        # bcrypt, for offline fallback
}
```

#### Chat Log (Audit)
```python
ChatLog: {
  id: UUID (PK),
  user_id: UUID (FK),
  session_id: UUID,
  query: str,
  retrieval_chunks: ChunkRef[],  # chunk_id, score, page, para
  llm_response: str,
  confidence: ConfidenceScore,
  sources: SourceCitation[],
  flags: SafetyFlags,            # hallucination_risk, referral_triggered
  latency_ms: int,
  model_used: str,
  created_at: datetime,
  hash_chain: str,               # HMAC(prev_hash + payload)
}
```

#### Referral (Immutable)
```python
ReferralLog: {
  id: UUID (PK),
  asha_id: UUID,
  patient_hash: str,             # salted hash of minimal ID
  danger_signs: list[str],
  triage_result: TriageResult,
  phc_id: str,
  phc_distance_km: float,
  status: Enum[pending, acknowledged, completed],
  created_at: datetime,
  synced_at: datetime | None,
  hash_chain: str,
}
```

## Deployment Topology

| Environment | Compute | Vector DB | SQL | Secrets | Observability |
|-------------|---------|-----------|-----|---------|---------------|
| **Dev** | Docker Compose | Chroma (local) | SQLite (encrypted) | .env | stdout + Loki |
| **Staging** | ECS Fargate / K8s | Milvus Standalone | PostgreSQL + pgcrypto | AWS Secrets Manager | Prometheus + Grafana + Tempo |
| **Prod** | EKS/GKE (multi-AZ) | Milvus Cluster | PostgreSQL (read replica) | Vault + KMS | Full stack + alerting |

## Non-Functional Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Median retrieval latency | <1.5s | p50 /chat endpoint |
| End-to-end answer (cached) | <3s | p90 |
| End-to-end answer (cold) | <8s | p90 |
| STT latency (on-device) | <1.5s | p95 |
| TTS first audio | <500ms | p95 |
| Offline triage decision | <100ms | p99 |
| Availability (core) | 99.9% | Uptime monitor |
| Guideline-consistent accuracy | ≥90% | Golden set eval |
| Danger-sign false negative | <1% | Golden set eval |

## Cost Optimization Levers

| Lever | Est. Savings |
|-------|--------------|
| Semantic caching (exact + fuzzy) | 30–50% LLM calls |
| Small model (Gemma-2B) for simple Q&A | 80% token cost |
| Quantized local embeddings (offline) | 100% embedding cost offline |
| Request batching (async) | 20% infra cost |
| Spot instances for batch jobs | 60–70% compute |

---

## Implementation Phases

| Phase | Focus | Deliverables |
|-------|-------|--------------|
| **1** | Security/Privacy | Encryption, consent, RBAC, audit, PII hashing |
| **2** | RAG Hardening | Proper chunking, medical embeddings, BM25, confidence, hallucination guard |
| **3** | Streaming + Voice | SSE chat, WebSocket voice, on-device STT/TTS, Hindi/dialect |
| **4** | Offline RAG | Quantized index, background sync, conflict resolution |
| **5** | Observability + Deploy | Docker, k8s, logging, metrics, tracing, CI/CD |
| **6** | Benchmark + Optimize | Golden set, eval pipeline, cost dashboards |