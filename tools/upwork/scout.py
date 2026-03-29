#!/usr/bin/env python3
"""
Job Scout -- finds, screens, and categorizes remote jobs for RA.

Sources:
  - RemoteOK API (automatic, free, real dates)
  - WebSearch results (agent feeds via --web-results)

Usage:
  python3 scout.py                        # Fetch RemoteOK, print report
  python3 scout.py --telegram             # Also send via Telegram
  python3 scout.py --web-results f.json   # Include WebSearch results
  python3 scout.py --no-dedup             # Show previously seen jobs too
  python3 scout.py --reset-seen           # Clear seen job cache
"""

import json, sys, re, os, argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import urlopen, Request
from collections import Counter

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
SEEN_FILE = PROJECT_DIR / ".tmp" / "scout_seen.json"

# ============================================================
# RA's Profile
# ============================================================

SKILLS = {
    "ai automation": 3, "n8n": 3, "claude": 3, "ai agent": 3,
    "agentic": 3, "workflow automation": 3, "python": 2,
    "meta ads": 2, "facebook ads": 2, "chatbot": 2,
    "landing page": 2, "fastapi": 2, "crm": 2,
    "make.com": 2, "zapier": 2, "api integration": 2,
    "telegram": 2, "google sheets": 1, "web scraping": 1,
    "social media": 1, "e-commerce": 1, "javascript": 1,
    "content automation": 2, "content pipeline": 2,
    "automation": 2, "ai": 1,
}

EXCLUDE = [
    "salesforce", "sap", ".net", "c#", "angular",
    "react native", "ios developer", "android developer",
    "unity", "unreal", "blockchain", "solidity",
    "machine learning engineer", "deep learning", "pytorch",
    "tensorflow", "kubernetes", "devops engineer",
    "data scientist", "phd required", "tableau", "power bi",
    "ruby on rails", "golang", "scala",
]

PORTFOLIO = {
    "ai automation": "DuberyMNL agentic social media pipeline",
    "n8n": "DuberyMNL automation workflows (WF1-WF4)",
    "claude": "Claude Code agentic system (15+ skills)",
    "workflow automation": "End-to-end content pipeline",
    "chatbot": "WF4 Messenger chatbot (Claude + Flask)",
    "meta ads": "Meta Ads campaign mgmt (Traffic v2)",
    "facebook ads": "Meta Ads with staging + insights",
    "landing page": "DuberyMNL landing page (mobile-first)",
    "ai agent": "Multi-agent system: moderator + Belle + Rasclaw",
    "crm": "Pipeline tracking (Sheets + Notion + JSON)",
    "python": "20+ Python tools ecosystem",
    "api integration": "Meta, Drive, kie.ai, Telegram APIs",
    "social media": "Social media automation + dayparting",
    "automation": "Full automation stack (DuberyMNL)",
    "content": "Content generation pipeline",
}


# ============================================================
# Fetch
# ============================================================

def strip_html(text):
    return re.sub(r"<[^>]+>", " ", text)


