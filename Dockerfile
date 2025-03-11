FROM python:3.13-slim-bookworm

WORKDIR /arrchive
COPY . .

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN uv sync --frozen --no-dev

CMD [ "uv", "run", "arrchive.py" ]
