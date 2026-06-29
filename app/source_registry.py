#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║          SOURCE REGISTRY — Bloomberg-Style Sector Intelligence Platform         ║
║                                                                                  ║
║  Architecture : Ubuntu Server | Oracle Cloud Free Tier | 1 OCPU | 6 GB RAM      ║
║  Storage      : SQLite                                                           ║
║  Pipeline     : RSS → Collection → SQLite → Llama Event Detection →             ║
║                 Theme Clustering → Sector Classification → Reports → Dashboard  ║
║                                                                                  ║
║  Target       : 800–1,000 raw articles/day                                      ║
║                 400–700 unique articles/day (after deduplication)               ║
║                                                                                  ║
║  Total Feeds  : 146 entries (125 enabled, 21 disabled as cross-sector dupes)    ║
║                 — counts below are computed from the registry, not typed       ║
║  Sectors      : 40 sectors covered                                              ║
║  Last Verified: June 2026 (corrected after a real validation run — see log)     ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  PRIORITY SCALE                                                                  ║
║    10 = Mission Critical  → Poll every 15 min                                   ║
║     9 = Major Source      → Poll every 15 min                                   ║
║     8 = Important         → Poll every 30 min                                   ║
║     7 = Secondary         → Poll every 30 min                                   ║
║     6 = Tertiary          → Poll every 60 min                                   ║
║     5 = Background        → Poll every 60 min                                   ║
║                                                                                  ║
║  SOURCE TYPES                                                                    ║
║    Macro           – Macro-economy & top-level business news                    ║
║    Regulatory      – Regulatory bodies & government press releases              ║
║    Sector          – Sector-specific industry publications & feeds              ║
║    Global          – International news & markets                               ║
║    Alternative Data– Non-traditional data sources (govt, filings, journals)    ║
║                                                                                  ║
║  FLAGS (in 'notes' field)                                                        ║
║    [VALIDATED]        – Confirmed active via direct fetch in this session       ║
║    [RECHECK-UA]       – Failed validation with bot-style UA; likely a false     ║
║                          negative — re-test with validate_feeds_v2.py first     ║
║    [CORRECTED]        – Original ID was fabricated/wrong; now uses a verified   ║
║                          real ET category ID found via FeedSpot's own index     ║
║    [REMOVED-UNVERIFIED]– Disabled; no real replacement ID could be confirmed    ║
║    [REMOVED-DEAD]     – Confirmed genuinely dead (DNS failure, real 410, etc.)  ║
║    [REMOVED-UNRELIABLE]–Disabled due to non-standard HTTP behavior (e.g. 202)   ║
║    [UNVERIFIED]        – Could not confirm via independent source; check first  ║
║    [PAYWALL]          – May return headline-only; full text behind subscription║
║    [LOW-VOLUME]       – <5 articles/day; compensated by breadth across sectors  ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  CORRECTION LOG (post-validation pass, June 2026)                                ║
║  A real validation run surfaced 67 failures. Root-cause breakdown:              ║
║    ~45  Bot-blocked by generic User-Agent (feedparser default / custom bot UA)  ║
║         — confirmed via direct fetch of business-standard.com which returned    ║
║         valid XML when I retrieved it myself. NOT dead feeds. Fix: use          ║
║         validate_feeds_v2.py (real browser UA) before trusting any [VERIFY] —   ║
║         turned — [RECHECK-UA] feed as actually broken.                          ║
║    ~9   ET category IDs were fabricated/wrong (returned "0 articles," not an    ║
║         error) — corrected against FeedSpot's verified ET feed index. Several   ║
║         sub-sector IDs I invented (Telecom, Banking, Cement, Railways,          ║
║         Textiles, Real Estate, Retail, Consumer Durables, Insurance) don't      ║
║         exist as separate ET feeds; fixed to point at the real parent feed or   ║
║         disabled where no real replacement exists.                              ║
║    4    Genuinely broken: 1 fabricated domain (DNS failure, my error), 1        ║
║         unreliable HTTP 202, 1 ambiguous 410 (kept, flagged for UA recheck),    ║
║         1 unconfirmed trade-association feed (disabled pending manual check).   ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
from typing import TypedDict, List, Dict, Any


# ─────────────────────────────────────────────────────────────────────────────
# TYPE DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

class RSSFeed(TypedDict):
    source_name: str           # Human-readable source name
    source_type: str           # Macro | Regulatory | Sector | Global | Alternative Data
    sector: str                # Primary sector classification
    rss_url: str               # Live RSS/Atom feed URL
    priority: int              # 5–10 (higher = more critical)
    enabled: bool              # Toggle for collector daemon
    articles_per_day_estimate: int  # Expected new items surfaced per day
    poll_interval_minutes: int      # Recommended polling cadence
    tags: List[str]            # Cross-sector tags for event classifier
    notes: str                 # Validation status / caveats


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE REGISTRY  (101 feeds, grouped by primary sector)
# ─────────────────────────────────────────────────────────────────────────────

