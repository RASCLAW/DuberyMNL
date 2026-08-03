"""OJ job-board scout -- card-boundary-safe parser. Public pages only."""
import html
import json
import os
import random
import re
import subprocess
import time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")


def strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def fetch(url, cache):
    if os.path.exists(cache):
        return open(cache, encoding="utf-8", errors="replace").read()
    out = subprocess.run(["curl", "-s", "--max-time", "35", "-A", UA, url],
                         capture_output=True).stdout.decode("utf-8", "replace")
    open(cache, "w", encoding="utf-8").write(out)
    time.sleep(random.uniform(2.5, 4.0))
    return out


def parse(page):
    jobs = []
    # One card per <!-- Start --> ... <!-- End --> block: no cross-card bleed.
    for block in re.split(r"<!--\s*Start\s*-->", page)[1:]:
        block = re.split(r"<!--\s*End\s*-->", block)[0]
        href = re.search(r'href="(/jobseekers/job/[^"]+)"', block)
        h4 = re.search(r"<h4[^>]*>(.*?)</h4>", block, re.S)
        if not (href and h4):
            continue
        sal = re.search(r'<dd class="col">(.*?)</dd>', block, re.S)
        posted = re.search(r"<em>Posted on ([\d\- :]+)</em>", block)
        title = strip(h4.group(1))
        jtype = ""
        for t in ("Full Time", "Part Time", "Gig", "Any"):
            if title.endswith(t):
                title, jtype = title[: -len(t)].strip(), t
                break
        jobs.append({"id": href.group(1).rsplit("-", 1)[-1], "title": title,
                     "type": jtype, "salary": strip(sal.group(1)) if sal else "",
                     "posted": posted.group(1) if posted else "",
                     "url": "https://www.onlinejobs.ph" + href.group(1)})
    return jobs


KEYWORDS = ["n8n", "zapier", "make.com", "ai automation", "automation",
            "ai agent", "workflow", "chatbot", "prompt engineer",
            "ai image", "image generation", "midjourney", "python", "openai"]

os.makedirs("ojcache", exist_ok=True)
seen, rows = set(), []
for kw in KEYWORDS:
    url = ("https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword="
           + kw.replace(" ", "+"))
    jobs = parse(fetch(url, f"ojcache/{kw.replace('.','_').replace(' ','_')}.html"))
    new = [j for j in jobs if j["id"] not in seen]
    for j in new:
        seen.add(j["id"])
        j["kw"] = kw
        rows.append(j)
    print(f"{kw:18} parsed={len(jobs):3}  new={len(new):3}")

json.dump(rows, open("oj_jobs2.json", "w", encoding="utf-8"), indent=2)
print(f"\nunique: {len(rows)} -> oj_jobs2.json")
# Spot-check pairing integrity.
print("\nspot check (title <-> url slug must agree):")
for j in rows[:5]:
    print(f"  {j['title'][:44]:46} | {j['salary'][:18]:20} | {j['url'].rsplit('/',1)[-1][:40]}")
