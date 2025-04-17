# daily_osmonitor.py

import os
from datetime import datetime
import pandas as pd
import logging

from core_monitor import (
    run_repo_tracking,
    anthropic_client,
    get_last_db_update_time,
    get_db_row_count,
    SEARCH_QUERY,
    sync_df_to_airtable,
    post_to_basecamp
)

import logging

BIG_COMPANIES = {
    "microsoft",
    "huggingface",
    "google",
    "facebook",
    "n8n-io",
    "modelcontextprotocol",
    "ollama",
    "meta",
    "amazon",
    "aws",
    "openai",
    "apple",
    "ibm",
    "nvidia",
    "intel",
    "salesforce",
    "databricks",
    "anthropic",
    "stability-ai",
    "qwen",
    "qwenlm",
    "vercel",
    "deepmind",
    "deepseek-ai",
    "deepseek",
    "xai",
    "pytorch",
    "tensorflow",
    "baidu",
    "bytedance",
    "alibaba",
    "deeplearning4j"
}

def generate_daily_analysis(df):
    """
    Analyze the top 50 AI repos by daily % star growth and report on the most interesting 5 in well-structured Markdown.
    """
    prompt = (
        "You are a helpful assistant for a highly technical VC fund with a rich history of investing in very early and scrappy open-source projects when they were small, often earlier than 1000 stars but not always.\n"
        "Please read the following DataFrame (which lists open-source AI repositories by daily star growth),\n"
        "then produce a concise summary of the **top 5** most interesting in well-structured Markdown.\n\n"
        f"Data:\n{df.to_string()}\n\n"
        "Instructions:\n"
        "1. Only summarize the top 5 repositories based on which you evaluate as most interesting to a potential investor. Often, these are not those with the most stars, but rather discrete repos with commercialization potential.\n"
        "2. Output exactly in Markdown with headings, numbered lists, and bullet points.\n"
        "3. Use this format (but fill in the real data):\n"
        "# Daily AI Repo Growth Analysis\n\n"
        "Here are the top 5 AI repositories assessed to be the most interesting of the top 50 fastest growing today:\n\n"
        "1. [Repository Name] ([XX%] daily growth)\n"
        "   - Added [X,XXX] stars\n"
        "   - [Short one-line description]\n\n"
        "   - [Summary of why it stood out as interesting]\n\n"
        "2. ...\n"
        "3. ...\n"
        "4. ...\n"
        "5. ...\n\n"
        "4. Do NOT include extra commentary—just the summary.\n"
        "Focus on daily changes only, and ensure the final output is valid Markdown."
    )

    logging.info(f"Prompt to Claude for daily analysis:\n{prompt}")

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        # Depending on the Anthropic client, you might need:
        #  - response["completion"]
        #  - response.content[0].text
        # Adjust the line below for your particular client usage:
        return response.content[0].text.strip()

    except Exception as e:
        logging.error(f"Error generating daily analysis: {e}")
        return "Error generating daily analysis."

