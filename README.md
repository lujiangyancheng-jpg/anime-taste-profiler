# Anime Taste Profiler

Anime Taste Profiler is a Streamlit app that analyzes public anime rating lists from AniList or Bangumi and turns them into a readable taste profile.

The app source lives in:

```text
anime-taste-profiler/
```

## Run Locally

```bash
cd anime-taste-profiler
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

For Streamlit Community Cloud, use this main file path:

```text
anime-taste-profiler/app.py
```

More deployment notes are in [`anime-taste-profiler/DEPLOYMENT.md`](anime-taste-profiler/DEPLOYMENT.md).

## Quality Checks

GitHub Actions runs a basic validation workflow on pushes and pull requests:

- install app dependencies
- compile Python files
- run unit tests from `tests/`
