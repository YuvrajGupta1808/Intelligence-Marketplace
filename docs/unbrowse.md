# Unbrowse for Deep Agents: Local-Only Skills in the Repo

A guide to **what Unbrowse is**, how to use it inside a **deep research agent**, and how **skills are created and reused** by other agents or sub-agents. No custom “skill code” is required — Unbrowse creates and stores skills automatically.

**Local-only; no marketplace.** This project uses only the local Unbrowse server. The cloud marketplace and API keys are not used. Skills are saved in the repo (**skills/unbrowse-company-data/registry.json**). After a successful resolve, the agent calls **register_unbrowse_skill**; other sub-agents use **load_skill("unbrowse-company-data")** and **get_unbrowse_registry()**, then **unbrowse_execute** when the registry has a matching source (e.g. SEC EDGAR).

**Flow:** (1) Local server at localhost:6969. (2) First agent calls unbrowse_resolve → register_unbrowse_skill (saves to repo). (3) Other sub-agents: get_unbrowse_registry() → unbrowse_execute(skill_id, endpoint_id) when match. See **skills/unbrowse-company-data/SKILL.md** and [LangChain multi-agent skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills).

---

## 1. What is Unbrowse?

**Unbrowse** is an **API-native browser** for AI agents. It does not work like a classic web crawler (e.g. Firecrawl) or a search API (e.g. Tavily). Its job is:

1. **Capture** — Visit a real site in a headless browser and record all network traffic (XHR/fetch, API calls).
2. **Discover** — Reverse-engineer that traffic into structured endpoints (URL, method, headers, typical responses).
3. **Publish** — Save that as a reusable **skill** in a **shared marketplace** (e.g. `beta-api.unbrowse.ai`).
4. **Replay** — Later, any agent can call the same intent; Unbrowse finds the skill and **replays the HTTP calls** (no browser, no re-capture).

So: **one agent (or user) triggers a capture once → a skill is created and stored → every agent can reuse it.**  
You do **not** hand-write “skills”; Unbrowse creates them from live traffic.

| Concept | Meaning |
|--------|---------|
| **Intent** | Natural-language goal, e.g. “get Airbnb listing details for Tokyo”. |
| **Skill** | Learned set of endpoints + how to call them, stored in the marketplace. |
| **Capture** | First-time visit: browser runs, traffic is recorded, skill is generated and published. |
| **Replay** | Subsequent calls: marketplace skill is executed (HTTP only), no browser. |

**Local setup:** Unbrowse runs as a local service (default `http://localhost:6969`). You install it (`npm install -g unbrowse@latest`), run `unbrowse setup`, and your agents talk to it via HTTP (e.g. `POST /v1/intent/resolve`). To store skills in Unbrowse's shared marketplace (your account), set `UNBROWSE_API_KEY` in your `.env` to your Unbrowse API key; the app will send it as the Bearer token with every request.

