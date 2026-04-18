FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY src/ src/

RUN uv pip install --system -e .

ENV IMMICH_BASE_URL=""
ENV IMMICH_API_KEY=""

EXPOSE 8000

ENTRYPOINT ["immich-mcp"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
