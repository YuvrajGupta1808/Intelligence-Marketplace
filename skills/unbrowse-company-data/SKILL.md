---
name: unbrowse-company-data
description: "Use the local Unbrowse server to fetch company and SEC/EDGAR data. Skills are created on first resolve and saved in this repo; sub-agents reuse them via the local registry (no cloud marketplace or API keys). Load this skill when any sub-agent needs SEC filings or site-specific company data."
---

# Unbrowse Company & SEC Data (local only)

This skill uses the **local** Unbrowse server (http://localhost:6969). The Unbrowse cloud marketplace and API keys are **not used**. The agent that first fetches company/SEC data creates a skill via resolve; the skill is **saved in this repo** (`registry.json` in this directory). Other sub-agents then use **get_unbrowse_registry** and **unbrowse_execute** so they never depend on the marketplace.

**LangChain integration:** This skill follows the [LangChain multi-agent skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills) pattern. The orchestrator and sub-agents use **list_skills** / **load_skill("unbrowse-company-data")** to get these instructions, then call the tools below.

## When to use

- You need **SEC.gov company filings** (10-K, 10-Q, EDGAR) for a ticker.
- You need **company or financial data** from a specific website that requires browser capture (e.g. broker pages, data sites).
- Another sub-agent may have already resolved the same intent and **registered** the skill in the repo; you then use **unbrowse_execute** with the stored `skill_id` and `endpoint_id` from **get_unbrowse_registry**.

## Workflow (required order)

1. **Load this skill**  
   Call **load_skill("unbrowse-company-data")** (you are following it now).

2. **Check the repo registry first**  
   Call **get_unbrowse_registry()**. If the response has an entry for the source you need (e.g. `source_label`: "SEC EDGAR") with `skill_id` and `endpoint_id`, use **unbrowse_execute(skill_id, endpoint_id, ...)** and skip resolve. No cloud; the local server will run the stored skill.

3. **If no matching entry: resolve and then register**  
   Call **unbrowse_resolve(intent, context_url=...)** with:
   - **intent**: e.g. `"SEC.gov company filings for [TICKER]"` or `"EDGAR company filings [TICKER]"`.
   - **context_url**: Required for first-time capture. Use the SEC URL below (replace `[TICKER]` with the ticker, e.g. AAPL).
   From the resolve response, take `skill_id` and `endpoint_id`. Then:
   - Call **register_unbrowse_skill(skill_id, endpoint_id, intent, source_label)** so the skill is **saved in the repo** (e.g. source_label `"SEC EDGAR"`). Sub-agents will then find it via get_unbrowse_registry.
   - Call **unbrowse_execute(skill_id, endpoint_id, path?, extract?, limit?)** as needed.
   - Call **unbrowse_feedback(skill_id, endpoint_id, rating, outcome)** after presenting results.

4. **Execute and refine**  
   Use **unbrowse_execute(skill_id, endpoint_id, path?, extract?, limit?)** to get or refine data. Use `path` and `extract` if the API returns extraction_hints.

5. **Feedback**  
   After presenting Unbrowse results, call **unbrowse_feedback(skill_id, endpoint_id, rating, outcome)** (rating 1–5, outcome `"success"` or `"failure"`).

## Intent and context_url (SEC/EDGAR)

| Source     | Intent example                      | context_url template |
|------------|--------------------------------------|----------------------|
| SEC EDGAR  | SEC.gov company filings for [TICKER] | `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=[TICKER]&type=10-K&dateb=&owner=include&count=40` |
| EDGAR      | EDGAR company filings [TICKER]        | Same as above |

Replace `[TICKER]` with the actual ticker (e.g. AAPL, MSFT, NVDA). For numeric CIK, you may use the CIK number in the URL if known.

## Tools

| Tool | Purpose |
|------|--------|
| **get_unbrowse_registry()** | Read skills saved in the repo. Use first; if there is a matching source, use returned skill_id/endpoint_id with unbrowse_execute. |
| **unbrowse_resolve(intent, url?, context_url?, dry_run?)** | Resolve intent on the **local** server; pass **context_url** for first-time capture (e.g. SEC). |
| **register_unbrowse_skill(skill_id, endpoint_id, intent, source_label)** | **Save** this skill in the repo after a successful resolve so sub-agents can reuse it. |
| **unbrowse_execute(skill_id, endpoint_id, path?, extract?, limit?, ...)** | Run a known skill (from registry or from resolve response). |
| **unbrowse_feedback(skill_id, endpoint_id, rating, outcome)** | Submit after presenting results. |
| **unbrowse_list_skills()** / **unbrowse_skill_detail(skill_id)** | Optional: inspect what the local server has. |

## Local registry (repo)

- **Path:** `skills/unbrowse-company-data/registry.json`
- **Content:** List of `{ "skill_id", "endpoint_id", "intent", "source_label" }` for skills created by resolve and saved with register_unbrowse_skill. One entry per source_label (e.g. one "SEC EDGAR" entry). Sub-agents use this so they do not call resolve when a skill is already in the repo.

## Notes

- Unbrowse **local** server must be running (`unbrowse setup` or `npx unbrowse setup`). If it is unavailable, use **live_finance_researcher** for company data.
- No cloud marketplace or API keys are required; all skills are created and reused locally and stored in the repo.
