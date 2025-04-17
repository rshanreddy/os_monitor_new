# weekly_osmonitor.py

import os
from datetime import datetime
import pandas as pd
import logging
import math

from core_monitor import run_repo_tracking, openai_client, post_to_basecamp

def get_web_signals(repo_name):
    # TO DO: implement web signals retrieval
    return {"maintainer_info": []}

def generate_weekly_analysis(df):
    """
    Summarize the top 5 AI repos by weekly % star growth.
    """
    # First get web signals for top repos by weekly growth
    top_repos = df.nlargest(5, 'weekly_diff')
    web_signals = {}
    for _, row in top_repos.iterrows():
        web_signals[row['repo_name']] = get_web_signals(row['repo_name'])

    # Build the prompt in parts to avoid string formatting issues
    header = """You are a **seed‑stage VC partner** at **True Ventures** with 20+ years of investing experience.
You've led seed rounds into Blue Bottle coffee before specialty coffee existed, Wordpress before a big OS project had ever been commercialized, and more.
You can see the potential for products driving large markets sometimes even before a founder can.  

Input: a Pandas `DataFrame` where each row is a GitHub repo, plus web signals data.
Columns (fill missing numerics with 0, missing dates with "1970‑01‑01"):
`repo_name, stars, weekly_diff, weekly_pct, created_at, language, topics,
 description, sponsors, contributors, commits_7d, issues_closed_7d`."""

    data_section = f"""
Web signals for each repo:
{web_signals}

──────────────── INPUT DATA ────────────────
{df.to_markdown(index=False)}
────────────────────────────────────────────"""

    scoring_section = """
################ 1 · FILTERS ################
DROP any repo that matches at least one of:
• **Aggregator / reference** – regex `(awesome|papers|list|collection|curated|spec)`  
• **License** – not permissive (`MIT`,`Apache`,`BSD`,`MPL`)  
• **Corp‑owned** – org has >50 public members (if `org_size`)  
• **Clearly non‑AI** – description shows no relation to ML/AI/LLM/agents

(We do **not** filter on growth or domain keywords — novelty may hide there.)

################ 2 · SCORES ################
## 2A Momentum (0‑30 pts)
For each repo, calculate:
```python
m_score = min(30, weekly_pct*0.2 + math.log10(weekly_diff+1)*4 + math.log10(stars+1))
m_score += min(5, commits_7d*0.05 + issues_closed_7d*0.05)  # activity bonus
```

## 2B Novelty (0‑30 pts) – **qualitative, chosen by you**
Judge how *fresh, odd, or uniquely positioned* a repo is using this rubric:
* **New tech approach** (e.g., "vector DB in WebAssembly") · 0‑10 pts
* **Underserved domain** (e.g., "AI for marine biology sensors") · 0‑10 pts
* **Bridges ecosystems** (e.g., "LLM agent on microcontrollers") · 0‑10 pts
Assign `novelty_pts` 0‑30 and set `n_score = novelty_pts`.

## 2C Market Validation (0‑30 pts) – **based on web signals**
* **HN/Reddit Discussion** – quality & sentiment of community feedback · 0‑10 pts
* **Tech Blog Coverage** – depth of technical analysis & reception · 0‑10 pts
* **Enterprise Interest** – evidence of real-world adoption/pilots · 0‑10 pts
Set `v_score` based on web signals data.

## 2D Investability bonuses / penalties (‑20 … +10)
For each repo, calculate:
```python
inv = 0
inv += 5 if sponsors > 0 else 0         # early $ signal
inv += 3 if 'cloud' in description.lower() else 0
inv -= 7 if contributors > 20 else 0     # may be too mature
inv -= 0.02 * max(((datetime.now() - created_at).days/30) - 36, 0)  # age >3 yr
# Maintainer quality from web signals
inv += 5 if len(maintainer_info) > 0 else 0
```

## 2E TOTAL SCORE
`total_score = m_score + n_score + v_score + inv`  (max 100)

################ 3 · PICK CANDIDATES ################
Select **top 5** repos by `total_score`. If fewer than 5, output what you have."""

    output_section = """
################ 4 · OUTPUT (STRICT) ################
## VC Short‑List (auto‑ranked)

|Rank|Repo|1‑wk ⭐|Growth %|Total ⭐|Age (mo)|Why It Pops|
|---|---|---|---|---|---|---|
|1|owner/name|+1 234|42 %|3 456|4|Transformer DNA compression|
|2| |
|3| |
|4| |
|5| |

### Deep Dives
<!-- Repeat the block below ONCE for each repo selected above -->
#### {{rank}}. {{repo_name}} ({{weekly_pct:.2f}} %, +{{weekly_diff:,}} ⭐)
- **What**: one‑sentence plain English description
- **Why Interesting**: your novelty rationale (≤ 75 chars)
- **Momentum**: stars/commits/issues this wk
- **Market Validation**: 
  - Community: HN/Reddit sentiment
  - Coverage: notable blog posts/articles
  - Adoption: enterprise usage signals
- **Founder**: maintainer background & achievements
- **VC Verdict**: call / track / pass — ≤ 5 words
- **Risks**: license, tech, competition, etc.
"""

    rules_section = """
################ 5 · STRICT RULES ################
* Output **only** the fenced block.  
* Fill the table and deep‑dives with real data.  
* Replace placeholders `{{…}}`.  
* Bullet labels & order unchanged; bullets ≤ 75 chars.  
* Leave empty table rows if fewer than 5 repos.
* Use web signals data to inform market validation section.

Begin."""

    # Combine all sections
    prompt = "\n".join([header, data_section, scoring_section, output_section, rules_section])
    
    logging.info(f"Prompt to GPT-4.1 for weekly analysis:\n{prompt}")
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating weekly analysis: {e}")
        return "Error generating weekly analysis."

