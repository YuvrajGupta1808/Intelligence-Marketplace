# Production API image for Deep Finance Research pipeline
FROM python:3.11-slim

WORKDIR /app

# Copy project (needed for pip install .)
COPY pyproject.toml .
COPY deep_research/ deep_research/
COPY api.py agent.py ./
COPY skills/ skills/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8000

# Do not bake secrets; pass FIREWORKS_API_KEY, UNBROWSE_URL, etc. at runtime
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
