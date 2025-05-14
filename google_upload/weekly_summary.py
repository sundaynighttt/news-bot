name: Weekly Naver News Summary

on:
  schedule:
    - cron: '10 22 * * 5'  # 매주 토요일 07:10 KST (금요일 22:10 UTC)
  workflow_dispatch:

permissions:
  contents: write

jobs:
  weekly_summary:
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

      - name: Run weekly summary script
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python google_upload/weekly_summary.py

      - name: Commit results
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add .
          git commit -m "Weekly summary update" || echo "Nothing to commit"
          git push
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
