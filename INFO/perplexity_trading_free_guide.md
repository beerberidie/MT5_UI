
# Perplexity AI for Day Traders — **Zero‑Cost Master Guide**
*Last updated: 2 Oct 2025 (GMT+2)*

---

## 1 Why use Perplexity AI in trading?

Perplexity is a real‑time answer engine that reads the open web on demand and lets you ask follow‑up questions inside the same thread (“Space”).  
For a day‑trader, that means:

* **Instant context** – condenses macro headlines, Fed speeches, and breaking news into bullet points.
* **Cited sources** – every fact is hyper‑linked so you can verify the claim before risking capital.
* **Thread memory** – each Space turns into a mini research notebook you can clone or search later.
* **API access** – even the free Tier‑0 key lets you script daily routines without paying a cent.

---

## 2 Features that are _completely_ free & **unlimited**

| Free Feature | Practical trading use‑case | Why it matters |
|--------------|---------------------------|----------------|
| **Quick / Basic searches** | “When does CME gold pit reopen after the Monday halt?” | Unlimited, no quotas. |
| **Spaces (thread history)** | Save a daily “XAU Playbook” Space; clone it tomorrow. | Becomes a searchable trade journal. |
| **Public‑URL context** | Paste a TradingView chart, FRED series, or news article into the prompt. | Adds external data without extra quota. |
| **Browser / mobile ‘highlight → summarise’** | One‑click headline condensing during the session. | Zero cost, zero quota usage. |
| **API Tier‑0 key** | Cron‑job pulls for economic calendar at 07:00 SA time. | Rate‑limited but free; no credit card required. |

> **Tip:** Chain multiple follow‑ups in the same Space; each is still **free** while you stay on Quick search mode.

---

## 3 Free—**but capped** (resets every 24 h)

| Item | Daily allowance | Smart usage tip |
|------|-----------------|-----------------|
| **Pro searches** | 3–5 | Draft your long prompt offline, then paste once. |
| **Deep‑Research jobs** | 3 | Reserve for weekly macro deep‑dives. |
| **File uploads / images** | 3 per day *(+5 per Space)* | Combine multiple screenshots into a single PDF before upload. |

---

## 4 Zero‑rand daily workflow (example timeline)

| SA Time | Action | Free Perplexity prompt | Quota used |
|---------|--------|------------------------|------------|
| **06:30** | Pre‑market scan | “List every high‑impact economic release in the next 12 h that historically moves XAU USD by ≥ 0.5 %. Return GMT+2 times.” | Quick (unlimited) |
| **09:00** | Opening range sentiment | “Give me a 5‑line sentiment snapshot for US30, DAX, BTC based on the last 100 Reuters & Bloomberg headlines.” | Follow‑up (still Quick) |
| **10:15** | Plan the day’s trade | “Using only today’s releases and last Friday’s CFTC positioning, outline three bullish and three bearish catalysts for gold.” | Switch to **1 × Pro** if deeper reasoning needed |
| **12:45** | News spike reaction | Highlight article → *Summarise → ‘Probable effect on risk‑on vs risk‑off’*. | Extension (free) |
| **17:05** | Post‑trade review | Upload CSV of the day’s trades → “Find patterns that explain my –R240 drawdown; rank the top 3.” | **1 × File upload** + (optional) **1 × Pro** |

---

## 5 Automating with the free API

```bash
# Cron example: fetch macro calendar every morning
curl -G 'https://api.perplexity.ai/search'      -d 'q=High+impact+economic+events+today+GMT%2B2'      -d 'autocomplete=false'      -H 'Authorization: Bearer YOUR_TIER0_KEY'
```

1. **Store JSON** → Google Sheets (`IMPORTJSON`) or local CSV.  
2. **Trade bot** reads sheet → posts to Discord at market open.  
3. **Cache answers** to avoid re‑asking the same question and hitting the rate‑limit.

---

## 6 Reusable prompt templates

```text
### 6.1 Market‑Moving Events
Act as an economic calendar bot. Time zone = GMT+2.
Return a table: {Time | Release | Consensus | Previous | Typical Asset Impact}

### 6.2 Scenario Matrix
You are a cross‑asset strategist. Build a 2×2 bull/bear matrix for {TICKER}.
Columns = Growth outlook (Strong/Weak); Rows = Fed stance (Dovish/Hawkish).
Output: bullet points + probability %.

### 6.3 Trade Audit
You are a quantitative performance coach. Given the attached CSV of trades,
– Compute win‑rate, average RR, largest intraday drawdown.
– List top 3 mistakes ranked by dollar impact.
```

Save each template inside a dedicated Space; clone the Space daily and only change the date.

---

## 7 Advanced tricks that _stay_ free

| Trick | Method | Benefit |
|-------|--------|---------|
| **Thread cloning** | Duplicate yesterday’s Space, change the date. | Re‑use past context with zero quota. |
| **Cross‑account sharing** | A friend runs their Deep‑Research query, then sends you the Space URL. | Crowdsources around your daily cap. |
| **Local LLM combo** | Run Llama‑3 8‑B in LM Studio for heavy maths; use Perplexity only when you need live web access. | Saves Pro slots & GPU time. |

---

## 8 Extra zero‑cost resources to bolt on

| Tool / Data Feed | Use case | Free tier |
|------------------|----------|-----------|
| **TradingView (Free)** | Chart sketching; public chart URLs back into Perplexity. | Unlimited public charts (delayed prices on some exchanges). |
| **FRED API** | Pull CPI, DXY, 10‑year yields into Python or Excel. | Unlimited calls. |
| **ForexFactory calendar** | Human‑readable release times & consensus. | Free web scrape. |
| **FinBERT (Hugging Face)** | Python headline sentiment scoring. | MIT licence, free. |
| **QuantConnect Lean (local)** | Back‑testing engine in C#/Python. | Free when run locally. |

---

## 9 Bottom line

* **Truly unlimited & free** inside Perplexity: Quick searches, Spaces, URL context, highlight‑summary extension, Tier‑0 API.  
* **Free-but-capped:** 3–5 daily Pro queries, 3 Deep‑Research jobs, 3 uploads.  
* Combine the uncapped bits with other zero‑cost data feeds and a local LLM to build a professional‑grade research stack without opening your wallet.

---

### © 2025 – Use at your own risk. This guide is informational and **not** financial advice.
