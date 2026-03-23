ARG PYTHON_VERSION=3.10

FROM python:$PYTHON_VERSION

ARG DJANGO_VERSION=5.2

WORKDIR /app

# Copy entire project
COPY . /app/

# Upgrade pip and install specific Django version first
RUN pip install --upgrade pip && pip install "Django~=$DJANGO_VERSION.0"

# Install the package in editable mode with optional valkey support
# Valkey requires Python 3.10+, so we only install it if available
RUN if python -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then \
  pip install -e .[dev,valkey]; \
  else \
  pip install -e .[dev]; \
  fi