def generate_weekly_report(df, analysis_text=""):
    """
    Build a Markdown report focusing on top weekly growth.
    """
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')

    timestamp = datetime.now().strftime('%Y-%m-%d')
    top_10_weekly = df.nlargest(10, 'weekly_pct')

    report = f"""# Weekly AI Repos Report
Generated on {timestamp}

{analysis_text}

## Top 10 Weekly Growth
"""

    for _, repo in top_10_weekly.iterrows():
        repo_created = (repo['created_at'].strftime('%Y-%m-%d') 
                        if pd.notnull(repo['created_at']) else "Unknown")
        report += f"""### {repo['repo_name']}
- ⭐ Stars: {repo['stars']:,} 
- 📈 1-Week Growth: {repo['weekly_diff']:,} stars ({repo['weekly_pct']:.2f}%)
- 🎂 Created: {repo_created}
- 🔍 Description: {repo['description']}
- 🔗 [Repo Link](https://github.com/{repo['repo_name']})

"""

    return report

def run():
    try:
        # 1) Update DB / get current snapshot
        df = run_repo_tracking()
        if df.empty:
            logging.error("No data collected, exiting.")
            exit(1)

        # 2) Weekly analysis
        analysis = generate_weekly_analysis(df.nlargest(5, 'weekly_pct'))

        # 3) Build the weekly Markdown report
        weekly_md = generate_weekly_report(df, analysis_text=analysis)
        
        # 4) Create a folder in logs/weekly/<timestamp>
        timestamp_full = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = os.path.join("logs", "weekly", timestamp_full)
        os.makedirs(folder_name, exist_ok=True)
        
        # 5) Save the .md file
        md_path = os.path.join(folder_name, f"weekly_report_{timestamp_full}.md")
        with open(md_path, "w") as f:
            f.write(weekly_md)
        
        # 6) (Optional) also store a CSV
        csv_path = os.path.join(folder_name, f"weekly_repos_{timestamp_full}.csv")
        df.to_csv(csv_path, index=False)

        logging.info(f"Weekly report created: {md_path}")

        # 7) Post to Basecamp
        post_to_basecamp(md_path, subject="Weekly OS Report")
        logging.info(f"Weekly report posted to Basecamp")

    except Exception as e:
        logging.error(f"Error in weekly script: {e}")

if __name__ == "__main__":
    run()