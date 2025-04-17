# OS AI Repository Monitor

An automated system that tracks and analyzes open-source AI repositories on GitHub. It generates daily reports on the fastest-growing repositories, excluding major tech companies, and provides insights through Airtable and Basecamp.

## Features

- Daily monitoring of AI/ML-related GitHub repositories
- Tracks repository growth (daily and weekly)
- Filters out major tech company repositories
- Generates detailed Markdown reports
- Syncs data to Airtable
- Posts reports to Basecamp
- Uses Claude/Anthropic API for repository analysis

## Requirements

- Python 3.10+
- GitHub App credentials
- Airtable account and API key
- Basecamp account and access token
- Anthropic API key
- OpenAI API key (optional)

## Setup

1. Create a GitHub repository and clone it
2. Add the following secrets in your GitHub repository settings:
   - `AIRTABLE_API_KEY`
   - `AIRTABLE_BASE_ID`
   - `BASECAMP_ACCESS_TOKEN`
   - `BASECAMP_ACCOUNT_ID`
   - `BASECAMP_PROJECT_ID`
   - `BASECAMP_MESSAGE_BOARD_ID`
   - `APP_ID` (GitHub App)
   - `INSTALLATION_ID` (GitHub App)
   - `GITHUB_APP_PRIVATE_KEY`
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`

3. The GitHub Action is scheduled to run daily at 3:00 AM PST (10:00 UTC)

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env.prod` file with your credentials (see `.env.example`)

5. Run manually:
   ```bash
   python daily_osmonitor.py
   ```

## Project Structure

```
.
├── .github/workflows/    # GitHub Actions workflow
├── logs/                 # Generated reports and logs
│   ├── daily/           # Daily reports
│   └── weekly/          # Weekly reports
├── core_monitor.py      # Core monitoring functionality
├── daily_osmonitor.py   # Daily monitoring script
├── weekly_osmonitor.py  # Weekly monitoring script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Data Storage

- SQLite database (`repos.db`) for historical data
- CSV exports of daily snapshots
- Markdown reports in `logs/daily/` and `logs/weekly/`
- Data synced to Airtable for easy viewing/filtering
- Reports posted to Basecamp for team visibility

## Monitoring

The system includes several monitoring features:
- GitHub Actions status checks
- Failure notifications via Basecamp
- Log retention for 7 days
- Artifact storage for reports and data files

## License

MIT License