**Skills on the web dashboard:** The dashboard at [unbrowse.ai](https://www.unbrowse.ai/dashboard) shows "Skills Discovered" and "Total Executions" for **one agent**. The app sends the value of `UNBROWSE_API_KEY` as the Bearer token; Unbrowse attributes all requests to the agent that owns that key. If the dashboard shows 0:

1. **Use the key for the agent you are viewing.** On the dashboard, find **Agent ID** (e.g. `key_sPHpB36n`). Set in `.env`: `UNBROWSE_API_KEY="key_sPHpB36n"` (use your dashboard’s value). If you use a different key (e.g. another `ubr_...` key), activity is attributed to a different agent and will not show on this dashboard.
2. **Verify which agent the current key is for:** run `uv run python scripts/check_unbrowse_agent.py`. It calls the Unbrowse server with your current key and, if supported, prints the agent info. Compare with the Agent ID on the dashboard.
3. **Trigger activity:** run `uv run python scripts/test_unbrowse_marketplace.py` or a full research (e.g. "Research AAPL") so the app calls resolve/execute. Then refresh the dashboard.
4. If the dashboard still shows 0, the local server may not report metrics to the cloud for your setup; check Unbrowse’s docs or support.

---

## 2. Using Unbrowse for Real-Time, Problem-Solving Agents

### 2.1 Single-shot: “Answer this from the web”

Your agent sends one intent + URL; Unbrowse either finds a matching skill (fast) or captures the site (slower once), then returns data.

- **Real-time:** After the first capture, replays are fast (tens or hundreds of ms).
- **Problem-solving:** The “problem” is “get structured data from this site”; Unbrowse solves it by learning the site’s API and returning JSON (or DOM-derived structure).

Example flow:

1. User: “What are the top stays in Paris on Airbnb?”
2. Agent calls Unbrowse: `POST /v1/intent/resolve` with intent = “get top stays in Paris on Airbnb”, params.url = `https://www.airbnb.com/s/Paris`.
3. Unbrowse searches marketplace → if no skill, captures Airbnb → publishes skill → returns data.
4. Agent uses that data to answer the user.

### 2.2 Deep research: Multi-step and chaining

A **deep research agent** can use Unbrowse as one of its tools and chain multiple steps:

1. **Plan** — Break the research into sub-questions (e.g. “Airbnb Paris”, “reviews for listing X”, “availability”).
2. **Resolve** — For each sub-question, call `POST /v1/intent/resolve` with a clear intent and the right URL. Unbrowse handles “do I have a skill?” and “do I need to capture?”.
3. **Synthesize** — Combine results (and other tools: search, code, etc.) into a final answer or report.

Real-time and problem-solving here mean:

- **Real-time:** Data comes from live sites (and from the latest skill execution), not from a static crawl.
- **Problem-solving:** Each intent is a sub-problem (“get listing details”, “get reviews”); Unbrowse solves it by skill replay or capture.

Pattern for your orchestrator:

- Maintain a list of “research steps” (intent + URL).
- For each step, call Unbrowse; on success, feed the result into the next step or into the LLM for synthesis.
- Optionally implement retries, timeouts, and fallbacks (e.g. “if Unbrowse fails, use a different source”).

---

## 3. How Skills Are Created and Who Uses Them

### 3.1 Creation (automatic)

- **You do not** write skill definitions by hand.
- When **any** client (Agent 1, your app, the CLI) calls `POST /v1/intent/resolve` with an intent and URL and **no matching skill exists**, Unbrowse:
  - Runs a **live capture** (headless browser).
  - Infers **endpoints** from traffic.
  - **Publishes** the new skill to the **shared marketplace**.
- So “creating a skill” = “triggering a first-time resolve” for that intent/URL. No extra API call is needed.

### 3.2 Reuse by other agents or sub-agents

- The marketplace is **shared** (e.g. across machines using the same Unbrowse backend / same cloud).
- **Any** agent or sub-agent that calls `POST /v1/intent/resolve` with a **similar intent** (semantic match) will:
  - Get a **marketplace hit** if a skill exists.
  - **Replay** that skill (HTTP only), without opening a browser.

So:

- **Agent 1** (or “research sub-agent”) does: resolve “get Airbnb listing details for Tokyo” → Unbrowse captures, creates and saves the skill.
- **Agent 2** (or another sub-agent) later does: resolve “get Airbnb listing details” or “search Airbnb Tokyo” → Unbrowse finds the same skill and runs it for Agent 2.

No separate “share skill” or “export skill” step is required. Same Unbrowse service + same marketplace = shared skills.

### 3.3 Design for sub-agents

- **Orchestrator** — Decides the research plan and which intents/URLs to call.
- **Sub-agents** — Each can call Unbrowse with an intent + URL. The first sub-agent to trigger a new intent causes a capture and skill creation; others reuse the skill.
- **Shared backend** — Point all agents/sub-agents at the same Unbrowse URL (and thus same marketplace) so they all see the same skills.

---

## 4. Do You Need to “Create Skills” or Just a .md File?

- **You do not need to create skills yourself.** Unbrowse creates and stores them when a capture runs. Your job is to:
  - Build an agent (orchestrator + sub-agents) that **calls** Unbrowse with good intents and URLs.
  - Optionally document your agent’s behavior and how it uses Unbrowse (e.g. this .md file).

- **A single .md file (like this one)** is enough to explain:
  - What Unbrowse is.
  - How to use it for real-time, problem-solving, deep research.
  - How skills are created and reused by other agents/sub-agents.

So: **use a proper .md guide** (and optionally a Cursor/Codex “skill” that points at it) so that anyone building the deep agent knows how Unbrowse fits in. **Do not** implement custom “skill” code for Unbrowse’s marketplace — Unbrowse handles that.

---

## 5. Where to see skills

- **From the agent:** Ask the agent to list Unbrowse skills, e.g. *"List Unbrowse skills"*. The agent will call the `unbrowse_list_skills` tool and show you the skills stored in the Unbrowse marketplace (created on first resolve/capture).
- **From Unbrowse:** If Unbrowse provides a dashboard or API to list skills (e.g. at the Unbrowse cloud or local URL), you can use that to inspect skills directly; see Unbrowse’s documentation for the current URL.

---

## 6. Quick Reference: API and Flow

- **Health:** `GET http://localhost:6969/health`
- **Resolve (main entry):**  
  `POST http://localhost:6969/v1/intent/resolve`  
  Body: `{ "intent": "…", "params": { "url": "https://…" }, "context": { "url": "https://…" } }`
- **Auth (gated sites):** `POST /v1/auth/login` with `url` (and optionally `yolo: true` for Chrome session).
- **List skills:** `GET /v1/skills`
- **Execute a known skill:** `POST /v1/skills/{skill_id}/execute` with `params`.

For deep research, the main integration point is **intent/resolve**: the orchestrator (or sub-agents) sends intents and URLs; Unbrowse takes care of skill lookup, capture, publish, and replay.

---

## 7. Summary

| Question | Answer |
|----------|--------|
| What is Unbrowse? | API-native browser: capture site traffic → discover APIs → skill can be replayed. |
| Does this project use the cloud marketplace? | **No.** Local server only; skills are saved in the repo (registry.json). |
| How are skills created? | First resolve (with context_url) on the local server; then **register_unbrowse_skill** saves skill_id/endpoint_id in skills/unbrowse-company-data/registry.json. |
| How do sub-agents reuse them? | **get_unbrowse_registry()** → if matching source (e.g. SEC EDGAR), **unbrowse_execute(skill_id, endpoint_id)**. No resolve needed. |
| Do you need API keys? | No. Local server works without UNBROWSE_API_KEY; marketplace/dashboard are not used. |

Use this document as the single source of truth for integrating Unbrowse into your deep agent and for understanding how skills are created and shared across agents and sub-agents.