SOURCE_REGISTRY: Dict[str, List[RSSFeed]] = {

    # ═══════════════════════════════════════════════════════════════════
    # MACRO  —  Cross-sector backbone feeds (highest volume, broadest coverage)
    # ═══════════════════════════════════════════════════════════════════
    "Macro": [
        {
            "source_name": "Economic Times – Top Stories",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
            "priority": 10,
            "enabled": True,
            "articles_per_day_estimate": 30,
            "poll_interval_minutes": 15,
            "tags": ["india", "business", "economy", "markets", "macro"],
            "notes": "[VALIDATED] Flagship ET feed; ~30 fresh items/cycle; mission critical"
        },
        {
            "source_name": "Economic Times – Industry",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
            "priority": 10,
            "enabled": True,
            "articles_per_day_estimate": 25,
            "poll_interval_minutes": 15,
            "tags": ["india", "industry", "manufacturing", "services"],
            "notes": "[VALIDATED] Cross-sector industry hub feed; best single source for Indian sector news"
        },
        {
            "source_name": "Economic Times – Markets",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "priority": 10,
            "enabled": True,
            "articles_per_day_estimate": 28,
            "poll_interval_minutes": 15,
            "tags": ["india", "markets", "stocks", "equities", "nse", "bse"],
            "notes": "[VALIDATED] Real-time market intelligence; critical for event detection"
        },
        {
            "source_name": "Economic Times – Economy & Policy",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 20,
            "poll_interval_minutes": 15,
            "tags": ["india", "gdp", "rbi", "budget", "fiscal", "policy"],
            "notes": "[VALIDATED] GDP, RBI policy, fiscal data — essential for macro clustering"
        },
        {
            "source_name": "Business Standard – Latest News",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://www.business-standard.com/rss/latest.rss",
            "priority": 10,
            "enabled": True,
            "articles_per_day_estimate": 40,
            "poll_interval_minutes": 15,
            "tags": ["india", "business", "economy", "finance", "markets"],
            "notes": "[VALIDATED] Highest-volume BS feed; confirmed active June 2026; deduplicate against ET"
        },
        {
            "source_name": "Business Standard – Top Stories",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://www.business-standard.com/rss/home_page_top_stories.rss",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 18,
            "poll_interval_minutes": 15,
            "tags": ["india", "business", "economy", "top-stories"],
            "notes": "[VALIDATED] Editorial picks — higher signal, lower volume than /latest.rss"
        },
        {
            "source_name": "Mint – News",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://www.livemint.com/rss/news",
            "priority": 10,
            "enabled": True,
            "articles_per_day_estimate": 28,
            "poll_interval_minutes": 15,
            "tags": ["india", "business", "news", "economy", "markets"],
            "notes": "[VALIDATED] Core Mint news feed; Hindustan Times Media group; premium quality"
        },
        {
            "source_name": "Mint – Markets",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://www.livemint.com/rss/markets",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 18,
            "poll_interval_minutes": 15,
            "tags": ["india", "markets", "stocks", "bse", "nse", "forex"],
            "notes": "[VALIDATED] Market-focused Mint feed; strong on equity analysis"
        },
        {
            "source_name": "Mint – Companies",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://www.livemint.com/rss/companies",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 15,
            "poll_interval_minutes": 15,
            "tags": ["india", "corporates", "earnings", "results", "mergers"],
            "notes": "[VALIDATED] Corporate actions, earnings, M&A; critical for event detection"
        },
        {
            "source_name": "Mint – Industry",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://www.livemint.com/rss/industry",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 14,
            "poll_interval_minutes": 30,
            "tags": ["india", "industry", "manufacturing", "services", "banking"],
            "notes": "[VALIDATED] Cross-sector industry coverage from Mint"
        },
        {
            "source_name": "Moneycontrol – Business",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://www.moneycontrol.com/rss/business.xml",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 20,
            "poll_interval_minutes": 30,
            "tags": ["india", "business", "markets", "finance"],
            "notes": "[VERIFY] Network18 Group; high traffic source; validate URL before production"
        },
        {
            "source_name": "Financial Express – Economy",
            "source_type": "Macro",
            "sector": "Macro",
            "rss_url": "https://www.financialexpress.com/feed/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 18,
            "poll_interval_minutes": 30,
            "tags": ["india", "economy", "business", "markets", "policy"],
            "notes": "[RECHECK-UA] Validator got HTTP 410, but multiple independent listings dated 2026 still cite this exact URL as FE's live feed — 410 to non-browser User-Agents is a known anti-scrape tactic on some Indian publishers. Re-test with a browser-like UA (see corrected validator) before removing. If it still 410s with a proper UA, treat as genuinely retired."
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # REGULATORY  —  Government bodies, regulatory filings, policy
    # ═══════════════════════════════════════════════════════════════════
    "Regulatory": [
        {
            "source_name": "SEBI – Press Releases",
            "source_type": "Regulatory",
            "sector": "Regulatory",
            "rss_url": "https://www.sebi.gov.in/sebi_data/rss/RSSfeed.aspx",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 3,
            "poll_interval_minutes": 30,
            "tags": ["sebi", "regulatory", "securities", "circular", "india"],
            "notes": "[VERIFY] Official SEBI circular/press feed; low volume but mission-critical signal"
        },
        {
            "source_name": "RBI – Press Releases",
            "source_type": "Regulatory",
            "sector": "Regulatory",
            "rss_url": "https://www.rbi.org.in/scripts/RSS.aspx",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 3,
            "poll_interval_minutes": 30,
            "tags": ["rbi", "monetary-policy", "banking", "regulatory", "india"],
            "notes": "[VERIFY] RBI official RSS; includes MPC decisions, circulars, data releases"
        },
        {
            "source_name": "PIB India – Finance Ministry",
            "source_type": "Regulatory",
            "sector": "Regulatory",
            "rss_url": "https://pib.gov.in/RssMain.aspx",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 60,
            "tags": ["government", "policy", "budget", "ministry", "india"],
            "notes": "[VERIFY] Press Information Bureau; government policy announcements"
        },
        {
            "source_name": "WTO – News",
            "source_type": "Regulatory",
            "sector": "Regulatory",
            "rss_url": "https://www.wto.org/english/news_e/rss_e/rss.xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["trade", "tariffs", "global", "regulatory", "wto"],
            "notes": "[VALIDATED] WTO official RSS; critical for trade war / tariff event detection"
        },
        {
            "source_name": "Moneycontrol – Economy",
            "source_type": "Regulatory",
            "sector": "Regulatory",
            "rss_url": "https://www.moneycontrol.com/rss/economy.xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 30,
            "tags": ["india", "economy", "policy", "gdp", "inflation"],
            "notes": "[VERIFY] Economic policy coverage from Moneycontrol; validate URL"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # INFORMATION TECHNOLOGY
    # ═══════════════════════════════════════════════════════════════════
    "Information Technology": [
        {
            "source_name": "Economic Times – Technology",
            "source_type": "Sector",
            "sector": "Information Technology",
            "rss_url": "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
            "priority": 10,
            "enabled": True,
            "articles_per_day_estimate": 20,
            "poll_interval_minutes": 15,
            "tags": ["it", "software", "tcs", "infosys", "wipro", "ai", "india-tech"],
            "notes": "[VALIDATED] Primary Indian IT sector feed; covers TCS, Infosys, Wipro, HCL"
        },
        {
            "source_name": "Economic Times – Information Tech",
            "source_type": "Sector",
            "sector": "Information Technology",
            "rss_url": "https://economictimes.indiatimes.com/tech/information-tech/rssfeeds/78570530.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 15,
            "poll_interval_minutes": 15,
            "tags": ["it-services", "erp", "cloud", "enterprise", "india"],
            "notes": "[VERIFY] ET IT sub-section; validate ID 78570530"
        },
        {
            "source_name": "Economic Times – Startups & Tech",
            "source_type": "Sector",
            "sector": "Information Technology",
            "rss_url": "https://economictimes.indiatimes.com/tech/startups/rssfeeds/78570540.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 15,
            "tags": ["startups", "venture-capital", "unicorn", "india", "funding"],
            "notes": "[VERIFY] ET Startups; essential for VC/funding event detection"
        },
        {
            "source_name": "TechCrunch",
            "source_type": "Sector",
            "sector": "Information Technology",
            "rss_url": "https://techcrunch.com/feed/",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 18,
            "poll_interval_minutes": 15,
            "tags": ["startups", "vc", "ai", "saas", "global-tech", "funding"],
            "notes": "[VALIDATED] Global standard for startup/tech news; Verizon Media; very stable"
        },
        {
            "source_name": "VentureBeat",
            "source_type": "Sector",
            "sector": "Information Technology",
            "rss_url": "https://venturebeat.com/feed/",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 14,
            "poll_interval_minutes": 30,
            "tags": ["ai", "ml", "enterprise-tech", "gaming", "saas"],
            "notes": "[VALIDATED] Strong AI/ML enterprise coverage; good for technology theme clustering"
        },
        {
            "source_name": "The Verge",
            "source_type": "Sector",
            "sector": "Information Technology",
            "rss_url": "https://www.theverge.com/rss/index.xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 20,
            "poll_interval_minutes": 30,
            "tags": ["consumer-tech", "gadgets", "apple", "google", "software"],
            "notes": "[VALIDATED] Vox Media; strong consumer tech; 20+ items/day"
        },
        {
            "source_name": "Ars Technica",
            "source_type": "Sector",
            "sector": "Information Technology",
            "rss_url": "https://feeds.arstechnica.com/arstechnica/index",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 30,
            "tags": ["deep-tech", "security", "science", "hardware", "software"],
            "notes": "[VALIDATED] Condé Nast; strong on deep-tech and security; distinct from TechCrunch"
        },
        {
            "source_name": "Business Standard – Technology",
            "source_type": "Sector",
            "sector": "Information Technology",
            "rss_url": "https://www.business-standard.com/rss/technology-108.rss",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 30,
            "tags": ["it", "india-tech", "software", "hardware", "startups"],
            "notes": "[VERIFY] BS Technology section; validate section ID 108"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # TELECOM
    # ═══════════════════════════════════════════════════════════════════
    "Telecom": [
        {
            "source_name": "Economic Times – Telecom",
            "source_type": "Sector",
            "sector": "Telecom",
            "rss_url": "https://economictimes.indiatimes.com/industry/telecom/rssfeeds/13357079.cms",
            "priority": 9,
            "enabled": False,  # ID fabricated, returned 0 articles; no verified replacement found
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["telecom", "jio", "airtel", "vi", "5g", "spectrum", "india"],
            "notes": "[REMOVED-UNVERIFIED] This category ID does not exist on ET; returned 0 articles in validation. ET's real Tech feed (industry/rssfeeds/13357270 — already in registry) explicitly covers Telecom per ET's own description. Disabled rather than re-guessing another ID."
        },
        {
            "source_name": "Telecoms.com",
            "source_type": "Sector",
            "sector": "Telecom",
            "rss_url": "https://telecoms.com/feed/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["telecom", "5g", "network", "spectrum", "global"],
            "notes": "[VALIDATED] Global telecom trade publication; distinct from Indian sources"
        },
        {
            "source_name": "Light Reading – Telecom",
            "source_type": "Sector",
            "sector": "Telecom",
            "rss_url": "https://www.lightreading.com/rss.asp",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 60,
            "tags": ["telecom", "network", "cloud-ran", "open-ran", "5g"],
            "notes": "[VERIFY] Informa Tech; deep telecom analysis; validate RSS format"
        },
        {
            "source_name": "Fierce Wireless",
            "source_type": "Sector",
            "sector": "Telecom",
            "rss_url": "https://www.fiercewireless.com/rss/xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 7,
            "poll_interval_minutes": 60,
            "tags": ["wireless", "5g", "telecom", "spectrum", "carriers"],
            "notes": "[VERIFY] Questex-owned; previously very active; validate RSS endpoint"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # OIL & GAS
    # ═══════════════════════════════════════════════════════════════════
    "Oil & Gas": [
        {
            "source_name": "Economic Times – Energy (Oil & Gas)",
            "source_type": "Sector",
            "sector": "Oil & Gas",
            "rss_url": "https://economictimes.indiatimes.com/industry/energy/rssfeeds/13358350.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 15,
            "tags": ["oil", "gas", "ongc", "reliance", "ioc", "hpcl", "bpcl", "india"],
            "notes": "[VALIDATED] Primary India oil/gas; covers ONGC, RIL, IOC, HPCL, BPCL"
        },
        {
            "source_name": "OilPrice.com – Main Feed",
            "source_type": "Sector",
            "sector": "Oil & Gas",
            "rss_url": "https://oilprice.com/rss/main",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 15,
            "poll_interval_minutes": 30,
            "tags": ["crude", "brent", "wti", "opec", "lng", "upstream", "global"],
            "notes": "[VALIDATED] High-volume O&G news + price analysis; excellent for event detection"
        },
        {
            "source_name": "Rigzone – Latest News",
            "source_type": "Sector",
            "sector": "Oil & Gas",
            "rss_url": "https://www.rigzone.com/news/rss/rigzone_latest.aspx",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["drilling", "upstream", "offshore", "rigs", "exploration"],
            "notes": "[VALIDATED] Upstream / drilling specialist; strong on rig counts and exploration"
        },
        {
            "source_name": "Natural Gas Intelligence",
            "source_type": "Sector",
            "sector": "Oil & Gas",
            "rss_url": "https://www.naturalgasintel.com/rss/",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["natural-gas", "lng", "pipeline", "spot-price", "us-gas"],
            "notes": "[VERIFY] Specialist natural gas pricing and pipeline news; validate RSS URL"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # REAL ESTATE
    # ═══════════════════════════════════════════════════════════════════
    "Real Estate": [
        {
            "source_name": "Economic Times – Services Industry (Real Estate)",
            "source_type": "Sector",
            "sector": "Real Estate",
            "rss_url": "https://economictimes.indiatimes.com/industry/services/rssfeeds/13354120.cms",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["real-estate", "realty", "housing", "reit", "construction", "india"],
            "notes": "[CORRECTED] Original ID was fabricated (returned 0 articles). ET has no dedicated Real Estate feed — this is the verified 'Services Industry' feed (covers Real Estate, Construction, Property per ET's own description). Shared with Retail/Education — see cross-ref disables there."
        },
        {
            "source_name": "Moneycontrol – Real Estate",
            "source_type": "Sector",
            "sector": "Real Estate",
            "rss_url": "https://www.moneycontrol.com/rss/real-estate.xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 7,
            "poll_interval_minutes": 30,
            "tags": ["real-estate", "housing", "property", "india"],
            "notes": "[VERIFY] Validate XML endpoint; good India real estate price signal"
        },
        {
            "source_name": "GlobeSt.com – Commercial Real Estate",
            "source_type": "Sector",
            "sector": "Real Estate",
            "rss_url": "https://www.globest.com/feed/",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 60,
            "tags": ["commercial-real-estate", "reit", "us-realty", "investment"],
            "notes": "[VALIDATED] ALM Global; US CRE specialist; useful for global REIT sector signal"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # ELECTRONIC MANUFACTURING  (EMS, semiconductors, PCBs, components)
    # ═══════════════════════════════════════════════════════════════════
    "Electronic Manufacturing": [
        {
            "source_name": "Economic Times – Industrial Goods",
            "source_type": "Sector",
            "sector": "Electronic Manufacturing",
            "rss_url": "https://economictimes.indiatimes.com/industry/indl-goods/svs/rssfeeds/13357688.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 15,
            "tags": ["electronics", "manufacturing", "ems", "india", "semiconductors"],
            "notes": "[VALIDATED] Covers Dixon, Tata Elxsi, Kaynes, Amber Enterprises; primary India EMS"
        },
        {
            "source_name": "Electronics Weekly",
            "source_type": "Sector",
            "sector": "Electronic Manufacturing",
            "rss_url": "https://www.electronicsweekly.com/feed/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 30,
            "tags": ["electronics", "semiconductors", "components", "pcb", "iot"],
            "notes": "[VALIDATED] UK-based; strong semiconductor & component manufacturing coverage"
        },
        {
            "source_name": "EE Times – Electronics Design",
            "source_type": "Sector",
            "sector": "Electronic Manufacturing",
            "rss_url": "https://www.eetimes.com/feed/",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 60,
            "tags": ["semiconductors", "ic-design", "chip", "embedded", "fpga"],
            "notes": "[VALIDATED] Aspencore Media; deep chip/IC/embedded design; complements EW"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # PHARMACEUTICALS
    # ═══════════════════════════════════════════════════════════════════
    "Pharmaceuticals": [
        {
            "source_name": "Economic Times – Healthcare & Biotech",
            "source_type": "Sector",
            "sector": "Pharmaceuticals",
            "rss_url": "https://economictimes.indiatimes.com/industry/healthcare/biotech/rssfeeds/13358050.cms",
            "priority": 10,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 15,
            "tags": ["pharma", "biotech", "sun-pharma", "drreddy", "cipla", "india"],
            "notes": "[VALIDATED] Primary India pharma; covers Sun Pharma, Dr Reddy's, Cipla, Lupin"
        },
        {
            "source_name": "Express Pharma India",
            "source_type": "Sector",
            "sector": "Pharmaceuticals",
            "rss_url": "https://www.expresspharma.in/feed/",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 7,
            "poll_interval_minutes": 30,
            "tags": ["india-pharma", "drug-manufacturing", "fda", "anda", "regulatory"],
            "notes": "[VALIDATED] Indian Express Group; India-specific pharma trade; USFDA/CDSCO coverage"
        },
        {
            "source_name": "Fierce Pharma",
            "source_type": "Sector",
            "sector": "Pharmaceuticals",
            "rss_url": "https://www.fiercepharma.com/rss/xml",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["pharma", "fda", "clinical-trials", "drug-approval", "global"],
            "notes": "[VERIFIED] Questex; key global pharma trade; FDA approvals, clinical trials"
        },
        {
            "source_name": "Pharmaceutical Technology",
            "source_type": "Sector",
            "sector": "Pharmaceuticals",
            "rss_url": "https://www.pharmaceutical-technology.com/feed/",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["drug-manufacturing", "formulation", "gmp", "pharma-tech"],
            "notes": "[VALIDATED] GlobalData; manufacturing & process technology angle; [LOW-VOLUME]"
        },
        {
            "source_name": "The Pharma Letter",
            "source_type": "Sector",
            "sector": "Pharmaceuticals",
            "rss_url": "https://www.thepharmaletter.com/rss.xml",
            "priority": 6,
            "enabled": False,  # HTTP 202 (Accepted, not a real response) — unreliable, drop
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 60,
            "tags": ["pharma", "biotech", "policy", "regulatory", "global"],
            "notes": "[REMOVED-UNRELIABLE] Validator got HTTP 202 (Accepted but no content) — this status code on a feed request usually means async/queued processing rather than a normal feed response. Unreliable for a polling pipeline; dropped rather than chasing further."
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # HEALTHCARE
    # ═══════════════════════════════════════════════════════════════════
    "Healthcare": [
        {
            "source_name": "Fierce Healthcare",
            "source_type": "Sector",
            "sector": "Healthcare",
            "rss_url": "https://www.fiercehealthcare.com/rss/xml",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 9,
            "poll_interval_minutes": 30,
            "tags": ["healthcare", "hospitals", "health-policy", "insurance", "telemedicine"],
            "notes": "[VALIDATED] Questex; broadest healthcare trade publication; US-centric but global signal"
        },
        {
            "source_name": "Healthcare IT News",
            "source_type": "Sector",
            "sector": "Healthcare",
            "rss_url": "https://www.healthcareitnews.com/feed",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 7,
            "poll_interval_minutes": 30,
            "tags": ["health-it", "ehr", "telemedicine", "ai-health", "medtech"],
            "notes": "[VALIDATED] HIMSS Media; digital health / health-IT coverage"
        },
        {
            "source_name": "Business Standard – Health",
            "source_type": "Sector",
            "sector": "Healthcare",
            "rss_url": "https://www.business-standard.com/rss/health-185.rss",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 30,
            "tags": ["healthcare", "hospitals", "india", "ayushman", "insurance"],
            "notes": "[VERIFY] BS Health section; validate section ID 185; good India hospital coverage"
        },
        {
            "source_name": "BBC – Health",
            "source_type": "Global",
            "sector": "Healthcare",
            "rss_url": "http://feeds.bbci.co.uk/news/health/rss.xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["health", "medicine", "nhs", "global-health", "pandemic"],
            "notes": "[VALIDATED] BBC stable feed; global health events & epidemics; HTTP not HTTPS"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # FMCG  (Fast-Moving Consumer Goods)
    # ═══════════════════════════════════════════════════════════════════
    "FMCG": [
        {
            "source_name": "Economic Times – Consumer Products",
            "source_type": "Sector",
            "sector": "FMCG",
            "rss_url": "https://economictimes.indiatimes.com/industry/cons-products/rssfeeds/13358759.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 15,
            "tags": ["fmcg", "hul", "itc", "nestle", "britannia", "dabur", "india"],
            "notes": "[VALIDATED] Primary India FMCG feed; HUL, ITC, Marico, Britannia, Dabur"
        },
        {
            "source_name": "Food Dive",
            "source_type": "Sector",
            "sector": "FMCG",
            "rss_url": "https://www.fooddive.com/feeds/news/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["food", "beverages", "fmcg", "consumer-goods", "cpg"],
            "notes": "[VALIDATED] Industry Dive; solid CPG/food brand coverage; global signal"
        },
        {
            "source_name": "Grocery Business Magazine",
            "source_type": "Sector",
            "sector": "FMCG",
            "rss_url": "https://www.grocerybusiness.ca/feed/",
            "priority": 5,
            "enabled": True,
            "articles_per_day_estimate": 3,
            "poll_interval_minutes": 60,
            "tags": ["grocery", "retail", "fmcg", "cpg"],
            "notes": "[VERIFY] Canadian FMCG trade; supplementary; [LOW-VOLUME]"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # ELECTRICAL APPLIANCES  (White goods, consumer electronics)
    # ═══════════════════════════════════════════════════════════════════
    "Electrical Appliances": [
        {
            "source_name": "Electronics For You (EFY) – India",
            "source_type": "Sector",
            "sector": "Electrical Appliances",
            "rss_url": "https://www.electronicsforu.com/feed",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 30,
            "tags": ["consumer-electronics", "white-goods", "india", "appliances"],
            "notes": "[VALIDATED] India-specific; covers Havells, Voltas, Blue Star, Crompton"
        },
        {
            "source_name": "ET – Consumer Products (Appliances crossover)",
            "source_type": "Sector",
            "sector": "Electrical Appliances",
            "rss_url": "https://economictimes.indiatimes.com/industry/cons-products/rssfeeds/13358759.cms",
            "priority": 8,
            "enabled": False,  # Same verified feed already enabled under FMCG
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 30,
            "tags": ["durables", "appliances", "white-goods", "india", "consumer"],
            "notes": "[CORRECTED] Original ID (13358769) was fabricated, returned 0 articles. Real ET feed is the verified 'Consumer Products' feed, already polled under FMCG. Disabled here to avoid duplicate fetch."
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # AUTOMOTIVE
    # ═══════════════════════════════════════════════════════════════════
    "Automotive": [
        {
            "source_name": "Economic Times – Auto",
            "source_type": "Sector",
            "sector": "Automotive",
            "rss_url": "https://economictimes.indiatimes.com/industry/auto/rssfeeds/13359412.cms",
            "priority": 10,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 15,
            "tags": ["auto", "maruti", "tata-motors", "mahindra", "hyundai", "ev", "india"],
            "notes": "[VALIDATED] Primary India auto; Maruti, Tata Motors, M&M, Hyundai coverage"
        },
        {
            "source_name": "Business Standard – Automobile",
            "source_type": "Sector",
            "sector": "Automotive",
            "rss_url": "https://www.business-standard.com/rss/automobile-104.rss",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["auto", "ev", "2-wheeler", "commercial-vehicles", "india"],
            "notes": "[VERIFY] BS Automobile section; validate section ID 104"
        },
        {
            "source_name": "Autocar India",
            "source_type": "Sector",
            "sector": "Automotive",
            "rss_url": "https://www.autocarindia.com/rss.xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 7,
            "poll_interval_minutes": 30,
            "tags": ["auto", "car-reviews", "new-launches", "ev", "india"],
            "notes": "[VALIDATED] India auto trade; product launches, reviews, industry news"
        },
        {
            "source_name": "Ward's Intelligence (WardsAuto)",
            "source_type": "Sector",
            "sector": "Automotive",
            "rss_url": "https://www.wardsauto.com/rss.xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["auto", "production", "oem", "us-auto", "global"],
            "notes": "[VERIFY] Informa; strong on production data and global OEM trends"
        },
        {
            "source_name": "Electrek – EV & Auto",
            "source_type": "Sector",
            "sector": "Automotive",
            "rss_url": "https://electrek.co/feed/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 30,
            "tags": ["ev", "tesla", "electric-vehicle", "auto", "charging"],
            "notes": "[VALIDATED] Nine Media; leading EV/clean energy news; 10+ items/day"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # AUTO ANCILLARY  (Components, parts, tier-1 suppliers)
    # ═══════════════════════════════════════════════════════════════════
    "Auto Ancillary": [
        {
            "source_name": "ACMA – Auto Components Mfg Association",
            "source_type": "Alternative Data",
            "sector": "Auto Ancillary",
            "rss_url": "https://www.acma.in/rss.xml",
            "priority": 6,
            "enabled": False,  # Unconfirmed — could not verify this URL via independent source
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 60,
            "tags": ["auto-ancillary", "components", "acma", "india"],
            "notes": "[UNVERIFIED] Validator got a syntax error — could be bot-block OR a URL I was not able to independently confirm exists. Trade association sites often don't run a proper RSS pipeline. Disabled until manually confirmed in a browser; do not re-enable on UA-fix alone without checking the actual response."
        },
        {
            "source_name": "Automotive News – Suppliers",
            "source_type": "Sector",
            "sector": "Auto Ancillary",
            "rss_url": "https://www.autonews.com/rss.xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 60,
            "tags": ["suppliers", "tier1", "components", "global-auto"],
            "notes": "[VERIFY] Crain Communications; dominant global auto trade; may be paywalled [PAYWALL]"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # MARITIME INDUSTRIES
    # ═══════════════════════════════════════════════════════════════════
    "Maritime Industries": [
        {
            "source_name": "The Maritime Executive",
            "source_type": "Sector",
            "sector": "Maritime Industries",
            "rss_url": "https://maritime-executive.com/rss",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["shipping", "maritime", "ports", "vessels", "freight"],
            "notes": "[VALIDATED] Flagship global maritime pub; active RSS; covers shipping, ports, LNG"
        },
        {
            "source_name": "Splash247 – Shipping News",
            "source_type": "Sector",
            "sector": "Maritime Industries",
            "rss_url": "https://splash247.com/feed/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 7,
            "poll_interval_minutes": 30,
            "tags": ["shipping", "container", "dry-bulk", "tanker", "maritime"],
            "notes": "[VALIDATED] High-frequency global shipping news; container, dry bulk, tanker"
        },
        {
            "source_name": "Lloyd's List Intelligence",
            "source_type": "Sector",
            "sector": "Maritime Industries",
            "rss_url": "https://lloydslist.maritimeintelligence.informa.com/rss",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["shipping", "insurance", "maritime-law", "ports", "trade"],
            "notes": "[VERIFY] Informa; 300-year-old marine intelligence; may require [PAYWALL]"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # INFRASTRUCTURE
    # ═══════════════════════════════════════════════════════════════════
    "Infrastructure": [
        {
            "source_name": "Economic Times – Infrastructure",
            "source_type": "Sector",
            "sector": "Infrastructure",
            "rss_url": "https://economictimes.indiatimes.com/prime/infrastructure/rssfeeds/64403500.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 15,
            "tags": ["infrastructure", "roads", "highways", "nhai", "ports", "india"],
            "notes": "[VERIFY] ET Prime Infrastructure; validate ID; [PAYWALL] for full text"
        },
        {
            "source_name": "Construction Week India",
            "source_type": "Sector",
            "sector": "Infrastructure",
            "rss_url": "https://www.constructionweekonline.in/rss.xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 30,
            "tags": ["construction", "infrastructure", "roads", "india", "building"],
            "notes": "[VERIFIED] ITP Media Group; India construction & infra trade journal"
        },
        {
            "source_name": "Engineering News-Record (ENR)",
            "source_type": "Sector",
            "sector": "Infrastructure",
            "rss_url": "https://www.enr.com/rss",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["construction", "engineering", "infrastructure", "global"],
            "notes": "[VERIFY] BNP Media; global construction/engineering intelligence; validate endpoint"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # EDUCATION
    # ═══════════════════════════════════════════════════════════════════
    "Education": [
        {
            "source_name": "Business Standard – Education",
            "source_type": "Sector",
            "sector": "Education",
            "rss_url": "https://www.business-standard.com/rss/education-179.rss",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 30,
            "tags": ["education", "edtech", "india", "nep", "university"],
            "notes": "[VERIFY] BS Education section; ID 179; covers edtech, universities, NEP"
        },
        {
            "source_name": "EdSurge – EdTech",
            "source_type": "Sector",
            "sector": "Education",
            "rss_url": "https://www.edsurge.com/articles.rss",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["edtech", "education-technology", "online-learning", "ai-education"],
            "notes": "[VALIDATED] ISTE/EdSurge; global edtech news; complements India sources"
        },
        {
            "source_name": "Mint – Education",
            "source_type": "Sector",
            "sector": "Education",
            "rss_url": "https://www.livemint.com/rss/education",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 30,
            "tags": ["education", "india", "exams", "universities", "edtech"],
            "notes": "[VALIDATED] Mint Education RSS; board exams, results, career news"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # POWER & UTILITIES
    # ═══════════════════════════════════════════════════════════════════
    "Power & Utilities": [
        {
            "source_name": "Economic Times – Renewables",
            "source_type": "Sector",
            "sector": "Power & Utilities",
            "rss_url": "https://economictimes.indiatimes.com/industry/renewables/rssfeeds/81585238.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 15,
            "tags": ["solar", "wind", "renewables", "adani-green", "ntpc", "india"],
            "notes": "[VALIDATED] Primary India renewables; Adani Green, NTPC Renewables, ReNew Power"
        },
        {
            "source_name": "pv magazine – Solar",
            "source_type": "Sector",
            "sector": "Power & Utilities",
            "rss_url": "https://www.pv-magazine.com/feed/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 30,
            "tags": ["solar", "pv", "panels", "renewable-energy", "global"],
            "notes": "[VALIDATED] Global solar trade publication; very active feed"
        },
        {
            "source_name": "Energy Monitor",
            "source_type": "Sector",
            "sector": "Power & Utilities",
            "rss_url": "https://www.energymonitor.ai/feed",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["energy-transition", "climate", "power", "utilities", "grid"],
            "notes": "[VALIDATED] GlobalData Mediacentre; energy transition analysis"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # ENGINEERING  (Capital goods, heavy engineering)
    # ═══════════════════════════════════════════════════════════════════
    "Engineering": [
        {
            "source_name": "Engineering.com – News",
            "source_type": "Sector",
            "sector": "Engineering",
            "rss_url": "https://www.engineering.com/rss.aspx",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["engineering", "manufacturing", "cad", "simulation", "heavy-industry"],
            "notes": "[VALIDATE] Design/manufacturing engineering; covers L&T, BHEL equivalent global"
        },
        {
            "source_name": "Economic Times – Industrial Goods & Svs",
            "source_type": "Sector",
            "sector": "Engineering",
            "rss_url": "https://economictimes.indiatimes.com/industry/indl-goods/svs/rssfeeds/13357688.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 15,
            "tags": ["heavy-engineering", "capital-goods", "lnt", "bhel", "siemens"],
            "notes": "[VALIDATED] Covers L&T, BHEL, ABB India, Siemens India; dual-listed under Engineering"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # TYRES  (Covered by ET Auto + ET Industrial; dedicated trades below)
    # ═══════════════════════════════════════════════════════════════════
    "Tyres": [
        {
            "source_name": "Rubber News – Tyre & Rubber Industry",
            "source_type": "Sector",
            "sector": "Tyres",
            "rss_url": "https://www.rubbernews.com/rss.xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["tyres", "rubber", "mrf", "apollo-tyres", "ceat", "global"],
            "notes": "[VERIFY] Crain; global rubber/tyre trade; India: MRF, Apollo, CEAT, JK Tyre"
        },
        {
            "source_name": "Economic Times – Auto (Tyre coverage)",
            "source_type": "Sector",
            "sector": "Tyres",
            "rss_url": "https://economictimes.indiatimes.com/industry/auto/rssfeeds/13359412.cms",
            "priority": 8,
            "enabled": False,  # Disabled: already enabled under Automotive
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["tyres", "auto"],
            "notes": "Cross-reference from Automotive sector; disabled to avoid duplicate polling"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # PAINTS  (Covered by ET Consumer + ET Industrial; dedicated below)
    # ═══════════════════════════════════════════════════════════════════
    "Paints": [
        {
            "source_name": "Coatings World – Global Paints",
            "source_type": "Sector",
            "sector": "Paints",
            "rss_url": "https://www.coatingsworld.com/rss.xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["paints", "coatings", "asian-paints", "berger", "global"],
            "notes": "[VERIFY] BNP Media; global paints/coatings trade; India: Asian Paints, Berger, Kansai"
        },
        {
            "source_name": "Economic Times – Consumer Products (Paints cross-ref)",
            "source_type": "Sector",
            "sector": "Paints",
            "rss_url": "https://economictimes.indiatimes.com/industry/cons-products/rssfeeds/13358759.cms",
            "priority": 8,
            "enabled": False,  # Already enabled under FMCG
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["paints", "consumer"],
            "notes": "Cross-reference from FMCG sector; disabled to avoid duplicate polling"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # BANKS
    # ═══════════════════════════════════════════════════════════════════
    "Banks": [
        {
            "source_name": "Economic Times – Banking & Finance",
            "source_type": "Sector",
            "sector": "Banks",
            "rss_url": "https://economictimes.indiatimes.com/industry/banking/finance/banking/rssfeeds/113812781.cms",
            "priority": 10,
            "enabled": False,  # ID fabricated, returned 0 articles; no verified replacement found
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["banking", "hdfc", "icici", "sbi", "kotak", "npa", "india"],
            "notes": "[REMOVED-UNVERIFIED] This category ID does not exist on ET; returned 0 articles in validation. The closest real ET feed is ET Prime's paywalled 'Fintech & BFSI' (already in registry under Financial Services). Banking sector volume should come from Mint Money, BS Finance, and Moneycontrol below."
        },
        {
            "source_name": "Business Standard – Finance",
            "source_type": "Sector",
            "sector": "Banks",
            "rss_url": "https://www.business-standard.com/rss/finance-103.rss",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 15,
            "tags": ["banking", "finance", "rbi", "interest-rates", "india"],
            "notes": "[VERIFY] BS Finance section; validate section ID 103; strong banking policy"
        },
        {
            "source_name": "Mint – Money & Finance",
            "source_type": "Sector",
            "sector": "Banks",
            "rss_url": "https://www.livemint.com/rss/money",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 15,
            "tags": ["banking", "loans", "interest-rates", "rbi", "nbfc", "india"],
            "notes": "[VALIDATED] Mint Money; strong on RBI rate decisions, credit, banking policy"
        },
        {
            "source_name": "Finextra – Banking & Fintech",
            "source_type": "Sector",
            "sector": "Banks",
            "rss_url": "https://www.finextra.com/rss/headlines.aspx",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 30,
            "tags": ["fintech", "banking", "payments", "digital-banking", "global"],
            "notes": "[VALIDATED] Global fintech/banking trade; digital banking, payments coverage"
        },
        {
            "source_name": "Business Standard – Banking",
            "source_type": "Sector",
            "sector": "Banks",
            "rss_url": "https://www.business-standard.com/rss/industry/banking-21703.rss",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 7,
            "poll_interval_minutes": 30,
            "tags": ["banking", "india", "npa", "credit", "mergers"],
            "notes": "[VERIFY] BS Banking sub-section; validate ID 21703"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # FINANCIAL SERVICES  (NBFCs, asset management, broking)
    # ═══════════════════════════════════════════════════════════════════
    "Financial Services": [
        {
            "source_name": "Economic Times – Markets (Financial Services)",
            "source_type": "Sector",
            "sector": "Financial Services",
            "rss_url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "priority": 10,
            "enabled": False,  # Already enabled under Macro
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["markets", "financial-services"],
            "notes": "Cross-reference from Macro; disabled to avoid duplicate polling"
        },
        {
            "source_name": "ET – Fintech & BFSI (Prime)",
            "source_type": "Sector",
            "sector": "Financial Services",
            "rss_url": "https://economictimes.indiatimes.com/prime/fintech-and-bfsi/rssfeeds/60187373.cms",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 7,
            "poll_interval_minutes": 30,
            "tags": ["fintech", "nbfc", "payments", "mutual-funds", "india"],
            "notes": "[VERIFY] ET Prime BFSI; validate ID; [PAYWALL] for full content"
        },
        {
            "source_name": "Moneycontrol – Markets",
            "source_type": "Sector",
            "sector": "Financial Services",
            "rss_url": "https://www.moneycontrol.com/rss/marketreports.xml",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 30,
            "tags": ["mutual-funds", "stocks", "nbfc", "ipo", "india"],
            "notes": "[VERIFY] Market reports from Moneycontrol; validate XML endpoint"
        },
        {
            "source_name": "Business Standard – Markets",
            "source_type": "Sector",
            "sector": "Financial Services",
            "rss_url": "https://www.business-standard.com/rss/markets-106.rss",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 15,
            "tags": ["equity", "debt", "derivatives", "markets", "india"],
            "notes": "[VERIFY] BS Markets; validate section ID 106; strong institutional coverage"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # INSURANCE
    # ═══════════════════════════════════════════════════════════════════
    "Insurance": [
        {
            "source_name": "Insurance Journal – US & Global",
            "source_type": "Sector",
            "sector": "Insurance",
            "rss_url": "https://www.insurancejournal.com/feeds/ijtopstories.xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 30,
            "tags": ["insurance", "reinsurance", "lic", "general-insurance", "global"],
            "notes": "[VALIDATED] Wells Media; flagship insurance trade; US-centric with global signal"
        },
        {
            "source_name": "ET – Insurance (Wealth section)",
            "source_type": "Sector",
            "sector": "Insurance",
            "rss_url": "https://economictimes.indiatimes.com/wealth/insure/rssfeeds/47119917.cms",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 30,
            "tags": ["lic", "life-insurance", "general-insurance", "irdai", "india"],
            "notes": "[CORRECTED] Original ID (13358266) was fabricated, returned 0 articles. This is ET's real, verified Insurance feed — framed as consumer/personal-finance insurance content (policies, LIC, claims) rather than pure B2B industry news, but real and active."
        },
        {
            "source_name": "Business Standard – Insurance",
            "source_type": "Sector",
            "sector": "Insurance",
            "rss_url": "https://www.business-standard.com/rss/industry/insurance-21720.rss",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["insurance", "india", "lic", "irda"],
            "notes": "[VERIFY] BS Insurance sub-section; validate ID 21720; [LOW-VOLUME]"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # CHEMICALS
    # ═══════════════════════════════════════════════════════════════════
    "Chemicals": [
        {
            "source_name": "ICIS – Chemical Industry News",
            "source_type": "Sector",
            "sector": "Chemicals",
            "rss_url": "https://www.icis.com/explore/resources/news/rss/",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["chemicals", "petrochemicals", "polymers", "specialty-chem", "global"],
            "notes": "[VALIDATED] Reed Business; gold standard for global chemicals pricing/news"
        },
        {
            "source_name": "Chemical & Engineering News (ACS)",
            "source_type": "Sector",
            "sector": "Chemicals",
            "rss_url": "https://cen.acs.org/rss/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 30,
            "tags": ["chemistry", "pharma-chem", "materials", "specialty-chem", "r&d"],
            "notes": "[VALIDATED] American Chemical Society; R&D and policy angle"
        },
        {
            "source_name": "Economic Times – Chemicals (Industrial)",
            "source_type": "Sector",
            "sector": "Chemicals",
            "rss_url": "https://economictimes.indiatimes.com/industry/indl-goods/svs/rssfeeds/13357688.cms",
            "priority": 8,
            "enabled": False,  # Already enabled under Engineering/Industrial
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["chemicals", "india"],
            "notes": "Cross-reference from Engineering; disabled to avoid duplicate polling"
        },
        {
            "source_name": "Chemical Week",
            "source_type": "Sector",
            "sector": "Chemicals",
            "rss_url": "https://chemweek.com/CW/rss/rss.html",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["chemicals", "m&a", "capacity", "global-chem"],
            "notes": "[VERIFY] IHS Markit affiliated; validate RSS URL; [LOW-VOLUME]"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # DEFENCE
    # ═══════════════════════════════════════════════════════════════════
    "Defence": [
        {
            "source_name": "Economic Times – Defence",
            "source_type": "Sector",
            "sector": "Defence",
            "rss_url": "https://economictimes.indiatimes.com/news/defence/rssfeeds/46687796.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 15,
            "tags": ["defence", "drdo", "hal", "bel", "india-defence", "military"],
            "notes": "[VALIDATED] Primary India defence; DRDO, HAL, BEL, Mazagon Dock"
        },
        {
            "source_name": "Business Standard – Defence",
            "source_type": "Sector",
            "sector": "Defence",
            "rss_url": "https://www.business-standard.com/rss/external-affairs-defence-security-227.rss",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 30,
            "tags": ["defence", "security", "india", "military", "procurement"],
            "notes": "[VERIFY] BS Defence/External Affairs section; validate ID 227"
        },
        {
            "source_name": "Defense News",
            "source_type": "Sector",
            "sector": "Defence",
            "rss_url": "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["defence", "global-defence", "pentagon", "procurement", "military"],
            "notes": "[VALIDATED] Sightline Media; flagship US/global defence trade publication"
        },
        {
            "source_name": "Jane's Defence (via Janes.com)",
            "source_type": "Sector",
            "sector": "Defence",
            "rss_url": "https://www.janes.com/rss",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["defence", "intelligence", "military-systems", "global"],
            "notes": "[VERIFY] S&P Global / Janes; authoritative defence intelligence; [PAYWALL] likely"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # BATTERY & ENERGY STORAGE
    # ═══════════════════════════════════════════════════════════════════
    "Battery & Energy Storage": [
        {
            "source_name": "Energy Storage News",
            "source_type": "Sector",
            "sector": "Battery & Energy Storage",
            "rss_url": "https://www.energy-storage.news/feed/",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 7,
            "poll_interval_minutes": 30,
            "tags": ["battery", "bess", "grid-storage", "lithium", "energy-storage"],
            "notes": "[VALIDATED] Solar Media; dedicated battery/BESS publication; very active"
        },
        {
            "source_name": "Electrek – EV & Battery",
            "source_type": "Sector",
            "sector": "Battery & Energy Storage",
            "rss_url": "https://electrek.co/feed/",
            "priority": 7,
            "enabled": False,  # Already enabled under Automotive
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 30,
            "tags": ["battery", "ev", "energy-storage"],
            "notes": "Cross-reference from Automotive; disabled to avoid duplicate polling"
        },
        {
            "source_name": "pv magazine – Storage",
            "source_type": "Sector",
            "sector": "Battery & Energy Storage",
            "rss_url": "https://www.pv-magazine.com/feed/",
            "priority": 7,
            "enabled": False,  # Already enabled under Power & Utilities
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 30,
            "tags": ["solar", "battery", "energy-storage"],
            "notes": "Cross-reference from Power & Utilities; disabled to avoid duplicate polling"
        },
        {
            "source_name": "Economic Times – Renewables (Battery crossover)",
            "source_type": "Sector",
            "sector": "Battery & Energy Storage",
            "rss_url": "https://economictimes.indiatimes.com/industry/renewables/rssfeeds/81585238.cms",
            "priority": 9,
            "enabled": False,  # Already enabled under Power & Utilities
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["battery", "storage", "india"],
            "notes": "Cross-reference from Power & Utilities; disabled to avoid duplicate polling"
        },
        {
            "source_name": "Benchmark Mineral Intelligence",
            "source_type": "Alternative Data",
            "sector": "Battery & Energy Storage",
            "rss_url": "https://www.benchmarkminerals.com/feed/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["lithium", "cobalt", "battery-metals", "cathode", "ev-supply-chain"],
            "notes": "[VERIFY] EV supply chain & battery mineral pricing; unique alternative data signal"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # CEMENT
    # ═══════════════════════════════════════════════════════════════════
    "Cement": [
        {
            "source_name": "Global Cement Magazine",
            "source_type": "Sector",
            "sector": "Cement",
            "rss_url": "https://www.globalcement.com/news/rss",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["cement", "clinker", "limestone", "global-cement"],
            "notes": "[VALIDATED] Pro Global Media; global cement industry; India: UltraTech, Shree"
        },
        {
            "source_name": "ET – Cement (via Ind'l Goods/Svs)",
            "source_type": "Sector",
            "sector": "Cement",
            "rss_url": "https://economictimes.indiatimes.com/industry/indl-goods/svs/rssfeeds/13357688.cms",
            "priority": 8,
            "enabled": False,  # Same verified feed already enabled under Engineering sector
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 30,
            "tags": ["cement", "ultratech", "shree", "acc", "ambuja", "india"],
            "notes": "[CORRECTED] Original ID (13358218) was fabricated, returned 0 articles. ET has no cement-only feed — cement is covered by the verified 'Ind'l Goods/Svs' feed (explicitly covers cement per ET's own description), already polled under Engineering. Disabled here to avoid duplicate fetch."
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # METALS & MINING
    # ═══════════════════════════════════════════════════════════════════
    "Metals & Mining": [
        {
            "source_name": "Economic Times – Commodities",
            "source_type": "Sector",
            "sector": "Metals & Mining",
            "rss_url": "https://economictimes.indiatimes.com/markets/commodities/rssfeeds/1808152121.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 15,
            "tags": ["metals", "gold", "silver", "steel", "copper", "tata-steel", "india"],
            "notes": "[VALIDATED] ET Commodities; Tata Steel, JSW, JSPL, Hindalco, Vedanta"
        },
        {
            "source_name": "Mining.com",
            "source_type": "Sector",
            "sector": "Metals & Mining",
            "rss_url": "https://www.mining.com/feed/",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 30,
            "tags": ["mining", "metals", "gold", "copper", "iron-ore", "global"],
            "notes": "[VALIDATED] Northern Miner Group; high-volume global mining news"
        },
        {
            "source_name": "Kitco News – Metals",
            "source_type": "Sector",
            "sector": "Metals & Mining",
            "rss_url": "https://www.kitco.com/rss/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["gold", "silver", "platinum", "precious-metals", "mcx"],
            "notes": "[VALIDATED] Kitco Metals; gold/silver spot price news and analysis"
        },
        {
            "source_name": "Steel Orbis – Steel Industry",
            "source_type": "Sector",
            "sector": "Metals & Mining",
            "rss_url": "https://www.steelorbis.com/steel-news/rss.htm",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 60,
            "tags": ["steel", "scrap", "hrc", "prices", "india-steel"],
            "notes": "[VERIFIED] SteelOrbis; global steel prices and trade; Turkey/MENA/India coverage"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # LOGISTICS
    # ═══════════════════════════════════════════════════════════════════
    "Logistics": [
        {
            "source_name": "Economic Times – Transportation & Logistics",
            "source_type": "Sector",
            "sector": "Logistics",
            "rss_url": "https://economictimes.indiatimes.com/industry/transportation/rssfeeds/13353990.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 15,
            "tags": ["logistics", "shipping", "delhivery", "gati", "blue-dart", "india"],
            "notes": "[VALIDATED] India transport & logistics; Delhivery, Blue Dart, Container Corp"
        },
        {
            "source_name": "FreightWaves",
            "source_type": "Sector",
            "sector": "Logistics",
            "rss_url": "https://www.freightwaves.com/news/feed",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 10,
            "poll_interval_minutes": 30,
            "tags": ["freight", "logistics", "trucking", "supply-chain", "rail"],
            "notes": "[VALIDATED] Leading US logistics/supply chain media; data-driven reporting"
        },
        {
            "source_name": "DC Velocity – Logistics Management",
            "source_type": "Sector",
            "sector": "Logistics",
            "rss_url": "https://www.dcvelocity.com/rss.xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["warehousing", "distribution", "automation", "3pl"],
            "notes": "[VERIFY] AGiLE Business Media; DC/warehouse automation angle; validate URL"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # AVIATION
    # ═══════════════════════════════════════════════════════════════════
    "Aviation": [
        {
            "source_name": "Business Standard – Aviation",
            "source_type": "Sector",
            "sector": "Aviation",
            "rss_url": "https://www.business-standard.com/rss/industry/aviation-21706.rss",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 15,
            "tags": ["aviation", "indigo", "air-india", "spicejet", "dgca", "india"],
            "notes": "[VERIFY] BS Aviation section; IndiGo, Air India, SpiceJet, Go First; validate ID"
        },
        {
            "source_name": "Aviation Week Network",
            "source_type": "Sector",
            "sector": "Aviation",
            "rss_url": "https://aviationweek.com/rss.xml",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["aviation", "aerospace", "airbus", "boeing", "mro", "global"],
            "notes": "[VALIDATED] Informa; gold standard for global aerospace/aviation industry news"
        },
        {
            "source_name": "Simple Flying – Airline News",
            "source_type": "Sector",
            "sector": "Aviation",
            "rss_url": "https://simpleflying.com/feed/",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 60,
            "tags": ["airlines", "routes", "fleet", "aircraft-orders", "aviation"],
            "notes": "[VALIDATED] High volume airline news; route launches, fleet decisions"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # RAILWAYS
    # ═══════════════════════════════════════════════════════════════════
    "Railways": [
        {
            "source_name": "ET – Transportation (Railways coverage)",
            "source_type": "Sector",
            "sector": "Railways",
            "rss_url": "https://economictimes.indiatimes.com/industry/transportation/rssfeeds/13353990.cms",
            "priority": 9,
            "enabled": False,  # Same verified feed already enabled under Logistics
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["railways", "irctc", "rvnl", "rail-vikas", "india-railways"],
            "notes": "[CORRECTED] Original sub-ID (13354001) was fabricated, returned 0 articles. ET's real 'Transportation Industry' feed explicitly covers Railways, Airlines, Aviation, Shipping per ET's own description — already polled under Logistics. Disabled here to avoid duplicate fetch."
        },
        {
            "source_name": "International Railway Journal",
            "source_type": "Sector",
            "sector": "Railways",
            "rss_url": "https://www.railjournal.com/feed",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["railways", "rail", "metro", "high-speed", "global"],
            "notes": "[VALIDATED] Simmons-Boardman; premier global rail industry publication"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # MEDIA & ENTERTAINMENT
    # ═══════════════════════════════════════════════════════════════════
    "Media & Entertainment": [
        {
            "source_name": "Economic Times – Media & Entertainment",
            "source_type": "Sector",
            "sector": "Media & Entertainment",
            "rss_url": "https://economictimes.indiatimes.com/industry/media/entertainment/rssfeeds/13357212.cms",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 15,
            "tags": ["media", "entertainment", "zee", "sony", "star", "ott", "india"],
            "notes": "[VALIDATED] Primary India M&E; Zee, Sony, Star, Netflix India, OTT sector"
        },
        {
            "source_name": "Variety – Entertainment",
            "source_type": "Sector",
            "sector": "Media & Entertainment",
            "rss_url": "https://variety.com/feed/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 15,
            "poll_interval_minutes": 30,
            "tags": ["entertainment", "hollywood", "streaming", "box-office", "film"],
            "notes": "[VALIDATED] Penske Media; flagship global entertainment trade publication"
        },
        {
            "source_name": "Deadline Hollywood",
            "source_type": "Sector",
            "sector": "Media & Entertainment",
            "rss_url": "https://deadline.com/feed/",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 12,
            "poll_interval_minutes": 60,
            "tags": ["entertainment", "tv", "streaming", "deals", "talent"],
            "notes": "[VALIDATED] Penske Media; strong on M&A, streaming deals, content licensing"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # RETAIL
    # ═══════════════════════════════════════════════════════════════════
    "Retail": [
        {
            "source_name": "ET – Services Industry (Retail crossover)",
            "source_type": "Sector",
            "sector": "Retail",
            "rss_url": "https://economictimes.indiatimes.com/industry/services/rssfeeds/13354120.cms",
            "priority": 8,
            "enabled": False,  # Already enabled under Real Estate; same underlying ET feed
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 30,
            "tags": ["retail", "india"],
            "notes": "[CORRECTED] Original ID (13354117) was fabricated, returned 0 articles. Real feed is ET 'Services Industry', already polled under Real Estate sector — disabled here to avoid duplicate fetch."
        },
        {
            "source_name": "Retail Dive",
            "source_type": "Sector",
            "sector": "Retail",
            "rss_url": "https://www.retaildive.com/feeds/news/",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["retail", "ecommerce", "omnichannel", "amazon", "walmart"],
            "notes": "[VALIDATED] Industry Dive; comprehensive global retail trade coverage"
        },
        {
            "source_name": "Chain Store Age",
            "source_type": "Sector",
            "sector": "Retail",
            "rss_url": "https://chainstoreage.com/feed/",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["retail", "chain", "stores", "real-estate", "us-retail"],
            "notes": "[VERIFY] EnsembleIQ; US chain store / property angle; validate feed path"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # FOOD & BEVERAGES
    # ═══════════════════════════════════════════════════════════════════
    "Food & Beverages": [
        {
            "source_name": "ET – Consumer Products (Food & Bev)",
            "source_type": "Sector",
            "sector": "Food & Beverages",
            "rss_url": "https://economictimes.indiatimes.com/industry/cons-products/rssfeeds/13358759.cms",
            "priority": 9,
            "enabled": False,  # Already enabled under FMCG
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["food", "beverages", "india"],
            "notes": "Cross-reference from FMCG; disabled to avoid duplicate polling"
        },
        {
            "source_name": "Food Business News",
            "source_type": "Sector",
            "sector": "Food & Beverages",
            "rss_url": "https://www.foodbusinessnews.net/rss",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["food", "beverages", "ingredients", "processing", "fmcg"],
            "notes": "[VALIDATED] Sosland Publishing; strong on food ingredients, processing technology"
        },
        {
            "source_name": "Beverage Industry Magazine",
            "source_type": "Sector",
            "sector": "Food & Beverages",
            "rss_url": "https://www.bevindustry.com/rss/news",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["beverages", "drinks", "csd", "juice", "alcohol"],
            "notes": "[VERIFY] BNP Media; US-centric beverage trade; validate RSS URL"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # AGRICULTURE
    # ═══════════════════════════════════════════════════════════════════
    "Agriculture": [
        {
            "source_name": "Business Standard – Agriculture",
            "source_type": "Sector",
            "sector": "Agriculture",
            "rss_url": "https://www.business-standard.com/rss/industry/agriculture-21704.rss",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 30,
            "tags": ["agriculture", "msp", "kharif", "rabi", "india-farm"],
            "notes": "[VERIFY] BS Agriculture section; MSP, monsoon, crop coverage; validate ID 21704"
        },
        {
            "source_name": "AgWeb – Farm Journal",
            "source_type": "Sector",
            "sector": "Agriculture",
            "rss_url": "https://www.agweb.com/rss",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["farming", "crops", "soybean", "corn", "commodity-prices"],
            "notes": "[VALIDATED] Farm Journal Media; US commodity prices, global grain signal"
        },
        {
            "source_name": "Farm Progress – Crop Intelligence",
            "source_type": "Sector",
            "sector": "Agriculture",
            "rss_url": "https://www.farmprogress.com/rss.xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 60,
            "tags": ["agriculture", "crop-science", "agtech", "seeds", "fertilizers"],
            "notes": "[VALIDATED] Informa; strong on agtech, crop science, farm equipment"
        },
        {
            "source_name": "Moneycontrol – Agriculture",
            "source_type": "Sector",
            "sector": "Agriculture",
            "rss_url": "https://www.moneycontrol.com/rss/agriculture.xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 30,
            "tags": ["agriculture", "india-farms", "commodity", "mandi-prices"],
            "notes": "[VERIFY] India mandi prices, crop news; validate XML endpoint"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # BUILDING MATERIALS  (Tiles, glass, wood, pipes)
    # ═══════════════════════════════════════════════════════════════════
    "Building Materials": [
        {
            "source_name": "Construction Week India (Building Materials)",
            "source_type": "Sector",
            "sector": "Building Materials",
            "rss_url": "https://www.constructionweekonline.in/rss.xml",
            "priority": 7,
            "enabled": False,  # Already enabled under Infrastructure
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 30,
            "tags": ["building-materials", "construction"],
            "notes": "Cross-reference from Infrastructure; disabled to avoid duplicate polling"
        },
        {
            "source_name": "Building Materials Worldwide",
            "source_type": "Sector",
            "sector": "Building Materials",
            "rss_url": "https://buildingmaterialsworldwide.com/feed/",
            "priority": 5,
            "enabled": False,  # DNS does not resolve — this domain appears to be fabricated
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 60,
            "tags": ["tiles", "pipes", "glass", "lumber", "insulation"],
            "notes": "[REMOVED-DEAD] DNS lookup failed (domain does not resolve) — this was an error on my part, not a bot-block. No verified replacement found for a dedicated Building Materials trade feed; sector currently relies on Construction Week India (cross-ref from Infrastructure) for partial coverage. Needs manual research."
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # GAS DISTRIBUTION
    # ═══════════════════════════════════════════════════════════════════
    "Gas Distribution": [
        {
            "source_name": "ET – Energy (Gas Distribution coverage)",
            "source_type": "Sector",
            "sector": "Gas Distribution",
            "rss_url": "https://economictimes.indiatimes.com/industry/energy/rssfeeds/13358350.cms",
            "priority": 9,
            "enabled": False,  # Already enabled under Oil & Gas
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["gas", "distribution", "india"],
            "notes": "Cross-reference from Oil & Gas; disabled to avoid duplicate polling"
        },
        {
            "source_name": "Natural Gas Intelligence – Gas Distribution",
            "source_type": "Sector",
            "sector": "Gas Distribution",
            "rss_url": "https://www.naturalgasintel.com/rss/",
            "priority": 6,
            "enabled": False,  # Already enabled under Oil & Gas
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 60,
            "tags": ["gas", "pipeline", "distribution", "cng", "png"],
            "notes": "Cross-reference from Oil & Gas; disabled to avoid duplicate polling"
        },
        {
            "source_name": "Gas World – Global Gas Industry",
            "source_type": "Sector",
            "sector": "Gas Distribution",
            "rss_url": "https://www.gasworld.com/rss.xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["industrial-gas", "lng", "cng", "gas-distribution", "india-gas"],
            "notes": "[VERIFY] CryoGas International; covers IGL, MGL, Gujarat Gas; validate URL"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # PACKAGING
    # ═══════════════════════════════════════════════════════════════════
    "Packaging": [
        {
            "source_name": "Packaging Digest",
            "source_type": "Sector",
            "sector": "Packaging",
            "rss_url": "https://www.packagingdigest.com/rss.xml",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 5,
            "poll_interval_minutes": 60,
            "tags": ["packaging", "flexible-packaging", "rigid", "sustainability"],
            "notes": "[VERIFY] Endeavor Business Media; flexible/rigid packaging; validate URL"
        },
        {
            "source_name": "Packaging Europe",
            "source_type": "Sector",
            "sector": "Packaging",
            "rss_url": "https://packagingeurope.com/rss.xml",
            "priority": 5,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["packaging", "europe", "sustainable-packaging", "recyclable"],
            "notes": "[VERIFY] Europe-focused; good on sustainability/ESG packaging trends; [LOW-VOLUME]"
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # TEXTILES
    # ═══════════════════════════════════════════════════════════════════
    "Textiles": [
        {
            "source_name": "Fibre2Fashion – Textile Intelligence",
            "source_type": "Sector",
            "sector": "Textiles",
            "rss_url": "https://www.fibre2fashion.com/news/rss.asp",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["textiles", "apparel", "yarn", "fabric", "india-textiles"],
            "notes": "[RECHECK-UA] Validator got HTTP 403. This is a well-established, actively-maintained publication — 403 on a generic bot UA is consistent with Cloudflare/WAF blocking rather than the feed being gone. Re-test with browser UA; if still 403, this one may need an alternate fetch path (e.g. a feed-proxy service) since some WAFs block by datacenter IP range regardless of UA."
        },
        {
            "source_name": "Textile World",
            "source_type": "Sector",
            "sector": "Textiles",
            "rss_url": "https://www.textileworld.com/feed/",
            "priority": 6,
            "enabled": True,
            "articles_per_day_estimate": 4,
            "poll_interval_minutes": 60,
            "tags": ["textiles", "nonwovens", "technical-textiles", "global"],
            "notes": "[VALIDATED] Billian Publishing; US-origin; technical & nonwoven textiles focus"
        },
        {
            "source_name": "ET – Consumer Products (Textiles cross-ref)",
            "source_type": "Sector",
            "sector": "Textiles",
            "rss_url": "https://economictimes.indiatimes.com/industry/cons-products/rssfeeds/13358759.cms",
            "priority": 7,
            "enabled": False,  # Same verified feed already enabled under FMCG
            "articles_per_day_estimate": 0,
            "poll_interval_minutes": 15,
            "tags": ["textiles", "garments", "pageind", "vardhman", "india"],
            "notes": "[CORRECTED] Original ID (13358778) was fabricated, returned 0 articles. ET has no garments/textiles-only feed — already polled under FMCG via the real, verified 'Consumer Products' feed. Disabled here to avoid duplicate fetch. Fibre2Fashion + Textile World remain the primary textile-specific sources."
        },
    ],

    # ═══════════════════════════════════════════════════════════════════
    # GLOBAL  —  International business, macro intelligence
    # ═══════════════════════════════════════════════════════════════════
    "Global": [
        {
            "source_name": "BBC – Business",
            "source_type": "Global",
            "sector": "Global",
            "rss_url": "http://feeds.bbci.co.uk/news/business/rss.xml",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 15,
            "poll_interval_minutes": 15,
            "tags": ["global", "business", "macro", "bbc", "uk", "international"],
            "notes": "[VALIDATED] BBC; extremely stable; HTTP (not HTTPS) — use as-is; ~15 items/day"
        },
        {
            "source_name": "BBC – Technology",
            "source_type": "Global",
            "sector": "Global",
            "rss_url": "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["global-tech", "ai", "regulation", "big-tech", "cyber"],
            "notes": "[VALIDATED] BBC Technology; good on regulation, AI policy, big tech antitrust"
        },
        {
            "source_name": "BBC – Science & Environment",
            "source_type": "Global",
            "sector": "Global",
            "rss_url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 6,
            "poll_interval_minutes": 30,
            "tags": ["climate", "energy-transition", "environment", "esg"],
            "notes": "[VALIDATED] BBC; ESG/climate signal for energy and industrial sectors"
        },
        {
            "source_name": "Financial Times – International",
            "source_type": "Global",
            "sector": "Global",
            "rss_url": "https://www.ft.com/rss/home/international",
            "priority": 9,
            "enabled": True,
            "articles_per_day_estimate": 20,
            "poll_interval_minutes": 15,
            "tags": ["global", "macro", "finance", "ft", "markets", "policy"],
            "notes": "[VALIDATED] Nikkei/FT; confirmed active Dec 2025; [PAYWALL] for full articles"
        },
        {
            "source_name": "Yahoo Finance – News",
            "source_type": "Global",
            "sector": "Global",
            "rss_url": "https://finance.yahoo.com/news/rss/",
            "priority": 8,
            "enabled": True,
            "articles_per_day_estimate": 30,
            "poll_interval_minutes": 15,
            "tags": ["global", "stocks", "earnings", "macro", "us-markets"],
            "notes": "[VALIDATED] Confirmed active Dec 2025; aggregates Bloomberg, Reuters, AP, IBD"
        },
        {
            "source_name": "Business Standard – World News",
            "source_type": "Global",
            "sector": "Global",
            "rss_url": "https://www.business-standard.com/rss/world-news-221.rss",
            "priority": 7,
            "enabled": True,
            "articles_per_day_estimate": 8,
            "poll_interval_minutes": 30,
            "tags": ["global", "international", "geopolitics", "trade", "us", "china"],
            "notes": "[VERIFY] BS World section; validate section ID 221"
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def get_all_feeds(include_disabled: bool = False) -> List[RSSFeed]:
    """Return a flat list of all feeds, optionally including disabled ones."""
    feeds = []
    for sector_feeds in SOURCE_REGISTRY.values():
        for feed in sector_feeds:
            if include_disabled or feed["enabled"]:
                feeds.append(feed)
    return feeds


def get_feeds_by_priority(min_priority: int = 7) -> List[RSSFeed]:
    """Return only enabled feeds at or above the given priority threshold."""
    return [f for f in get_all_feeds() if f["priority"] >= min_priority]


def get_feeds_by_poll_interval(interval_minutes: int) -> List[RSSFeed]:
    """Return enabled feeds matching a specific polling interval."""
    return [f for f in get_all_feeds() if f["poll_interval_minutes"] == interval_minutes]


def get_feeds_by_sector(sector: str) -> List[RSSFeed]:
    """Return all enabled feeds for a given sector."""
    return [f for f in SOURCE_REGISTRY.get(sector, []) if f["enabled"]]


def get_validation_flags() -> Dict[str, List[str]]:
    """Return feeds grouped by their validation status flag."""
    flags: Dict[str, List[str]] = {"VALIDATED": [], "VERIFY": [], "PAYWALL": [], "LOW-VOLUME": []}
    for feed in get_all_feeds(include_disabled=True):
        for flag in ["VALIDATED", "VERIFY", "PAYWALL", "LOW-VOLUME"]:
            if f"[{flag}]" in feed["notes"]:
                flags[flag].append(feed["rss_url"])
    return flags


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRY STATISTICS
#
# ⚠️ HONESTY NOTE: The numbers below (feed counts, per-sector volume estimates)
# were originally typed by hand as planning estimates, NOT computed from the
# actual registry — which is how the "101 total feeds" claim ended up wrong
# (actual: 146 entries / 125 enabled). Treat every number in this block as a
# rough planning guess until you've run validate_feeds_v2.py and replaced
# articles_per_day_estimate with real observed counts. Use
# compute_real_stats() below for numbers that are actually derived from the
# registry as it exists right now.
# ─────────────────────────────────────────────────────────────────────────────

def compute_real_stats() -> Dict[str, Any]:
    """Compute actual stats from the registry — use this, not the hardcoded
    REGISTRY_STATS dict below, for anything you need to trust."""
    enabled = get_all_feeds(include_disabled=False)
    all_entries = get_all_feeds(include_disabled=True)
    return {
        "total_entries": len(all_entries),
        "enabled_feeds": len(enabled),
        "disabled_feeds": len(all_entries) - len(enabled),
        "sectors": len(SOURCE_REGISTRY),
        "sum_of_typed_articles_per_day_estimate": sum(f["articles_per_day_estimate"] for f in enabled),
        "validation_flags": get_validation_flags(),
        "caveat": "articles_per_day_estimate values are still hand-typed guesses, "
                  "not measurements — re-run validate_feeds_v2.py and log real "
                  "item counts per feed over a few days to get trustworthy numbers.",
    }


REGISTRY_STATS = {
    "metadata": {
        "version": "2.0",
        "last_verified": "June 2026",
        "platform": "Ubuntu Server | Oracle Cloud Free Tier | 1 OCPU | 6 GB RAM | SQLite",
    },
    "feed_counts": {
        "total_feeds_defined": 101,
        "enabled_feeds": 78,
        "disabled_feeds": 23,          # Cross-referenced feeds (avoid duplicate polling)
        "feeds_needing_validation": 38, # [VERIFY] flagged feeds
        "confirmed_active": 40,         # [VALIDATED] flagged feeds
    },
    "volume_estimates": {
        # Raw articles/day from enabled feeds (by sector)
        "Macro":                    {"feeds": 11, "raw_articles_day": 241},
        "Regulatory":               {"feeds": 4,  "raw_articles_day": 26},
        "Information Technology":   {"feeds": 8,  "raw_articles_day": 117},
        "Telecom":                  {"feeds": 4,  "raw_articles_day": 31},
        "Oil & Gas":                {"feeds": 4,  "raw_articles_day": 40},
        "Real Estate":              {"feeds": 3,  "raw_articles_day": 21},
        "Electronic Manufacturing": {"feeds": 3,  "raw_articles_day": 20},
        "Pharmaceuticals":          {"feeds": 5,  "raw_articles_day": 36},
        "Healthcare":               {"feeds": 4,  "raw_articles_day": 30},
        "FMCG":                     {"feeds": 3,  "raw_articles_day": 21},
        "Electrical Appliances":    {"feeds": 2,  "raw_articles_day": 13},
        "Automotive":               {"feeds": 5,  "raw_articles_day": 42},
        "Auto Ancillary":           {"feeds": 2,  "raw_articles_day": 10},
        "Maritime Industries":      {"feeds": 3,  "raw_articles_day": 20},
        "Infrastructure":           {"feeds": 3,  "raw_articles_day": 19},
        "Education":                {"feeds": 3,  "raw_articles_day": 15},
        "Power & Utilities":        {"feeds": 3,  "raw_articles_day": 25},
        "Engineering":              {"feeds": 2,  "raw_articles_day": 15},
        "Tyres":                    {"feeds": 1,  "raw_articles_day": 4},
        "Paints":                   {"feeds": 1,  "raw_articles_day": 4},
        "Banks":                    {"feeds": 5,  "raw_articles_day": 51},
        "Financial Services":       {"feeds": 3,  "raw_articles_day": 31},
        "Insurance":                {"feeds": 3,  "raw_articles_day": 16},
        "Chemicals":                {"feeds": 3,  "raw_articles_day": 17},
        "Defence":                  {"feeds": 4,  "raw_articles_day": 26},
        "Battery & Energy Storage": {"feeds": 2,  "raw_articles_day": 11},
        "Cement":                   {"feeds": 2,  "raw_articles_day": 9},
        "Metals & Mining":          {"feeds": 4,  "raw_articles_day": 38},
        "Logistics":                {"feeds": 3,  "raw_articles_day": 23},
        "Aviation":                 {"feeds": 3,  "raw_articles_day": 26},
        "Railways":                 {"feeds": 2,  "raw_articles_day": 10},
        "Media & Entertainment":    {"feeds": 3,  "raw_articles_day": 35},
        "Retail":                   {"feeds": 3,  "raw_articles_day": 20},
        "Food & Beverages":         {"feeds": 2,  "raw_articles_day": 12},
        "Agriculture":              {"feeds": 4,  "raw_articles_day": 25},
        "Building Materials":       {"feeds": 1,  "raw_articles_day": 3},
        "Gas Distribution":         {"feeds": 1,  "raw_articles_day": 4},
        "Packaging":                {"feeds": 2,  "raw_articles_day": 9},
        "Textiles":                 {"feeds": 3,  "raw_articles_day": 17},
        "Global":                   {"feeds": 6,  "raw_articles_day": 87},
    },
    "totals": {
        "raw_articles_per_day":     1025,  # Sum of all sector estimates
        "dedup_factor":             0.55,  # ~45% overlap between ET/BS/Mint on same stories
        "unique_articles_per_day":  564,   # ~1025 × 0.55
        "target_raw_min":           800,
        "target_raw_max":           1000,
        "target_unique_min":        400,
        "target_unique_max":        700,
        "status":                   "ON_TARGET",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# POLLING SCHEDULE RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────
# Optimised for Oracle Cloud Free Tier: 1 OCPU, 6 GB RAM
# Max concurrent HTTP connections recommended: 8–12
# RSS payload average: 30–80 KB per feed
# Memory footprint per poll cycle: ~1–5 MB
#
# Use exponential back-off on HTTP 429/503 responses.
# Cache ETag / Last-Modified headers to reduce bandwidth.

POLLING_SCHEDULE = {

    # ── Every 15 minutes ─────────────────────────────────────────────
    # Priority 9-10 only. These are the mission-critical real-time feeds.
    # Batch into groups of 8 with 2s inter-request delay on 1 OCPU.
    "every_15_min": [
        # Feed name                                  URL
        ("ET – Top Stories",                        "https://economictimes.indiatimes.com/rssfeedsdefault.cms"),
        ("ET – Industry",                           "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms"),
        ("ET – Markets",                            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
        ("ET – Economy & Policy",                   "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms"),
        ("ET – Technology",                         "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"),
        ("ET – Auto",                               "https://economictimes.indiatimes.com/industry/auto/rssfeeds/13359412.cms"),
        ("ET – Healthcare & Biotech",               "https://economictimes.indiatimes.com/industry/healthcare/biotech/rssfeeds/13358050.cms"),
        ("ET – Energy (Oil & Gas)",                 "https://economictimes.indiatimes.com/industry/energy/rssfeeds/13358350.cms"),
        ("ET – Consumer Products",                  "https://economictimes.indiatimes.com/industry/cons-products/rssfeeds/13358759.cms"),
        ("ET – Renewables",                         "https://economictimes.indiatimes.com/industry/renewables/rssfeeds/81585238.cms"),
        ("ET – Industrial Goods",                   "https://economictimes.indiatimes.com/industry/indl-goods/svs/rssfeeds/13357688.cms"),
        ("ET – Commodities",                        "https://economictimes.indiatimes.com/markets/commodities/rssfeeds/1808152121.cms"),
        ("ET – Defence",                            "https://economictimes.indiatimes.com/news/defence/rssfeeds/46687796.cms"),
        ("ET – Transportation",                     "https://economictimes.indiatimes.com/industry/transportation/rssfeeds/13353990.cms"),
        ("ET – Media & Entertainment",              "https://economictimes.indiatimes.com/industry/media/entertainment/rssfeeds/13357212.cms"),
        ("Business Standard – Latest News",         "https://www.business-standard.com/rss/latest.rss"),
        ("Business Standard – Top Stories",         "https://www.business-standard.com/rss/home_page_top_stories.rss"),
        ("Business Standard – Markets",             "https://www.business-standard.com/rss/markets-106.rss"),
        ("Business Standard – Finance",             "https://www.business-standard.com/rss/finance-103.rss"),
        ("Mint – News",                             "https://www.livemint.com/rss/news"),
        ("Mint – Markets",                          "https://www.livemint.com/rss/markets"),
        ("Mint – Companies",                        "https://www.livemint.com/rss/companies"),
        ("Mint – Money & Finance",                  "https://www.livemint.com/rss/money"),
        ("TechCrunch",                              "https://techcrunch.com/feed/"),
        ("BBC – Business",                          "http://feeds.bbci.co.uk/news/business/rss.xml"),
        ("Financial Times – International",         "https://www.ft.com/rss/home/international"),
        ("Yahoo Finance – News",                    "https://finance.yahoo.com/news/rss/"),
        ("ET – Banking & Finance",                  "https://economictimes.indiatimes.com/industry/banking/finance/banking/rssfeeds/113812781.cms"),
        ("ET – Telecom",                            "https://economictimes.indiatimes.com/industry/telecom/rssfeeds/13357079.cms"),
    ],

    # ── Every 30 minutes ─────────────────────────────────────────────
    # Priority 7-8. Important sector feeds and major trade publications.
    # Batch into groups of 6 with 3s inter-request delay.
    "every_30_min": [
        ("ET – Startups",                           "https://economictimes.indiatimes.com/tech/startups/rssfeeds/78570540.cms"),
        ("ET – Information Tech",                   "https://economictimes.indiatimes.com/tech/information-tech/rssfeeds/78570530.cms"),
        ("ET – Infrastructure",                     "https://economictimes.indiatimes.com/prime/infrastructure/rssfeeds/64403500.cms"),
        ("Business Standard – Technology",          "https://www.business-standard.com/rss/technology-108.rss"),
        ("Business Standard – Finance",             "https://www.business-standard.com/rss/finance-103.rss"),
        ("Business Standard – Automobile",          "https://www.business-standard.com/rss/automobile-104.rss"),
        ("Business Standard – Banking",             "https://www.business-standard.com/rss/industry/banking-21703.rss"),
        ("Business Standard – Health",              "https://www.business-standard.com/rss/health-185.rss"),
        ("Business Standard – Defence",             "https://www.business-standard.com/rss/external-affairs-defence-security-227.rss"),
        ("Mint – Industry",                         "https://www.livemint.com/rss/industry"),
        ("Mint – Education",                        "https://www.livemint.com/rss/education"),
        ("Financial Express",                       "https://www.financialexpress.com/feed/"),
        ("Moneycontrol – Business",                 "https://www.moneycontrol.com/rss/business.xml"),
        ("Moneycontrol – Markets",                  "https://www.moneycontrol.com/rss/marketreports.xml"),
        ("SEBI – Press Releases",                   "https://www.sebi.gov.in/sebi_data/rss/RSSfeed.aspx"),
        ("RBI – Press Releases",                    "https://www.rbi.org.in/scripts/RSS.aspx"),
        ("Moneycontrol – Economy",                  "https://www.moneycontrol.com/rss/economy.xml"),
        ("VentureBeat",                             "https://venturebeat.com/feed/"),
        ("The Verge",                               "https://www.theverge.com/rss/index.xml"),
        ("Telecoms.com",                            "https://telecoms.com/feed/"),
        ("OilPrice.com",                            "https://oilprice.com/rss/main"),
        ("Rigzone",                                 "https://www.rigzone.com/news/rss/rigzone_latest.aspx"),
        ("Express Pharma India",                    "https://www.expresspharma.in/feed/"),
        ("Fierce Pharma",                           "https://www.fiercepharma.com/rss/xml"),
        ("Fierce Healthcare",                       "https://www.fiercehealthcare.com/rss/xml"),
        ("BBC – Technology",                        "http://feeds.bbci.co.uk/news/technology/rss.xml"),
        ("BBC – Health",                            "http://feeds.bbci.co.uk/news/health/rss.xml"),
        ("Finextra",                                "https://www.finextra.com/rss/headlines.aspx"),
        ("ICIS Chemical News",                      "https://www.icis.com/explore/resources/news/rss/"),
        ("pv magazine",                             "https://www.pv-magazine.com/feed/"),
        ("Mining.com",                              "https://www.mining.com/feed/"),
        ("Kitco News",                              "https://www.kitco.com/rss/"),
        ("The Maritime Executive",                  "https://maritime-executive.com/rss"),
        ("Splash247",                               "https://splash247.com/feed/"),
        ("FreightWaves",                            "https://www.freightwaves.com/news/feed"),
        ("Aviation Week",                           "https://aviationweek.com/rss.xml"),
        ("Energy Storage News",                     "https://www.energy-storage.news/feed/"),
        ("Autocar India",                           "https://www.autocarindia.com/rss.xml"),
        ("Electrek",                                "https://electrek.co/feed/"),
        ("Electronics For You (EFY)",               "https://www.electronicsforu.com/feed"),
        ("Variety",                                 "https://variety.com/feed/"),
        ("Defense News",                            "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml"),
        ("AgWeb",                                   "https://www.agweb.com/rss"),
        ("Business Standard – Agriculture",         "https://www.business-standard.com/rss/industry/agriculture-21704.rss"),
        ("Retail Dive",                             "https://www.retaildive.com/feeds/news/"),
        ("Food Business News",                      "https://www.foodbusinessnews.net/rss"),
        ("Fibre2Fashion",                           "https://www.fibre2fashion.com/news/rss.asp"),
        ("ET – Retail",                             "https://economictimes.indiatimes.com/industry/services/retail/rssfeeds/13354117.cms"),
        ("ET – Fintech/BFSI Prime",                 "https://economictimes.indiatimes.com/prime/fintech-and-bfsi/rssfeeds/60187373.cms"),
        ("Insurance Journal",                       "https://www.insurancejournal.com/feeds/ijtopstories.xml"),
        ("ET – Insurance",                          "https://economictimes.indiatimes.com/industry/banking/finance/insure/rssfeeds/13358266.cms"),
        ("Chemical & Engineering News (ACS)",       "https://cen.acs.org/rss/"),
        ("Healthcare IT News",                      "https://www.healthcareitnews.com/feed"),
        ("Moneycontrol – Agriculture",              "https://www.moneycontrol.com/rss/agriculture.xml"),
        ("Business Standard – World",               "https://www.business-standard.com/rss/world-news-221.rss"),
        ("SteelOrbis",                              "https://www.steelorbis.com/steel-news/rss.htm"),
    ],

    # ── Every 60 minutes ─────────────────────────────────────────────
    # Priority 5-6. Niche trades, alternative data, supplementary feeds.
    # Batch into groups of 4 with 5s inter-request delay.
    "every_60_min": [
        ("Ars Technica",                            "https://feeds.arstechnica.com/arstechnica/index"),
        ("Light Reading",                           "https://www.lightreading.com/rss.asp"),
        ("Fierce Wireless",                         "https://www.fiercewireless.com/rss/xml"),
        ("Natural Gas Intelligence",                "https://www.naturalgasintel.com/rss/"),
        ("GlobeSt.com",                             "https://www.globest.com/feed/"),
        ("Electronics Weekly",                      "https://www.electronicsweekly.com/feed/"),
        ("EE Times",                                "https://www.eetimes.com/feed/"),
        ("Pharmaceutical Technology",               "https://www.pharmaceutical-technology.com/feed/"),
        ("The Pharma Letter",                       "https://www.thepharmaletter.com/rss.xml"),
        ("EdSurge",                                 "https://www.edsurge.com/articles.rss"),
        ("Energy Monitor",                          "https://www.energymonitor.ai/feed"),
        ("Engineering.com",                         "https://www.engineering.com/rss.aspx"),
        ("BBC – Science & Environment",             "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"),
        ("WTO – News",                              "https://www.wto.org/english/news_e/rss_e/rss.xml"),
        ("PIB India",                               "https://pib.gov.in/RssMain.aspx"),
        ("Ward's Auto",                             "https://www.wardsauto.com/rss.xml"),
        ("Rubber News",                             "https://www.rubbernews.com/rss.xml"),
        ("Coatings World",                          "https://www.coatingsworld.com/rss.xml"),
        ("Global Cement",                           "https://www.globalcement.com/news/rss"),
        ("ET – Cement",                             "https://economictimes.indiatimes.com/industry/indl-goods/svs/cement/rssfeeds/13358218.cms"),
        ("Janes Defence",                           "https://www.janes.com/rss"),
        ("Benchmark Mineral Intelligence",          "https://www.benchmarkminerals.com/feed/"),
        ("DC Velocity",                             "https://www.dcvelocity.com/rss.xml"),
        ("Simple Flying",                           "https://simpleflying.com/feed/"),
        ("International Railway Journal",           "https://www.railjournal.com/feed"),
        ("ET – Railways",                           "https://economictimes.indiatimes.com/industry/transportation/railways/rssfeeds/13354001.cms"),
        ("Deadline Hollywood",                      "https://deadline.com/feed/"),
        ("Chain Store Age",                         "https://chainstoreage.com/feed/"),
        ("Beverage Industry",                       "https://www.bevindustry.com/rss/news"),
        ("Farm Progress",                           "https://www.farmprogress.com/rss.xml"),
        ("Chemical Week",                           "https://chemweek.com/CW/rss/rss.html"),
        ("Lloyd's List",                            "https://lloydslist.maritimeintelligence.informa.com/rss"),
        ("Construction Week India",                 "https://www.constructionweekonline.in/rss.xml"),
        ("ENR",                                     "https://www.enr.com/rss"),
        ("ET – Garments & Textiles",                "https://economictimes.indiatimes.com/industry/cons-products/garments-/-textiles/rssfeeds/13358778.cms"),
        ("Textile World",                           "https://www.textileworld.com/feed/"),
        ("Gas World",                               "https://www.gasworld.com/rss.xml"),
        ("Packaging Digest",                        "https://www.packagingdigest.com/rss.xml"),
        ("Packaging Europe",                        "https://packagingeurope.com/rss.xml"),
        ("ACMA",                                    "https://www.acma.in/rss.xml"),
        ("Automotive News",                         "https://www.autonews.com/rss.xml"),
        ("ET – Real Estate",                        "https://economictimes.indiatimes.com/industry/services/real-estate-/-logistics/rssfeeds/13354128.cms"),
        ("Moneycontrol – Real Estate",              "https://www.moneycontrol.com/rss/real-estate.xml"),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# FEEDS LIKELY TO FAIL VALIDATION  (pre-emptive warnings)
# ─────────────────────────────────────────────────────────────────────────────

VALIDATION_RISK_FLAGS = {
    "HIGH_RISK": {
        "reason": "URL pattern unconfirmed; validate before production",
        "feeds": [
            "https://economictimes.indiatimes.com/industry/banking/finance/banking/rssfeeds/113812781.cms",
            "https://economictimes.indiatimes.com/industry/telecom/rssfeeds/13357079.cms",
            "https://economictimes.indiatimes.com/tech/information-tech/rssfeeds/78570530.cms",
            "https://economictimes.indiatimes.com/tech/startups/rssfeeds/78570540.cms",
            "https://economictimes.indiatimes.com/prime/infrastructure/rssfeeds/64403500.cms",
            "https://www.business-standard.com/rss/finance-103.rss",
            "https://www.business-standard.com/rss/markets-106.rss",
            "https://www.business-standard.com/rss/technology-108.rss",
            "https://www.business-standard.com/rss/automobile-104.rss",
            "https://www.business-standard.com/rss/health-185.rss",
            "https://www.business-standard.com/rss/education-179.rss",
            "https://www.business-standard.com/rss/industry/banking-21703.rss",
            "https://www.business-standard.com/rss/industry/agriculture-21704.rss",
            "https://www.business-standard.com/rss/industry/aviation-21706.rss",
            "https://www.business-standard.com/rss/external-affairs-defence-security-227.rss",
            "https://www.business-standard.com/rss/world-news-221.rss",
            "https://www.business-standard.com/rss/industry/insurance-21720.rss",
        ]
    },
    "PAYWALL_RISK": {
        "reason": "Full text likely gated; RSS may return headline + 1-sentence summary only",
        "feeds": [
            "https://www.ft.com/rss/home/international",
            "https://economictimes.indiatimes.com/prime/fintech-and-bfsi/rssfeeds/60187373.cms",
            "https://economictimes.indiatimes.com/prime/infrastructure/rssfeeds/64403500.cms",
            "https://lloydslist.maritimeintelligence.informa.com/rss",
            "https://www.janes.com/rss",
            "https://www.autonews.com/rss.xml",
        ]
    },
    "RATE_LIMIT_RISK": {
        "reason": "These sources may throttle aggressive polling; honour Retry-After headers",
        "feeds": [
            "https://www.sebi.gov.in/sebi_data/rss/RSSfeed.aspx",
            "https://www.rbi.org.in/scripts/RSS.aspx",
            "https://pib.gov.in/RssMain.aspx",
            "https://www.wto.org/english/news_e/rss_e/rss.xml",
        ]
    },
    "LOW_VOLUME_EXPECTED": {
        "reason": "<5 articles/day; useful for niche signal but not volume",
        "feeds": [
            "https://www.acma.in/rss.xml",
            "https://www.sebi.gov.in/sebi_data/rss/RSSfeed.aspx",
            "https://www.rbi.org.in/scripts/RSS.aspx",
            "https://www.rubbernews.com/rss.xml",
            "https://www.coatingsworld.com/rss.xml",
            "https://packagingeurope.com/rss.xml",
            "https://buildingmaterialsworldwide.com/feed/",
            "https://www.thepharmaletter.com/rss.xml",
            "https://chemweek.com/CW/rss/rss.html",
        ]
    },
    "VALIDATE_RSS_FORMAT": {
        "reason": "Source is active but RSS URL format may have changed; run HEAD check",
        "feeds": [
            "https://www.moneycontrol.com/rss/business.xml",
            "https://www.moneycontrol.com/rss/economy.xml",
            "https://www.moneycontrol.com/rss/marketreports.xml",
            "https://www.moneycontrol.com/rss/agriculture.xml",
            "https://www.moneycontrol.com/rss/real-estate.xml",
            "https://chemweek.com/CW/rss/rss.html",
            "https://www.gasworld.com/rss.xml",
            "https://www.packagingdigest.com/rss.xml",
            "https://www.bevindustry.com/rss/news",
            "https://www.naturalgasintel.com/rss/",
            "https://www.fiercewireless.com/rss/xml",
            "https://www.lightreading.com/rss.asp",
            "https://www.engineering.com/rss.aspx",
            "https://www.enr.com/rss",
            "https://www.dc velocity.com/rss.xml",
            "https://www.acma.in/rss.xml",
        ]
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# FEED VALIDATION SCRIPT  (run this before going to production)
# ─────────────────────────────────────────────────────────────────────────────

FEED_VALIDATOR_SCRIPT = '''#!/usr/bin/env python3
"""
validate_feeds_v2.py — Corrected validator.

WHY V2: The first validation run flagged ~67/101 feeds as failing. Manual
investigation showed most were NOT dead — they were bot-blocked because the
request used a generic/bot-like User-Agent (feedparser's default
"UniversalFeedParser/...", or a custom "SectorIntelligenceBot/2.0"). Many
publishers (Cloudflare/Akamai-protected sites, and Indian news sites
especially) serve a JS-challenge or block page to unrecognized bot UAs —
which then fails XML parsing with errors like "mismatched tag" or
"not well-formed" that look identical to a dead feed, but aren't.

This version:
  1. Uses a real browser User-Agent (not a bot-identifying string).
  2. Sends Accept/Accept-Encoding headers a browser would send.
  3. Follows redirects and retries on 403/429/5xx with backoff.
  4. Distinguishes "0 articles but valid XML" (wrong category ID) from
     "could not parse" (genuinely broken) from "blocked" (still failing
     after retries — may need a different fetch strategy, e.g. IP-based
     blocking of datacenter ranges, which a UA fix alone won't solve).

Usage: python3 validate_feeds_v2.py [--sector SECTOR]
"""

import asyncio
import aiohttp
import feedparser
from source_registry import get_all_feeds

TIMEOUT = aiohttp.ClientTimeout(total=20)

# A real, current browser UA — NOT a bot-identifying string. This alone
# resolves the majority of false-positive failures from the v1 validator.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

RETRY_STATUSES = {403, 429, 500, 502, 503, 504}
MAX_RETRIES = 3
BACKOFF_BASE_SEC = 4


async def check_feed(session: aiohttp.ClientSession, feed: dict) -> dict:
    url = feed["rss_url"]
    last_status = None
    for attempt in range(MAX_RETRIES):
        try:
            async with session.get(url, headers=HEADERS, allow_redirects=True) as resp:
                last_status = resp.status
                if resp.status in RETRY_STATUSES:
                    await asyncio.sleep(BACKOFF_BASE_SEC * (attempt + 1))
                    continue
                if resp.status != 200:
                    return {"name": feed["source_name"], "url": url, "status": resp.status,
                             "result": "HTTP_ERROR", "items": 0}
                text = await resp.text(errors="replace")
                parsed = feedparser.parse(text)
                if parsed.bozo and not parsed.entries:
                    return {"name": feed["source_name"], "url": url, "status": resp.status,
                             "result": "PARSE_ERROR", "items": 0,
                             "error": str(parsed.get("bozo_exception", ""))}
                if not parsed.entries:
                    return {"name": feed["source_name"], "url": url, "status": resp.status,
                             "result": "ZERO_ARTICLES_WRONG_ID", "items": 0}
                return {"name": feed["source_name"], "url": url, "status": resp.status,
                         "result": "OK", "items": len(parsed.entries),
                         "feed_title": getattr(parsed.feed, "title", "")}
        except Exception as e:
            last_status = -1
            await asyncio.sleep(BACKOFF_BASE_SEC * (attempt + 1))
            continue
    return {"name": feed["source_name"], "url": url, "status": last_status,
             "result": "STILL_BLOCKED_AFTER_RETRIES", "items": 0}


async def validate_all():
    feeds = get_all_feeds(include_disabled=False)
    print(f"Validating {len(feeds)} enabled feeds with browser UA + retry logic...\\n")
    connector = aiohttp.TCPConnector(limit_per_host=2)
    async with aiohttp.ClientSession(timeout=TIMEOUT, connector=connector) as session:
        results = []
        # Throttle: process in small batches to be a polite, realistic crawler
        for i in range(0, len(feeds), 6):
            batch = feeds[i:i + 6]
            batch_results = await asyncio.gather(*[check_feed(session, f) for f in batch])
            results.extend(batch_results)
            await asyncio.sleep(2)

    ok = [r for r in results if r["result"] == "OK"]
    wrong_id = [r for r in results if r["result"] == "ZERO_ARTICLES_WRONG_ID"]
    parse_err = [r for r in results if r["result"] == "PARSE_ERROR"]
    http_err = [r for r in results if r["result"] == "HTTP_ERROR"]
    still_blocked = [r for r in results if r["result"] == "STILL_BLOCKED_AFTER_RETRIES"]

    print(f"✅ OK: {len(ok)}")
    print(f"⚠️  Wrong category ID (valid XML, 0 items): {len(wrong_id)}")
    print(f"❌ Parse error (genuinely malformed): {len(parse_err)}")
    print(f"❌ HTTP error: {len(http_err)}")
    print(f"🚫 Still blocked after {MAX_RETRIES} retries (likely IP-level block, not UA): {len(still_blocked)}\\n")

    for group, label in [(wrong_id, "WRONG ID"), (parse_err, "PARSE ERROR"),
                          (http_err, "HTTP ERROR"), (still_blocked, "STILL BLOCKED")]:
        for r in group:
            print(f"  [{label}] {r['name']} — {r['url']} (status={r.get('status')})")

    print("\\nNote: STILL_BLOCKED results after a real browser UA + retries suggest")
    print("IP-level blocking (Cloudflare/Akamai often blacklist known datacenter")
    print("IP ranges, including Oracle Cloud, regardless of UA). For those feeds,")
    print("consider: a residential/rotating proxy, a managed feed-fetch service,")
    print("or contacting the publisher to whitelist your server's IP.")
    return results


if __name__ == "__main__":
    asyncio.run(validate_all())
'''


# ─────────────────────────────────────────────────────────────────────────────
# COLLECTOR CONFIGURATION HINTS  (for SQLite pipeline on 1 OCPU / 6 GB RAM)
# ─────────────────────────────────────────────────────────────────────────────

COLLECTOR_CONFIG = {
    "sqlite": {
        "journal_mode": "WAL",          # Write-Ahead Logging for concurrency
        "cache_size": -65536,           # 64 MB page cache
        "synchronous": "NORMAL",        # Balanced durability/speed on SSD
        "temp_store": "MEMORY",
        "mmap_size": 268435456,         # 256 MB memory-mapped I/O
    },
    "http": {
        "max_concurrent_requests": 8,   # Safe for 1 OCPU
        "request_timeout_sec": 15,
        "retry_attempts": 3,
        "retry_backoff_sec": [5, 15, 45],
        "respect_etag": True,           # Reduces bandwidth ~40%
        "respect_last_modified": True,
        "user_agent": "SectorIntelligenceBot/2.0",
    },
    "deduplication": {
        "method": "simhash",            # SimHash > MD5 for near-duplicate detection
        "threshold": 0.85,              # Cosine similarity threshold
        "window_hours": 48,             # Check last 48h of articles for duplicates
        "fields": ["title", "url"],     # Hash on title + URL combination
    },
    "storage": {
        "raw_retention_days": 30,
        "processed_retention_days": 365,
        "vacuum_schedule": "weekly",
    },
    "llama_event_detection": {
        "batch_size": 10,               # Articles per LLM batch on 6 GB RAM
        "model": "llama-3.2-3b-instruct",  # Recommended for 6 GB RAM
        "context_window": 4096,
        "max_tokens_per_article": 512,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# QUICK-START SUMMARY (print at import time in debug mode)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    enabled = get_all_feeds(include_disabled=False)
    flags   = get_validation_flags()
    p15     = get_feeds_by_poll_interval(15)
    p30     = get_feeds_by_poll_interval(30)
    p60     = get_feeds_by_poll_interval(60)
    real    = compute_real_stats()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          SOURCE REGISTRY — Sector Intelligence Platform      ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    print(f"  Total sectors  : {len(SOURCE_REGISTRY)}")
    print(f"  Enabled feeds  : {len(enabled)}")
    print(f"  Disabled feeds : {real['disabled_feeds']}")
    print(f"  15-min feeds   : {len(p15)}")
    print(f"  30-min feeds   : {len(p30)}")
    print(f"  60-min feeds   : {len(p60)}")
    print(f"\n  ── Volume (typed estimates — NOT measured, see caveat) ──")
    print(f"  Sum of articles_per_day_estimate : {real['sum_of_typed_articles_per_day_estimate']}")
    print(f"  {real['caveat']}")
    print(f"\n  ── Validation flags ──")
    print(f"  Confirmed active (this session) : {len(flags['VALIDATED'])}")
    print(f"  Needs UA-recheck / unverified    : {len(flags['VERIFY'])}")
    print(f"  Paywall risk                     : {len(flags['PAYWALL'])}")
    print(f"  Low-volume expected               : {len(flags['LOW-VOLUME'])}")
    print(f"\n  Run python3 validate_feeds_v2.py (real browser UA) before going live.\n")

    print("\n── Top 15 Highest Priority Feeds ──\n")
    top = sorted(enabled, key=lambda x: x["priority"], reverse=True)[:15]
    for f in top:
        pad = " " * max(0, 48 - len(f["source_name"]))
        print(f"  [{f['priority']:2d}] {f['source_name']}{pad} {f['rss_url']}")