def fetch_remoteok():
    """Fetch relevant jobs from RemoteOK API (last 48h)."""
    req = Request("https://remoteok.com/api",
                  headers={"User-Agent": "RA-JobScout/1.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"RemoteOK fetch failed: {e}", file=sys.stderr)
        return []

    # First element is legal notice metadata
    if data and isinstance(data[0], dict) and "legal" in json.dumps(data[0]).lower():
        data = data[1:]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    jobs = []

    for item in data:
        epoch = item.get("epoch", 0)
        if datetime.fromtimestamp(epoch, tz=timezone.utc) < cutoff:
            continue

        text = f"{item.get('position', '')} {' '.join(item.get('tags', []))}".lower()
        desc = strip_html(item.get("description", "")).lower()
        full = f"{text} {desc}"

        if not any(s in full for s in SKILLS):
            continue
        if any(e in full for e in EXCLUDE):
            continue

        # Annual salary to hourly estimate
        sal_min = item.get("salary_min", 0) or 0
        sal_max = item.get("salary_max", 0) or 0
        hourly = round((sal_min + sal_max) / 2 / 2080) if sal_max > 0 else None

        jobs.append({
            "id": f"rok_{item['id']}",
            "title": item.get("position", ""),
            "company": item.get("company", ""),
            "url": item.get("apply_url", item.get("url", "")),
            "description": desc[:500],
            "tags": item.get("tags", []),
            "budget": hourly,
            "budget_type": "hourly" if hourly else None,
            "salary_range": f"${sal_min:,}-${sal_max:,}/yr" if sal_max else None,
            "posted": item.get("date", ""),
            "source": "RemoteOK",
            "duration": "", "hours": "", "contract_type": "",
        })

    return jobs


def fetch_jobicy():
    """Fetch relevant jobs from Jobicy API (last 48h)."""
    req = Request("https://jobicy.com/api/v2/remote-jobs?count=50",
                  headers={"User-Agent": "RA-JobScout/1.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"Jobicy fetch failed: {e}", file=sys.stderr)
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    jobs = []

    for item in data.get("jobs", []):
        # Parse date -- format: "2026-03-29 14:00:00"
        try:
            pub = datetime.strptime(item.get("pubDate", "")[:19], "%Y-%m-%d %H:%M:%S")
            pub = pub.replace(tzinfo=timezone.utc)
            if pub < cutoff:
                continue
        except (ValueError, TypeError):
            continue

        title = item.get("jobTitle", "")
        company = item.get("companyName", "")
        desc = strip_html(item.get("jobExcerpt", "") or item.get("jobDescription", "")).lower()
        full = f"{title.lower()} {desc}"

        if not any(s in full for s in SKILLS):
            continue
        if any(e in full for e in EXCLUDE):
            continue

        # Salary
        sal_min = item.get("annualSalaryMin", "") or ""
        sal_max = item.get("annualSalaryMax", "") or ""
        hourly = None
        sal_range = None
        if sal_max:
            try:
                hourly = round((int(sal_min or 0) + int(sal_max)) / 2 / 2080)
                sal_range = f"${sal_min}-${sal_max}/yr"
            except (ValueError, TypeError):
                pass

        job_type = item.get("jobType", [])
        if isinstance(job_type, list):
            job_type = ", ".join(job_type)

        jobs.append({
            "id": f"jcy_{item.get('id', '')}",
            "title": title,
            "company": company,
            "url": item.get("url", ""),
            "description": desc[:500],
            "tags": [],
            "budget": hourly,
            "budget_type": "hourly" if hourly else None,
            "salary_range": sal_range,
            "posted": item.get("pubDate", "")[:10],
            "source": "Jobicy",
            "duration": "", "hours": "", "contract_type": job_type,
        })

    return jobs


def fetch_wwr():
    """Fetch relevant jobs from We Work Remotely RSS (last 48h)."""
    feeds = [
        "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
        "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
        "https://weworkremotely.com/remote-jobs.rss",
    ]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    jobs = []
    seen_urls = set()

    for feed_url in feeds:
        req = Request(feed_url, headers={"User-Agent": "RA-JobScout/1.0"})
        try:
            with urlopen(req, timeout=15) as resp:
                root = ET.fromstring(resp.read())
        except Exception as e:
            print(f"WWR feed failed ({feed_url.split('/')[-1]}): {e}", file=sys.stderr)
            continue

        for item in root.findall(".//item"):
            link = item.findtext("link", "")
            if link in seen_urls:
                continue
            seen_urls.add(link)

            # Parse date -- format: "Wed, 25 Mar 2026 20:21:42 +0000"
            try:
                pub = parsedate_to_datetime(item.findtext("pubDate", ""))
                if pub < cutoff:
                    continue
            except (ValueError, TypeError):
                continue

            title = item.findtext("title", "")
            desc = strip_html(item.findtext("description", "") or "").lower()
            full = f"{title.lower()} {desc}"

            if not any(s in full for s in SKILLS):
                continue
            if any(e in full for e in EXCLUDE):
                continue

            # Extract company from title "Company: Job Title" format
            company = ""
            if ": " in title:
                parts = title.split(": ", 1)
                company = parts[0].strip()
                title = parts[1].strip()

            # WWR job ID from URL
            slug = link.rstrip("/").split("/")[-1]

            jobs.append({
                "id": f"wwr_{slug}",
                "title": title,
                "company": company,
                "url": link,
                "description": desc[:500],
                "tags": [],
                "budget": None,
                "budget_type": None,
                "salary_range": None,
                "posted": pub.strftime("%Y-%m-%d"),
                "source": "WWR",
                "duration": "", "hours": "", "contract_type": "",
            })

    return jobs


def parse_web_results(results):
    """Parse WebSearch results into job structs."""
    jobs = []
    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        snippet = r.get("snippet", "")

        if not any(x in url for x in ["/freelance-jobs/", "/jobs/", "/job/"]):
            continue
        if any(x in url for x in ["/hire/", "/services/", "/profile/"]):
            continue

        source = "Upwork"
        if "linkedin" in url: source = "LinkedIn"
        elif "onlinejobs" in url: source = "OnlineJobs.ph"
        elif "jobstreet" in url: source = "Jobstreet"
        elif "weworkremotely" in url: source = "WWR"

        meta = _parse_upwork_title(title) if source == "Upwork" else {}
        jid = re.search(r"~(\d+)", url)
        jid = jid.group(1) if jid else re.sub(r"[^a-zA-Z0-9]", "", url[-30:])

        jobs.append({
            "id": f"web_{jid}",
            "title": meta.get("clean_title", title.split(" - ")[0].strip()),
            "company": "", "url": url, "description": snippet,
            "tags": [], "budget": meta.get("budget"),
            "budget_type": meta.get("budget_type"),
            "salary_range": None, "posted": meta.get("posted", ""),
            "duration": meta.get("duration", ""),
            "hours": meta.get("hours", ""),
            "contract_type": meta.get("contract_type", ""),
            "source": source,
        })
    return jobs


def _parse_upwork_title(title):
    meta = {}
    m = re.search(r"\$([\d,]+(?:\.\d{2})?)\s*(Fixed Price|/hr)", title)
    if m:
        meta["budget"] = float(m.group(1).replace(",", ""))
        meta["budget_type"] = "fixed" if "Fixed" in m.group(2) else "hourly"
    if "More than 30 hrs" in title: meta["hours"] = "30+"
    elif "Less than 30 hrs" in title: meta["hours"] = "<30"
    m = re.search(r"(More than 6 months|3 to 6 months|1 to 3 months|Less than 1 month)", title)
    if m: meta["duration"] = m.group(1)
    if "Contract to Hire" in title: meta["contract_type"] = "Contract to Hire"
    m = re.search(r"posted\s+([\w\s,]+\d{4})", title)
    if m: meta["posted"] = m.group(1).strip()
    meta["clean_title"] = re.split(r"\s*-\s*Freelance Job", title)[0].strip()
    return meta


# ============================================================
# Scoring
# ============================================================

def score_job(job):
    text = f"{job['title']} {job.get('description', '')} {' '.join(job.get('tags', []))}".lower()

    # Skill fit
    matched = [s for s in SKILLS if s in text]
    weight = sum(SKILLS[s] for s in matched)
    if weight >= 8: skill_fit = 5
    elif weight >= 5: skill_fit = 4
    elif weight >= 3: skill_fit = 3
    elif weight >= 1: skill_fit = 2
    else: skill_fit = 1

    # Portfolio proof
    proofs = list(set(PORTFOLIO[k] for k in PORTFOLIO if k in text))[:3]
    if len(proofs) >= 3: portfolio = 5
    elif len(proofs) >= 2: portfolio = 4
    elif len(proofs) >= 1: portfolio = 3
    else: portfolio = 2

    # Budget
    b = job.get("budget")
    bt = job.get("budget_type")
    if b is None: budget_score = 3
    elif bt == "fixed":
        if b >= 500: budget_score = 5
        elif b >= 200: budget_score = 4
        elif b >= 100: budget_score = 3
        elif b >= 50: budget_score = 2
        else: budget_score = 1
    else:
        if b >= 30: budget_score = 5
        elif b >= 20: budget_score = 4
        elif b >= 15: budget_score = 3
        elif b >= 10: budget_score = 2
        else: budget_score = 1

    # Comfort
    comfort = 3
    if any(w in text for w in ["startup", "small business", "solo founder", "simple"]):
        comfort += 1
    if any(w in text for w in ["urgent", "asap", "enterprise", "senior engineer", "lead", "10+ years"]):
        comfort -= 1
    comfort = max(1, min(5, comfort))

    # Growth
    growth = 2
    if job.get("contract_type") == "Contract to Hire": growth += 2
    if "6 months" in str(job.get("duration", "")): growth += 1
    if "30+" in str(job.get("hours", "")): growth += 1
    growth = max(1, min(5, growth))

    avg = round((skill_fit + portfolio + budget_score + comfort + growth) / 5, 1)
    job["scores"] = {
        "skill_fit": skill_fit, "portfolio": portfolio, "budget": budget_score,
        "comfort": comfort, "growth": growth, "average": avg,
    }
    job["_matched"] = matched[:5]
    job["_proofs"] = proofs
    return job


# ============================================================
# Report
# ============================================================

def generate_report(jobs):
    apply_now = sorted([j for j in jobs if j["scores"]["average"] >= 3.5],
                       key=lambda j: j["scores"]["average"], reverse=True)
    consider = sorted([j for j in jobs if 2.5 <= j["scores"]["average"] < 3.5],
                      key=lambda j: j["scores"]["average"], reverse=True)
    skip = [j for j in jobs if j["scores"]["average"] < 2.5]

    now = datetime.now().strftime("%b %d, %Y %I:%M %p")
    r = f"<b>JOB SCOUT REPORT</b>\n{now} PHT\n"

    r += f"\n<b>== APPLY NOW ({len(apply_now)}) ==</b>\n"
    for j in apply_now:
        r += _fmt(j)
    if not apply_now:
        r += "No strong matches this round.\n"

    r += f"\n<b>== WORTH CONSIDERING ({len(consider)}) ==</b>\n"
    for j in consider:
        r += _fmt(j)
    if not consider:
        r += "None.\n"

    if skip:
        r += f"\n<b>== SKIP ({len(skip)}) ==</b>\n"
        for j in skip[:5]:
            r += f"- {j['title'][:60]}\n"
        if len(skip) > 5:
            r += f"  ...and {len(skip) - 5} more\n"

    r += f"\n<b>== STATS ==</b>\n"
    r += f"Scanned: {len(jobs)} | Apply: {len(apply_now)} | Consider: {len(consider)} | Skip: {len(skip)}\n"

    all_skills = []
    for j in jobs:
        all_skills.extend(j.get("_matched", []))
    if all_skills:
        top = Counter(all_skills).most_common(3)
        r += f"Trending: {', '.join(f'{s}({c})' for s, c in top)}\n"

    return r


def _fmt(job):
    s = job["scores"]
    if job.get("salary_range"):
        bstr = job["salary_range"]
    elif job.get("budget"):
        bt = "Fixed" if job.get("budget_type") == "fixed" else "/hr"
        bstr = f"${job['budget']:,.0f}{bt}"
    else:
        bstr = "Budget N/A"

    line = f"\n<b>{job['title'][:80]}</b>"
    if job.get("company"):
        line += f" @ {job['company']}"
    line += f"\n  {bstr} | {job['source']} | Score: {s['average']}/5"
    if job["_proofs"]:
        line += f"\n  Proof: {job['_proofs'][0]}"
    line += f"\n  {job['url']}\n"
    return line


# ============================================================
# Dedup & Delivery
# ============================================================

def load_seen():
    if SEEN_FILE.exists():
        with open(SEEN_FILE) as f:
            return json.load(f)
    return {}


def save_seen(seen):
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)


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

def save_skills_log(jobs):
    """Append matched skill frequencies to rolling log for Market Intel."""
    log_file = PROJECT_DIR / ".tmp" / "scout_skills_log.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log = []
    if log_file.exists():
        try:
            with open(log_file) as f:
                log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log = []

    entry = {
        "date": datetime.now().isoformat(),
        "total_jobs": len(jobs),
        "skills": dict(Counter(s for j in jobs for s in j.get("_matched", []))),
        "sources": dict(Counter(j.get("source", "unknown") for j in jobs)),
        "budgets": {
            "hourly_avg": None,
            "fixed_avg": None,
        },
    }

    hourly = [j["budget"] for j in jobs if j.get("budget") and j.get("budget_type") == "hourly"]
    fixed = [j["budget"] for j in jobs if j.get("budget") and j.get("budget_type") == "fixed"]
    if hourly:
        entry["budgets"]["hourly_avg"] = round(sum(hourly) / len(hourly), 1)
    if fixed:
        entry["budgets"]["fixed_avg"] = round(sum(fixed) / len(fixed), 1)

    log.append(entry)

    # Keep last 30 days
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    log = [e for e in log if e.get("date", "") > cutoff]

    with open(log_file, "w") as f:
        json.dump(log, f, indent=2)
    print(f"  Skills log updated ({len(log)} entries)", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description="Job Scout for RA")
    p.add_argument("--telegram", "-t", action="store_true")
    p.add_argument("--web-results", help="JSON file with WebSearch results")
    p.add_argument("--no-dedup", action="store_true")
    p.add_argument("--reset-seen", action="store_true")
    p.add_argument("--save-skills", action="store_true",
                   help="Save skill frequencies to log for Market Intel")
    args = p.parse_args()

    if args.reset_seen:
        if SEEN_FILE.exists():
            SEEN_FILE.unlink()
        print("Seen cache cleared.")
        return

    jobs = []

    # Primary sources (free APIs, real dates)
    print("Fetching RemoteOK...", file=sys.stderr)
    rok = fetch_remoteok()
    print(f"  RemoteOK: {len(rok)} jobs (last 48h)", file=sys.stderr)
    jobs.extend(rok)

    print("Fetching Jobicy...", file=sys.stderr)
    jcy = fetch_jobicy()
    print(f"  Jobicy: {len(jcy)} jobs (last 48h)", file=sys.stderr)
    jobs.extend(jcy)

    print("Fetching We Work Remotely...", file=sys.stderr)
    wwr = fetch_wwr()
    print(f"  WWR: {len(wwr)} jobs (last 48h)", file=sys.stderr)
    jobs.extend(wwr)

    # Optional: WebSearch supplement (stale but catches Upwork/LinkedIn)
    if args.web_results:
        with open(args.web_results) as f:
            web = parse_web_results(json.load(f))
        print(f"  WebSearch: {len(web)} jobs (supplement)", file=sys.stderr)
        jobs.extend(web)

    if not jobs:
        print("No matching jobs found.")
        return

    # Dedup within run
    seen_ids = set()
    unique = []
    for j in jobs:
        if j["id"] not in seen_ids:
            seen_ids.add(j["id"])
            unique.append(j)
    jobs = unique

    # Dedup across runs
    if not args.no_dedup:
        seen = load_seen()
        new = [j for j in jobs if j["id"] not in seen]
        skipped = len(jobs) - len(new)
        if skipped:
            print(f"  Filtered {skipped} previously seen", file=sys.stderr)
        jobs = new
        for j in jobs:
            seen[j["id"]] = datetime.now().isoformat()
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        seen = {k: v for k, v in seen.items() if v > cutoff}
        save_seen(seen)

    if not jobs:
        print("All jobs already seen. Use --no-dedup to review again.")
        return

    # Score & report
    for job in jobs:
        score_job(job)

    report = generate_report(jobs)
    print(report)

    if args.save_skills:
        save_skills_log(jobs)

    if args.telegram:
        if send_telegram(report):
            print("\nSent via Telegram.", file=sys.stderr)
        else:
            print("\nTelegram send failed.", file=sys.stderr)


if __name__ == "__main__":
    main()
