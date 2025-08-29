# luki-modules-engagement  
*Community graph, interest matching & event recommendations for ReMeLife*

---

## License

This project is licensed under the [Apache 2.0 License with ReMeLife custom clauses]

---

## 1. Overview
This module powers **ReMeComm**: AI-driven community engagement inside the ReMeLife ecosystem.  
It builds and queries a **social/interest graph** to connect members with events, groups, products, and peers that match their ELR® profiles and current needs.

---

## 2. Core Capabilities
- **Interest & Demographic Matching** – Link users, carers, charities, and services by shared themes.  
- **Event / Group Recommendations** – Rank local or virtual activities for relevance & accessibility.  
- **Social Graph Analytics** – Centrality, community detection, and “who should you talk to?” prompts.  
- **Engagement Scoring** – Track and surface meaningful interactions (forum posts, chats, purchases).  
- **APIs for LUKi Agent** – Callable tools so the agent can suggest connections or post invites.

---

## 3. Tech Stack
- **Graph DB / Analysis:** NetworkX (default), Neo4j adapter optional  
- **Embeddings:** `sentence-transformers` for interest vectors  
- **Ranking:** scikit-learn / LightFM / custom heuristics  
- **Orchestration:** LangChain tools to expose matchers to the LUKi agent  
- **Data Handling:** pandas for ETL; pydantic for typed payloads

---

## 4. Repository Structure
~~~text
luki_modules_engagement/
├── __init__.py
├── config.py
├── data/
│   ├── loaders.py               # ingest ELR slices, forum logs, event feeds
│   └── schemas.py               # pydantic models for users/events
├── graph/
│   ├── build_graph.py           # create/update social-interest graph
│   ├── metrics.py               # centrality, community detection
│   └── store.py                 # Neo4j/NetworkX adapter
├── recommend/
│   ├── matcher.py               # interest/event matching logic
│   ├── ranker.py                # hybrid scoring & re-ranking
│   └── explainer.py             # "why this match?" reasons
├── interfaces/
│   ├── agent_tools.py           # LangChain @tool wrappers
│   └── api.py                   # FastAPI endpoints (optional)
└── tests/
~~~

---

## 5. Quick Start
~~~bash
git clone git@github.com:REMELife/luki-modules-engagement.git
cd luki-modules-engagement
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
~~~

### Index sample data
~~~python
from luki_modules_engagement.data.loaders import load_demo_users, load_demo_events
from luki_modules_engagement.graph.build_graph import GraphBuilder

users = load_demo_users()
events = load_demo_events()

gb = GraphBuilder()
gb.build(users, events)     # create graph
gb.persist("graph_store.pkl")
~~~

### Recommend connections
~~~python
from luki_modules_engagement.recommend.matcher import Matcher
from luki_modules_engagement.graph.store import LocalGraphStore

store = LocalGraphStore("graph_store.pkl")
matcher = Matcher(store)

recs = matcher.recommend_events(user_id="user_123", k=5)
for r in recs:
    print(r.title, r.score)
~~~

### Expose as LangChain tools
~~~python
# interfaces/agent_tools.py
from langchain.tools import tool
from .recommend.matcher import Matcher
from .graph.store import LocalGraphStore

_store = LocalGraphStore("graph_store.pkl")
_matcher = Matcher(_store)

@tool("recommend_events", return_direct=True)
def recommend_events(user_id: str) -> str:
    """Return top 3 events/groups for a user."""
    recs = _matcher.recommend_events(user_id=user_id, k=3)
    return "\n".join(f"{r.title} ({r.score:.2f})" for r in recs)
~~~

---

## 6. Privacy & Consent
- Only ingest **consented ELR fields** (interests, hobbies, non-sensitive tags).  
- Strip identifiers before analytics; keep IDs in a secure mapping layer.  
- Encrypt graph exports; never push real user graphs to public repos.

---

## 7. Roadmap
- Multi-criteria ranking (availability, mobility, cognitive load)  
- Geo-aware matching (distance, transport options)  
- Temporal sequencing (“this week’s picks”)  
- Automatic micro-community formation (community detection)  
- Federated engagement scoring to avoid centralising raw logs

---

## 8. Contributing
Public contributions welcome. Follow `CONTRIBUTING.md`, run tests, and keep docs updated.

---

## 9. License
**Apache-2.0** © 2025 Singularities Ltd / ReMeLife.  
(Add via GitHub “Choose a license template” or paste the standard Apache-2.0 text in `LICENSE`.)

---

**Connect the care community. Reduce isolation. Amplify engagement.**