def generate_daily_report(
    df,
    analysis_text="",
    prev_db_update_time=None,
    new_db_update_time=None,
    search_terms="",
):
    """
    Build a Markdown report focusing on top daily growth
    + some extra context at the top.
    """

    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')

    timestamp = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now() # current date and time

    year = now.strftime("%Y")
    print("year:", year)

    month = now.strftime("%m")
    print("month:", month)

    day = now.strftime("%d")
    print("day:", day)

    time = now.strftime("%H:%M:%S")
    print("time:", time)

    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    # Extract the GitHub owner (organization/user) from repo_name
    df["repo_owner"] = df["repo_name"].apply(lambda x: x.split("/")[0].lower() if "/" in x else "")

    # Filter out big company repos
    filtered_df = df[~df["repo_owner"].isin(BIG_COMPANIES)]

    # Select the top 10 after filtering
    top_10_daily = filtered_df.nlargest(10, 'daily_pct')

    # If fewer than 10 remain, fallback to unfiltered list
    if len(top_10_daily) < 10:
        remaining_needed = 10 - len(top_10_daily)
        additional_repos = df[~df["repo_name"].isin(top_10_daily["repo_name"])].nlargest(remaining_needed, 'daily_pct')
        top_10_daily = pd.concat([top_10_daily, additional_repos])

    # Calculate total repos for this run
    total_repos_this_run = len(df)

    # YOUR Airtable link:
    airtable_link = "https://airtable.com/appy9c2z3VHJ7dS7A/tbldkSJej1q9SfZXx/viwRSUoa1Gpucn6O7?blocks=hide"

    # Build the summary details:
    # (You can rename these headings or style them differently)
    report = f"""# Daily AI Repos Report

[**Airtable Link to Full OS Database**]({airtable_link})

Last update: {date_time}\

*This report summarizes today's fastest-growing open-source LLM repos on Github by star count.
This covers devtools, OS video/text/audio models, infrastructure, agents and more
and is intended to keep us apprised of the latest and greatest in OS AI projects broadly across categories.
We exclude [big companies](https://github.com/rshanreddy/os_repo_monitor/blob/main/bigcompanies.txt) from the list.*

## 📝 Database Overview
- **Total repos processed this run**: {total_repos_this_run}
- **Previous DB update**: {prev_db_update_time if prev_db_update_time else "N/A"}
- **New DB update**: {new_db_update_time if new_db_update_time else "N/A"}
- **Search terms**: {search_terms}

## Daily Analysis
{analysis_text}

## Top 10 Daily Growth
"""

    for _, repo in top_10_daily.iterrows():
        repo_created = (repo['created_at'].strftime('%Y-%m-%d')
                        if pd.notnull(repo['created_at']) else "Unknown")
        report += f"""### {repo['repo_name']}
- ⭐ Stars: {repo['stars']:,}
- 📈 1-Day Growth: {repo['daily_diff']:,} stars ({repo['daily_pct']:.2f}%)
- 🎂 Created: {repo_created}
- 🔍 Description: {repo['description']}
- 🔗 [Repo Link](https://github.com/{repo['repo_name']})

"""

    return report

def run():
    try:
        # 1) Check when DB was last updated *before* this run
        prev_db_update_time = get_last_db_update_time()

        # 2) Run the tracking (which inserts new rows)
        df = run_repo_tracking()
        if df.empty:
            logging.error("No data collected, exiting.")
            exit(1)

        # 3) Check the new DB update time (should reflect this run)
        new_db_update_time = get_last_db_update_time()

        # 4) Remove rows with missing or empty repo_name
        df = df.dropna(subset=["repo_name"])  # drop rows where repo_name is NaN
        df = df[df["repo_name"].str.strip() != ""]  # drop rows where repo_name is empty string

        # 5) Possibly do an AI analysis focusing on daily growth
        analysis = generate_daily_analysis(df.nlargest(50, 'daily_pct'))

        # 6) Build the daily Markdown report, passing our summary context
        daily_md = generate_daily_report(
            df,
            #analysis_text=analysis,
            prev_db_update_time=prev_db_update_time,
            new_db_update_time=new_db_update_time,
            search_terms=SEARCH_QUERY
        )

        print("Original top 10 daily repos:")
        print(df.nlargest(10, 'daily_pct')[["repo_name", "repo_owner", "daily_pct"]])

        filtered_df = df[~df["repo_owner"].isin(BIG_COMPANIES)]
        print("\nFiltered top 10 daily repos:")
        print(filtered_df.nlargest(10, 'daily_pct')[["repo_name", "repo_owner", "daily_pct"]])

        # 7) Create a folder in logs/daily/<timestamp>
        timestamp_full = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = os.path.join("logs", "daily", timestamp_full)
        os.makedirs(folder_name, exist_ok=True)

        # 8) Save the .md file
        md_path = os.path.join(folder_name, f"daily_report_{timestamp_full}.md")
        with open(md_path, "w") as f:
            f.write(daily_md)

        # 9) (Optional) also store a CSV of the entire snapshot
        csv_path = os.path.join(folder_name, f"daily_repos_{timestamp_full}.csv")
        df.to_csv(csv_path, index=False)

        logging.info(f"Daily report created: {md_path}")

        # 9) Sync to Airtable
        date_str = datetime.now().strftime('%m-%d-%Y')
        sync_df_to_airtable(df)
        logging.info("Finished pushing data to Airtable.")

        # 10) Post to Basecamp
        subject_line = f"Daily OS Report: {date_str}"
        post_to_basecamp(md_path, subject=subject_line)
        logging.info(f"Daily report created: {md_path}")

    except Exception as e:
        logging.error(f"Error in daily script: {e}")


if __name__ == "__main__":
   run()