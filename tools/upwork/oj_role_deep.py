"""Deep scan of OnlineJobs.ph for AI IMAGE GENERATION roles.

Public pages only, no login. Sweeps keywords, filters to image-gen roles,
then fetches each job's full detail page.
"""
import html
import json
import os
import random
import re
import subprocess
import time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")
os.makedirs("ojcache2", exist_ok=True)


def strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def get(url, cache):
    p = os.path.join("ojcache2", cache)
    if os.path.exists(p):
        return open(p, encoding="utf-8", errors="replace").read()
    out = subprocess.run(["curl", "-s", "--max-time", "35", "-A", UA, url],
                         capture_output=True).stdout.decode("utf-8", "replace")
    open(p, "w", encoding="utf-8").write(out)
    time.sleep(random.uniform(2.2, 3.6))
    return out


def cards(page):
    rows = []
    for blk in re.split(r"<!--\s*Start\s*-->", page)[1:]:
        blk = re.split(r"<!--\s*End\s*-->", blk)[0]
        h = re.search(r'href="(/jobseekers/job/[^"]+)"', blk)
        t = re.search(r"<h4[^>]*>(.*?)</h4>", blk, re.S)
        if not (h and t):
            continue
        title = strip(t.group(1))
        for k in ("Full Time", "Part Time", "Gig", "Any"):
            if title.endswith(k):
                title = title[: -len(k)].strip()
        rows.append({"id": h.group(1).rsplit("-", 1)[-1], "title": title,
                     "url": "https://www.onlinejobs.ph" + h.group(1)})
    return rows


KEYWORDS = ["ai image", "image generation", "midjourney", "nano banana",
            "product image", "ai photo", "stable diffusion", "flux ai",
            "ai art", "product photography", "ecommerce image", "dalle",
            "leonardo ai", "ideogram", "image editing", "ai creative",
            "generative", "photo generation"]

IMG = re.compile(
    r"ai image|image gen|generat\w* image|midjourney|nano banana|stable diffusion|"
    r"\bflux\b|dall.?e|leonardo|ideogram|ai art|ai photo|product photo|"
    r"ai creative|generative|prompt engineer|photo edit|image edit", re.I)

pool = {}
for kw in KEYWORDS:
    url = "https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=" + kw.replace(" ", "+")
    for j in cards(get(url, f"s_{kw.replace(' ', '_')}.html")):
        pool.setdefault(j["id"], j)
print(f"swept {len(KEYWORDS)} keywords -> {len(pool)} unique jobs")

hits = [j for j in pool.values() if IMG.search(j["title"])]
print(f"image/creative-AI titles: {len(hits)}\n")

FIELDS = ["TYPE OF WORK", "WAGE / SALARY", "HOURS PER WEEK", "DATE UPDATED"]
out = []
for j in hits:
    raw = get(j["url"], f"d_{j['id']}.html")
    t2 = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S)
    txt = re.sub(r"\n\s*\n+", "\n", html.unescape(re.sub(r"<[^>]+>", "\n", t2))).strip()
    rec = dict(j)
    for f in FIELDS:
        m = re.search(re.escape(f) + r"\s*\n\s*(.+)", txt)
        rec[f] = m.group(1).strip() if m else ""
    i = txt.find("JOB OVERVIEW")
    body = txt[i:i + 4000] if i >= 0 else ""
    body = re.split(r"SKILL REQUIREMENT|VIEW OTHER JOB POSTS|Please\s*\nlogin", body)[0]
    rec["body"] = re.sub(r"\n{2,}", "\n", body).strip()
    out.append(rec)
    print(f"  [{rec['WAGE / SALARY'][:18]:20}] {rec['title'][:62]}")

json.dump(out, open("oj_image_jobs.json", "w", encoding="utf-8"), indent=2)
print(f"\nsaved {len(out)} detailed roles -> oj_image_jobs.json")
