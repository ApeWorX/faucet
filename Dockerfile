FROM python:3.10
#-alpine3.16

ARG FAUCET_RPC_ADDRESS="http://localhost:8545" \
  FAUCET_TRANSFER_LIMIT=1000000000000000000

ENV FAUCET_RPC_ADDRESS=${FAUCET_RPC_ADDRESS} \
  FAUCET_TRANSFER_LIMIT=${FAUCET_TRANSFER_LIMIT} \
  ACCOUNT_JSON=${ACCOUNT_JSON} \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.4.2

# System deps:
RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY poetry.lock pyproject.toml /app/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --only main

# Creating folders, and files for a project:
COPY ./faucet /app

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
