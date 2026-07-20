# Deploying Anime Taste Profiler

This app can run locally or be deployed as a persistent web app.

## Option 1: Streamlit Community Cloud

Best if you want a simple public URL.

1. Create a GitHub repository.
2. Upload the contents of this `anime-taste-profiler` folder to that repository.
3. In Streamlit Community Cloud, create a new app from the repository.
4. Set the main file path to:

```text
app.py
```

5. Deploy. No secrets or login tokens are required.

The included files that matter for Streamlit Cloud are:

- `app.py`
- `requirements.txt`
- `runtime.txt`
- `.streamlit/config.toml`

## Option 2: Render

Best if you prefer a general web hosting service.

This project includes:

- `render.yaml`
- `Procfile`

Render can use the start command:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## Option 3: Run Locally Later

If you do not want to deploy online, double-click:

```text
start_app.bat
```

That will install dependencies if needed and start the app locally.

Local mode still uses a `127.0.0.1` address, so it only works while the Streamlit window/process is running.
