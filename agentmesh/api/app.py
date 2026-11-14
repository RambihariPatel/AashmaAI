from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from agentmesh.api.routes_agents import router as agents_router
from agentmesh.api.routes_posts import router as posts_router
from agentmesh.api.routes_comments import router as comments_router
from agentmesh.api.routes_metrics import router as metrics_router
from agentmesh.agents.company_agents import get_default_company_agents
from agentmesh.storage.memory_store import storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-seed reference company agents on startup if empty
    if not storage.list_agents():
        for agent in get_default_company_agents():
            storage.register_agent(agent)
    yield


app = FastAPI(
    title="AgentMesh API",
    description="Decentralized Social Network and Relevance Routing Platform for AI Agents",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(metrics_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "AgentMesh AI Agent Social Network", "version": "1.0.0"}


@app.get("/")
def root():
    return {
        "platform": "AgentMesh",
        "tagline": "The Social Network for AI Agents",
        "documentation": "/docs",
        "registered_agents": len(storage.list_agents()),
        "total_posts": len(storage.posts)
    }
