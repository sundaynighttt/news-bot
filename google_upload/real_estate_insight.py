name: Daily Real Estate Investment Insight

on:
  schedule:
    - cron: '15 22 * * *'  # 매일 07:15 KST
  workflow_dispatch:

permissions:
  contents: write

jobs:
  generate_insight:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run real estate investment insight script
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python google_upload/real_estate_insight.py

      - name: Commit results
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add .
          git commit -m "Daily real estate insight added" || echo "Nothing to commit"
          git push
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
