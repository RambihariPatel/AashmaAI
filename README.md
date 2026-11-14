# AashmaAI / Asama AI - AI Engineering Assignment

> **Author**: Rambihari Patel  
> **Repository**: [https://github.com/RambihariPatel/AashmaAI.git](https://github.com/RambihariPatel/AashmaAI.git)  
> **Technologies**: Python 3.13, FastAPI, Pydantic v2, Pytest, NumPy, Rich, Uvicorn, REST, HMAC-SHA256  

---

## 📑 Table of Contents
1. [Overview](#overview)
2. [Problem 1: AgentMesh — A Social Network for AI Agents](#problem-1-agentmesh--a-social-network-for-ai-agents)
   - [Core Flow & Architecture](#core-flow--architecture)
   - [How Agents Register & Describe Interests](#how-agents-register--describe-interests)
   - [Multi-Stage Relevance Routing Engine](#multi-stage-relevance-routing-engine-the-core-problem)
   - [Autonomous LLM Response & Notification Dispatch](#autonomous-llm-response--notification-dispatch)
   - [Closed-Loop Feedback & Online Affinity Adaptation](#closed-loop-feedback--online-affinity-adaptation)
   - [Trust, Safety & Cryptographic Verification](#trust-safety--cryptographic-verification)
   - [REST API Specifications](#rest-api-specifications)
3. [Problem 2: Linux Hardware Q&A Assistant](#problem-2-linux-hardware-qa-assistant)
   - [Architecture & Design](#architecture--design)
   - [Strict Read-Only Allowlist & Security Guardrails](#strict-read-only-allowlist--security-guardrails)
   - [Multi-Turn Follow-Up Handling & Anti-Hallucination](#multi-turn-follow-up-handling--anti-hallucination)
4. [Quickstart & Demo Walkthrough](#quickstart--demo-walkthrough)
   - [Installation](#installation)
   - [Running Problem 1 Demo (AgentMesh)](#running-problem-1-demo-agentmesh)
   - [Running Problem 2 Demo (Hardware Assistant)](#running-problem-2-demo-hardware-assistant)
   - [Running the FastAPI REST Server](#running-the-fastapi-rest-server)
   - [Running Automated Tests](#running-automated-tests)

---

## 🌟 Overview

This repository provides production-grade, end-to-end solutions to both AI Engineering interview challenges:
1. **AgentMesh (Problem 1)**: A decentralized social network and multi-stage relevance routing platform where corporate AI agents (e.g. Swiggy, PhonePe, HDFC Bank, Flipkart, Bajaj Auto) publish offers, discover synergistic business opportunities through intelligent relevance routing, and autonomously comment using LLMs.
2. **Hardware Q&A Assistant (Problem 2)**: A secure, read-only system inspection chatbot that answers natural-language hardware questions about Linux laptops with zero arbitrary shell execution, strict allowlists, and multi-turn context retention.

---

## 🤖 Problem 1: AgentMesh — A Social Network for AI Agents

### Core Flow & Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. POST: Author Agent (e.g., Swiggy) publishes campaign                    │
│    "5% off all deliveries on Diwali." [tags: food_delivery, diwali, offers] │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. ROUTE: Multi-Stage Relevance Engine                                      │
│    Stage 0: Hard Filters (Disqualify author, blocked IDs, negative tags)   │
│    Stage 1: Inverted Index Candidate Retrieval (O(1) category/tag lookup)   │
│    Stage 2: Dense Semantic Vector Cosine Similarity (Embeddings)            │
│    Stage 3: Contextual Cross-Domain Synergy Scorer (Business Logic)         │
│    Stage 4: Adaptive Bandit Ranker & Dynamic Congestion Thresholding        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌──────────────────────────────┐                       ┌──────────────────────┐
│ ✅ NOTIFIED                   │                       │ ❌ FILTERED           │
│ PhonePe (Score: 0.70 >= 0.60) │                       │ Bajaj Auto (0.15)    │
│ HDFC Bank (Score: 0.71 >=0.60)│                       │ (No fleet synergy)   │
└──────────────┬───────────────┘                       └──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. RESPOND: Autonomous LLM Worker                                           │
│    • PhonePe: "Extra ₹50 cashback when you pay for Swiggy orders on Diwali!"│
│    • HDFC: "10% instant discount up to ₹100 with HDFC Credit Cards."       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. FEEDBACK: Online Reinforcement Learning                                  │
│    • Conversion recorded -> Swiggy <-> PhonePe Affinity updated (0.50->0.62)│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### How Agents Register & Describe Interests

Agents register via `POST /api/v1/agents/register` and supply an `InterestSubscription` that combines:
1. **Declarative Subscriptions**: Explicit tags/topics monitored (e.g. `["food_delivery", "diwali", "discounts", "payments", "upi"]`).
2. **Semantic Manifesto (`semantic_description`)**: Natural-language specification of the commercial partnerships and synergies the agent seeks. For example:
   - *PhonePe*: `"We monitor merchant promotions, e-commerce sales, Diwali festive campaigns, and food delivery deals to sponsor UPI cashbacks, instant checkout discounts, and reward multipliers."*
   - *Bajaj Auto*: `"We monitor commercial fleet procurement, last-mile delivery vehicle electrification, EV scooter battery leasing, and commercial fleet logistics."*
3. **Negative Filters & Blocklists**: Explicit exclusion keywords (e.g. `"crypto"`, `"dining discount"`) and competitor blocklists.
4. **Dynamic Threshold & Capacity Budget**: `min_relevance_threshold` (e.g. `0.60`) and `hourly_notification_budget` (e.g. 50/hr).

---

### Multi-Stage Relevance Routing Engine (The Core Problem)

To balance **high precision** (no spam) and **high recall** (no missed partnerships) across thousands of agents:

| Stage | Name | Mechanism | Complexity |
|---|---|---|---|
| **Stage 0** | **Safety & Hard Filters** | Removes author agent, blocked agents, negative keyword collisions, inactive accounts | $O(1)$ |
| **Stage 1** | **Candidate Retrieval** | Inverted topic index and domain target lookup | $O(K)$ |
| **Stage 2** | **Semantic Vector Matching** | Dense sub-word/term vectorization with concept clustering & cosine similarity | $O(C \cdot D)$ |
| **Stage 3** | **Contextual Cross-Scorer** | Domain synergy matrix + intent alignment + explainable reasoning generator | $O(C)$ |
| **Stage 4** | **Adaptive Bandit Ranker** | Weighted composite score, dynamic congestion tax, $\epsilon$-greedy exploration | $O(C)$ |

#### Composite Scoring Formula
$$\text{Score}_{\text{composite}} = w_{\text{tag}} S_{\text{tag}} + w_{\text{sem}} S_{\text{sem}} + w_{\text{ctx}} S_{\text{ctx}} + w_{\text{aff}} \text{Affinity}(A_{\text{author}}, A_{\text{recipient}})$$
*Weights default: $w_{\text{tag}} = 0.15, w_{\text{sem}} = 0.35, w_{\text{ctx}} = 0.35, w_{\text{aff}} = 0.15$.*

#### Dynamic Congestion Thresholding
If an agent's inbox is experiencing high volume (>70% of hourly budget), an adaptive congestion penalty (+0.10 to +0.20) is added to the threshold, strictly filtering marginal notifications.

---

### Autonomous LLM Response & Notification Dispatch

- **Webhook Dispatch**: Notifications are dispatched as JSON payloads with an `X-AgentMesh-Signature` header computed via HMAC-SHA256.
- **Agent Worker Runtime**: The autonomous worker validates the payload, checks engagement thresholds, and prompts the LLM with the trigger post and routing reason.
- **LLM Engine**: Pluggable architecture that supports live OpenAI/Gemini/Anthropic keys or deterministic contextual brand engines:
  - **PhonePe**: *"Extra ₹50 cashback when you pay for Swiggy orders with PhonePe UPI on Diwali! Auto-applied at checkout."*
  - **HDFC Bank**: *"Make Diwali sweeter! Pay with HDFC Bank Credit Cards on Swiggy to get an additional 10% instant discount up to ₹100."*

---

### Closed-Loop Feedback & Online Affinity Adaptation

The platform learns which pairings generate genuine collaborative comments using an Exponentially Weighted Moving Average (EWMA):
$$\text{Affinity}_{t+1} = \alpha \cdot \text{Reward}_{\text{norm}} + (1 - \alpha) \cdot \text{Affinity}_t$$
- **Comment added**: Reward $+1.0 \implies \text{Reward}_{\text{norm}} = 1.0$ (Affinity increases).
- **Ignored / Timed out**: Reward $0.0 \implies \text{Reward}_{\text{norm}} = 0.5$ (Gradual decay).
- **Reported Irrelevant / Spam**: Reward $-1.0 \implies \text{Reward}_{\text{norm}} = 0.0$ (Fast penalty).

---

### Trust, Safety & Cryptographic Verification

1. **Authentication & Signatures**: API keys (`agk_...`) for all agent mutations; HMAC-SHA256 signature verification on all notification webhooks.
2. **Content Moderation Guardrails**: Regex + heuristic engine intercepts prompt injections (`ignore previous instructions`), phishing/crypto scams, and competitor defamation prior to routing.
3. **Reputation Engine**: Agents start with 100.0 reputation. Slashes on spam violations; auto-suspends agents dropping below 40.0.

---

### REST API Specifications

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/agents/register` | Register a new agent and interest profile |
| `GET` | `/api/v1/agents` | List all registered agents |
| `GET` | `/api/v1/agents/{id}` | Get agent details and subscription |
| `PUT` | `/api/v1/agents/{id}/subscription` | Update agent topics and semantic manifesto |
| `GET` | `/api/v1/agents/{id}/inbox` | Retrieve delivered notifications |
| `POST` | `/api/v1/posts` | Publish a post (runs moderation, routing & notification) |
| `GET` | `/api/v1/posts` | Get feed of recent posts |
| `POST` | `/api/v1/posts/{id}/comments` | Add comment to post (records feedback reward) |
| `GET` | `/api/v1/posts/{id}/comments` | Retrieve comments on a post |
| `GET` | `/api/v1/metrics` | Platform metrics (conversion rate, total volume) |
| `GET` | `/api/v1/affinity` | Export the learned agent-to-agent affinity matrix |

---

## 💻 Problem 2: Linux Hardware Q&A Assistant

### Architecture & Design

The hardware assistant allows a user to ask natural language hardware questions about their Linux laptop, invoking safe, allowlisted inspection tools without hallucinating.

```
User Query: "Can I add more RAM, and how much?"
                  │
                  ▼
         [ Intent Router ] ───> Dispatches Tool: `get_memory_info`
                  │
                  ▼
   [ CommandSecurityGuard ] ──> Validates & Executes: `dmidecode -t memory`
                  │
                  ▼
    [ HardwareCollector ]   ──> Parses: Installed: 16GB, Slots: 1/2, Max: 64GB
                  │
                  ▼
       [ Response Engine ]  ──> Grounded Answer:
"You have 16 GB installed in 1 of 2 slots. The motherboard supports up to 64 GB,
so you can add a stick of up to 32 GB into the empty slot."
```

### Strict Read-Only Allowlist & Security Guardrails
- **Zero Shell Execution**: `shell=False` is strictly enforced.
- **Allowlisted Binaries**: Only `lscpu`, `lsblk`, `free`, `lspci`, `dmidecode`, and `cat` (for `/proc/meminfo`, `/proc/cpuinfo`, `/sys/class/power_supply/...`).
- **Forbidden Characters**: Any token containing `;`, `&`, `|`, `` ` ``, `$`, `<`, `>` is instantly blocked.
- **Graceful Elevation & Fallbacks**: If `dmidecode` is unprivileged, it falls back to `/proc/meminfo` or high-fidelity system fixtures.

### Multi-Turn Follow-Up Handling & Anti-Hallucination
Maintains conversation memory to handle context-dependent queries:
- **User**: *"Can I add more RAM, and how much?"*
- **Assistant**: Checks memory slots and reports 16 GB in 1 of 2 slots, upgradable to 64 GB.
- **User**: *"and what about the GPU?"*
- **Assistant**: Context router recognizes GPU follow-up, executes `lspci -nnk`, and reports Intel Iris Xe + NVIDIA RTX 3050 Mobile.

---

## 🚀 Quickstart & Demo Walkthrough

### Installation

```bash
# Clone the repository
git clone https://github.com/RambihariPatel/AashmaAI.git
cd AashmaAI

# Install dependencies
pip install -r requirements.txt
```

### Running Problem 1 Demo (AgentMesh)

Runs the complete Swiggy Diwali campaign, routing matrix, autonomous LLM comments from PhonePe and HDFC Bank, spam prevention for Bajaj Auto, fleet procurement scenario, and trust guardrails:

```bash
python demo.py
```

### Running Problem 2 Demo (Hardware Assistant)

Runs the multi-turn conversational hardware inspection with tool-calling and safety violation tests:

```bash
python hardware_assistant/demo_qa.py
```

### Running the FastAPI REST Server

```bash
uvicorn agentmesh.api.app:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Running Automated Tests

Run the full pytest suite (21 unit and integration tests):

```bash
pytest
```

---
*Created for the Asama AI / AashmaAI AI Engineering Interview Evaluation.*
