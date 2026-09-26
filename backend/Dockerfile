FROM python:3.11-slim

# System deps: poppler for pdf2image, libusb for ESC/POS (disabled in cloud but avoids import errors)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install uv --quiet

# Copy dependency manifest first for layer caching
COPY backend/pyproject.toml .

# Install production deps only
RUN uv pip install --system --no-cache ".[prod]"

COPY backend/ .

# /data is mounted as Fly.io persistent volume — SQLite lives here
RUN mkdir -p /data /app/chits

ENV DATABASE_URL=sqlite:////data/restaurant.db
ENV PORT=8000

# Stamped last so it never busts the dependency layers. Deploy with:
#   flyctl deploy -a lily-cafe-pos --build-arg GIT_SHA=$(git rev-parse HEAD)
ARG GIT_SHA=unknown
ENV GIT_SHA=$GIT_SHA

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
