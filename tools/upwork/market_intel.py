#!/usr/bin/env python3
"""
Market Intel -- tracks demand trends and skill gaps for RA's job hunt.

Reads accumulated data from Active Scout runs (scout_skills_log.json)
and generates a market snapshot with skill demand, trends, and learning recs.

Usage:
  python3 market_intel.py                  # Print report
  python3 market_intel.py --telegram       # Also send via Telegram
  python3 market_intel.py --web FILE       # Include fresh WebSearch trend data
  python3 market_intel.py --dashboard      # Write to dashboard-data.json
"""

import json, sys, argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
SKILLS_LOG = PROJECT_DIR / ".tmp" / "scout_skills_log.json"
DASHBOARD_FILE = Path.home() / "projects" / "ra-dashboard" / "dashboard-data.json"

# ============================================================
# RA's current skills (mirrors scout.py)
# ============================================================

RA_SKILLS = {
    "ai automation", "n8n", "claude", "ai agent", "agentic",
    "workflow automation", "python", "meta ads", "facebook ads",
    "chatbot", "landing page", "fastapi", "crm", "make.com",
    "zapier", "api integration", "telegram", "google sheets",
    "web scraping", "social media", "e-commerce", "javascript",
    "content automation", "content pipeline", "automation", "ai",
}

# Skills RA does NOT have but might appear in job listings
LEARNABLE_SKILLS = {
    "supabase": {
        "difficulty": "easy", "time": "1-2 days",
        "connection": "Just Postgres + auth. Pairs with your Python/API skills.",
        "project": "Add Supabase backend to DuberyMNL landing page for order tracking.",
    },
    "retell ai": {
        "difficulty": "medium", "time": "1 week",
        "connection": "Voice AI agent. Extends your chatbot (WF4) from text to voice.",
        "project": "Build a voice-based product inquiry bot for DuberyMNL.",
    },
    "vapi": {
        "difficulty": "medium", "time": "1 week",
        "connection": "Similar to Retell -- voice agent platform. Hot on Upwork.",
        "project": "Voice receptionist demo that hands off to Claude for complex queries.",
    },
    "langchain": {
        "difficulty": "medium", "time": "3-5 days",
        "connection": "LLM orchestration framework. Your WAT framework is the same concept.",
        "project": "Rebuild one DuberyMNL workflow using LangChain to compare approaches.",
    },
    "rag": {
        "difficulty": "medium", "time": "1 week",
        "connection": "Retrieval Augmented Generation. Powers smarter chatbots (WF4 upgrade).",
        "project": "Build a RAG chatbot for DuberyMNL product FAQs using embeddings.",
    },
    "ghl": {
        "difficulty": "easy", "time": "2-3 days",
        "connection": "GoHighLevel CRM. Popular with agencies. Your CRM experience transfers.",
        "project": "Set up a GHL pipeline with n8n automation for a demo client.",
    },
    "openai": {
        "difficulty": "easy", "time": "1 day",
        "connection": "Same patterns as Claude API. You already know LLM integration.",
        "project": "Add OpenAI fallback to your content pipeline for model comparison.",
    },
    "airtable": {
        "difficulty": "easy", "time": "1-2 days",
        "connection": "Structured database like Notion/Sheets. n8n has native nodes.",
        "project": "Mirror your pipeline tracking in Airtable to demo cross-platform skills.",
    },
    "docker": {
        "difficulty": "easy", "time": "2-3 days",
        "connection": "You already use Docker for n8n. Just need to formalize the knowledge.",
        "project": "Dockerize the DuberyMNL tool stack for reproducible deployment.",
    },
    "nextjs": {
        "difficulty": "hard", "time": "2-3 weeks",
        "connection": "React framework. Your JS basics help but React is a bigger leap.",
        "project": "Rebuild the DuberyMNL landing page in Next.js for portfolio variety.",
    },
    "typescript": {
        "difficulty": "medium", "time": "1 week",
        "connection": "Typed JavaScript. Makes your JS skills more marketable.",
        "project": "Rewrite the dashboard frontend scripts in TypeScript.",
    },
    "selenium": {
        "difficulty": "easy", "time": "2-3 days",
        "connection": "Browser automation. You already use Playwright which is better.",
        "project": "You already have this covered with Playwright. Skip unless job requires it.",
    },
    "playwright": {
        "difficulty": "easy", "time": "already known",
        "connection": "You already use it. Make sure it's listed on your Upwork profile.",
        "project": "Already built -- web scraping tools in your stack.",
    },
    "notion api": {
        "difficulty": "easy", "time": "already known",
        "connection": "You already use Notion MCP + sync_pipeline.py.",
        "project": "Already built -- Notion dashboard sync.",
    },
}


