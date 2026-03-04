FROM python:3.12.10-slim AS base

RUN apt update && apt install --no-install-recommends -y git curl && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
ADD pyproject.toml .
ADD requirements.txt .
ADD uv.lock .
RUN uv sync --frozen && rm pyproject.toml requirements.txt uv.lock
ENV PYTHONPATH=/app

FROM base AS github_app
ADD pr_insight pr_insight
CMD ["python", "-m", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "pr_insight/servers/gunicorn_config.py", "--forwarded-allow-ips", "*", "pr_insight.servers.github_app:app"]

FROM base AS bitbucket_app
ADD pr_insight pr_insight
CMD ["python", "pr_insight/servers/bitbucket_app.py"]

FROM base AS bitbucket_server_webhook
ADD pr_insight pr_insight
CMD ["python", "pr_insight/servers/bitbucket_server_webhook.py"]

FROM base AS github_polling
ADD pr_insight pr_insight
CMD ["python", "pr_insight/servers/github_polling.py"]

FROM base AS gitlab_webhook
ADD pr_insight pr_insight
CMD ["python", "pr_insight/servers/gitlab_webhook.py"]

FROM base AS azure_devops_webhook
ADD pr_insight pr_insight
CMD ["python", "pr_insight/servers/azuredevops_server_webhook.py"]

FROM base AS gitea_app
ADD pr_insight pr_insight
CMD ["python", "-m", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "pr_insight/servers/gunicorn_config.py","pr_insight.servers.gitea_app:app"]


FROM base AS test
ADD requirements-dev.txt .
RUN uv pip install -r requirements-dev.txt --frozen && rm requirements-dev.txt
ADD pr_insight pr_insight
ADD tests tests

FROM base AS cli
ADD pr_insight pr_insight
ENTRYPOINT ["python", "pr_insight/cli.py"]
