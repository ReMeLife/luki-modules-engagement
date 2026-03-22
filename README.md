# luki-modules-engagement

> **This repository is archived.** Active development continues in a private repository. This public version reflects the ReMeLife integration era and is no longer maintained.

Community engagement module for LUKi. Builds social/interest graphs, matches users to events and peers, and tracks interaction metrics.

## What It Does

- Builds a social-interest graph from user profiles, events, and interactions (NetworkX)
- Matches users to events and peers by shared interests
- Ranks recommendations using engagement history and recency weighting
- Computes graph metrics (centrality, community detection)
- Tracks interaction frequency and engagement scores
- Exposes all functions as callable tools for the LUKi agent

## Stack

- **Graph:** NetworkX
- **API:** FastAPI
- **Data Models:** Pydantic, SQLAlchemy
- **HTTP:** httpx for async service calls
- **Deployment:** Docker on Railway

## Structure

```
luki_modules_engagement/
├── main.py                  # FastAPI app, all endpoints
├── config.py                # Service configuration
├── database.py              # Database session management
├── models.py                # SQLAlchemy models (interactions, profiles, metrics)
├── data/
│   ├── loaders.py           # Data ingestion from ELR and event feeds
│   └── schemas.py           # Pydantic models for users, events, interactions
├── graph/
│   ├── build_graph.py       # Graph construction from user/event data
│   ├── metrics.py           # Centrality, community detection, scoring
│   └── store.py             # Graph persistence (NetworkX adapter)
├── recommend/
│   ├── matcher.py           # Interest and event matching
│   ├── ranker.py            # Hybrid scoring and re-ranking
│   └── explainer.py         # Match explanation generation
└── interfaces/
    ├── agent_tools.py       # Functions exposed to LUKi agent
    └── api.py               # Additional API routes
```

## Setup

```bash
git clone git@github.com:ReMeLife/luki-modules-engagement.git
cd luki-modules-engagement
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn luki_modules_engagement.main:app --reload --port 8102
```

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/recommendations/{user_id}` | Social recommendations |
| GET | `/graph/{user_id}` | User graph connections |
| POST | `/interactions/track` | Record an interaction |
| GET | `/metrics/{user_id}` | Engagement metrics |
| GET | `/health` | Service health |

## License

Apache License 2.0. Copyright 2025 Singularities Ltd / ReMeLife. See [LICENSE](LICENSE).