# ============================================================
# Analysis
# ============================================================

def load_skills_log():
    """Load accumulated skill data from Active Scout runs."""
    if not SKILLS_LOG.exists():
        return []
    try:
        with open(SKILLS_LOG) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def analyze_scout_data(log, days=7):
    """Analyze skill frequencies from the last N days of scout runs."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    recent = [e for e in log if e.get("date", "") > cutoff]

    if not recent:
        return None

    # Aggregate skill counts
    skill_counts = Counter()
    total_jobs = 0
    source_counts = Counter()
    hourly_rates = []
    fixed_rates = []

    for entry in recent:
        for skill, count in entry.get("skills", {}).items():
            skill_counts[skill] += count
        total_jobs += entry.get("total_jobs", 0)
        for source, count in entry.get("sources", {}).items():
            source_counts[source] += count
        if entry.get("budgets", {}).get("hourly_avg"):
            hourly_rates.append(entry["budgets"]["hourly_avg"])
        if entry.get("budgets", {}).get("fixed_avg"):
            fixed_rates.append(entry["budgets"]["fixed_avg"])

    return {
        "period_days": days,
        "runs": len(recent),
        "total_jobs": total_jobs,
        "skill_counts": skill_counts,
        "source_counts": source_counts,
        "avg_hourly": round(sum(hourly_rates) / len(hourly_rates), 1) if hourly_rates else None,
        "avg_fixed": round(sum(fixed_rates) / len(fixed_rates), 1) if fixed_rates else None,
    }


def parse_web_trends(results):
    """Parse WebSearch trend data into skill mentions."""
    extra_skills = Counter()
    for r in results:
        text = f"{r.get('title', '')} {r.get('snippet', '')}".lower()
        # Check for learnable skills in trend data
        for skill in LEARNABLE_SKILLS:
            if skill in text:
                extra_skills[skill] += 1
        # Also check RA's existing skills
        for skill in RA_SKILLS:
            if skill in text:
                extra_skills[skill] += 1
    return extra_skills


def build_report(scout_data, web_trends=None):
    """Build the market intel report."""
    now = datetime.now()
    week_start = (now - timedelta(days=now.weekday())).strftime("%b %d")

    r = f"<b>MARKET SNAPSHOT</b>\nWeek of {week_start}, {now.year}\n"

    # Combine data sources
    all_skills = Counter()
    if scout_data:
        all_skills.update(scout_data["skill_counts"])
    if web_trends:
        all_skills.update(web_trends)

    if not all_skills:
        r += "\nNo data yet. Run Active Scout with --save-skills to start collecting.\n"
        return r, None

    top_skills = all_skills.most_common(15)

    # Skills in Demand
    r += "\n<b>== SKILLS IN DEMAND ==</b>\n"
    r += "Skill | Freq | RA? | Learn | Time\n"
    r += "-" * 45 + "\n"

    coverage_count = 0
    missing = []

    for skill, freq in top_skills[:10]:
        has_it = skill in RA_SKILLS
        if has_it:
            coverage_count += 1
            learn = "--"
            time_est = "--"
        elif skill in LEARNABLE_SKILLS:
            info = LEARNABLE_SKILLS[skill]
            learn = info["difficulty"]
            time_est = info["time"]
            missing.append((skill, info))
        else:
            learn = "?"
            time_est = "?"
            missing.append((skill, None))

        check = "YES" if has_it else "no"
        r += f"  {skill:<20} {freq:>3}x  {check:<4} {learn:<7} {time_est}\n"

    # Coverage
    total_top = min(10, len(top_skills))
    coverage_pct = round(coverage_count / total_top * 100) if total_top else 0

    r += f"\n<b>== RA'S COVERAGE ==</b>\n"
    r += f"  {coverage_pct}% of top {total_top} skills covered\n"

    if missing:
        # Easiest win
        easy = [(s, i) for s, i in missing if i and i["difficulty"] == "easy"]
        if easy:
            r += f"  Easiest win: {easy[0][0]} ({easy[0][1]['time']})\n"
        # Biggest gap (highest frequency missing skill)
        r += f"  Biggest gap: {missing[0][0]} (appeared {all_skills[missing[0][0]]}x)\n"

    # Budget trends
    if scout_data:
        r += f"\n<b>== BUDGET TRENDS ==</b>\n"
        r += f"  Scout runs: {scout_data['runs']} (last {scout_data['period_days']} days)\n"
        r += f"  Jobs scanned: {scout_data['total_jobs']}\n"
        if scout_data["avg_hourly"]:
            r += f"  Avg hourly: ${scout_data['avg_hourly']}/hr\n"
        if scout_data["avg_fixed"]:
            r += f"  Avg fixed: ${scout_data['avg_fixed']}\n"
        if scout_data["source_counts"]:
            r += f"  Sources: {', '.join(f'{s}({c})' for s, c in scout_data['source_counts'].most_common(5))}\n"

    # Recommended Next Skills
    r += f"\n<b>== RECOMMENDED NEXT SKILLS ==</b>\n"
    recs = []
    for skill, info in missing[:5]:
        if info:
            recs.append((skill, info))
    if not recs:
        # Fallback: suggest from LEARNABLE_SKILLS by frequency in any data
        for skill in ["rag", "supabase", "vapi", "retell ai", "ghl"]:
            if skill in LEARNABLE_SKILLS:
                recs.append((skill, LEARNABLE_SKILLS[skill]))
            if len(recs) >= 3:
                break

    for skill, info in recs[:3]:
        r += f"\n  <b>{skill.upper()}</b> ({info['difficulty']}, {info['time']})\n"
        r += f"    Why: {info['connection']}\n"
        r += f"    First project: {info['project']}\n"

    # Dashboard data structure
    dashboard_data = {
        "updated": now.strftime("%Y-%m-%d"),
        "coverage_pct": coverage_pct,
        "top_skills": [{"skill": s, "freq": f, "has_it": s in RA_SKILLS} for s, f in top_skills[:10]],
        "missing": [{"skill": s, "difficulty": i["difficulty"] if i else "unknown",
                      "time": i["time"] if i else "unknown"}
                     for s, i in missing[:5]],
        "avg_hourly": scout_data["avg_hourly"] if scout_data else None,
        "avg_fixed": scout_data["avg_fixed"] if scout_data else None,
        "total_jobs_scanned": scout_data["total_jobs"] if scout_data else 0,
    }

    return r, dashboard_data


# ============================================================
# Delivery
# ============================================================

def write_dashboard(intel_data):
    """Write market intel to dashboard-data.json -> briefing.market_intel."""
    if not DASHBOARD_FILE.exists():
        print(f"Dashboard file not found: {DASHBOARD_FILE}", file=sys.stderr)
        return False
    try:
        with open(DASHBOARD_FILE) as f:
            data = json.load(f)
        if "briefing" not in data:
            data["briefing"] = {}
        data["briefing"]["market_intel"] = intel_data
        with open(DASHBOARD_FILE, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("  Dashboard updated (briefing.market_intel)", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Dashboard write failed: {e}", file=sys.stderr)
        return False


def send_telegram(report):
    sys.path.insert(0, str(Path.home() / "projects/ra-dashboard/tools/telegram"))
    from send_message import send_to_ra
    if len(report) <= 4096:
        return send_to_ra(report)
    chunks, cur = [], ""
    for line in report.split("\n"):
        if len(cur) + len(line) + 1 > 4000:
            chunks.append(cur)
            cur = ""
        cur += line + "\n"
    if cur:
        chunks.append(cur)
    return all(send_to_ra(c) for c in chunks)


# ============================================================
# Main
# ============================================================

def main():
    p = argparse.ArgumentParser(description="Market Intel for RA's Job Hunt")
    p.add_argument("--telegram", "-t", action="store_true")
    p.add_argument("--web", help="JSON file with WebSearch trend results")
    p.add_argument("--dashboard", action="store_true",
                   help="Write intel to dashboard-data.json")
    p.add_argument("--days", type=int, default=7,
                   help="Lookback period in days (default: 7)")
    args = p.parse_args()

    # Load scout data
    log = load_skills_log()
    scout_data = analyze_scout_data(log, days=args.days)

    if scout_data:
        print(f"Loaded {scout_data['runs']} scout runs ({scout_data['total_jobs']} jobs)", file=sys.stderr)
    else:
        print("No scout data found. Run Active Scout with --save-skills first.", file=sys.stderr)

    # Load web trends if provided
    web_trends = None
    if args.web:
        with open(args.web) as f:
            web_trends = parse_web_trends(json.load(f))
        print(f"  WebSearch trends: {sum(web_trends.values())} mentions", file=sys.stderr)

    # Build report
    report, intel_data = build_report(scout_data, web_trends)
    print(report)

    # Write to dashboard
    if args.dashboard and intel_data:
        write_dashboard(intel_data)

    # Send via Telegram
    if args.telegram:
        if send_telegram(report):
            print("\nSent via Telegram.", file=sys.stderr)
        else:
            print("\nTelegram send failed.", file=sys.stderr)


if __name__ == "__main__":
    main()
