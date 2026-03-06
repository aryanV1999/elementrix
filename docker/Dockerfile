###############################################
# Frontend Build
###############################################
FROM node:24-alpine@sha256:1de022d8459f896fff2e7b865823699dc7a8d5567507e8b87b14a7442e07f206 \
    AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/yarn.lock ./

# Configure yarn for SSL issues and install dependencies
RUN yarn config set strict-ssl false && \
    yarn config set registry https://registry.npmjs.org/ && \
    yarn install \
    --prefer-offline \
    --frozen-lockfile \
    --non-interactive \
    --production=false \
    --network-timeout 1000000

COPY frontend . 

RUN yarn generate

###############################################
# Base Image - Python
###############################################
FROM python:3.12-slim@sha256:2267adc248a477c1f1a852a07a5a224d42abe54c28aafa572efa157dfb001bba \
    AS python-base

ENV MEALIE_HOME="/app"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    VENV_PATH="/opt/mealie"

# prepend venv to path
ENV PATH="$VENV_PATH/bin:$PATH"

# create user account
RUN useradd -u 911 -U -d $MEALIE_HOME -s /bin/bash abc \
    && usermod -G users abc \
    && mkdir $MEALIE_HOME

###############################################
# Backend Package Build
###############################################
FROM python-base AS backend-builder

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install build tools with trusted hosts for SSL issues
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org build

WORKDIR /mealie

# Copy dependency files first for better caching
COPY pyproject.toml ./
COPY mealie ./mealie

# Copy frontend to package it into the wheel
COPY --from=frontend-builder /frontend/dist ./mealie/frontend

# Build the wheel using pip without isolation to respect --trusted-host
# Install exact versions needed for build
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org \
    setuptools==80.10.2 wheel && \
    python -m build --wheel --outdir dist --no-isolation

# Create the requirements file
RUN MEALIE_VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])") && \
    echo "# Generated requirements for Mealie ${MEALIE_VERSION}" > dist/requirements.txt && \
    echo "mealie[pgsql]==${MEALIE_VERSION}" >> dist/requirements.txt

###############################################
# Package Container
# Only role is to hold the packages, or be overriden by a --build-context flag.
###############################################
FROM scratch AS packages
COPY --from=backend-builder /mealie/dist /

###############################################
# Python Virtual Environment Build
###############################################
FROM python-base AS venv-builder-base

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    libwebp-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv --upgrade-deps $VENV_PATH

FROM venv-builder-base AS venv-builder

COPY --from=packages * /dist/

# Install the wheel and dependencies into the venv with trusted hosts
RUN . $VENV_PATH/bin/activate && \
    pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r /dist/requirements.txt --find-links /dist

###############################################
# Production Image
###############################################
FROM python-base AS production

ENV PRODUCTION=true \
    TESTING=false \
    NLTK_DATA="/nltk_data/" \
    APP_PORT=9000 \
    HOST=0.0.0.0

ARG COMMIT
ENV GIT_COMMIT_HASH=$COMMIT

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    gosu \
    iproute2 \
    libldap-common \
    libldap2 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/secrets $NLTK_DATA

# Copy venv into image
COPY --from=venv-builder $VENV_PATH $VENV_PATH

# Install nltk data with SSL verification disabled (non-interactive)
RUN python -m nltk.downloader -d $NLTK_DATA averaged_perceptron_tagger_eng || true

VOLUME ["$MEALIE_HOME/data/"]

EXPOSE ${APP_PORT}

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD python -m mealie.scripts.healthcheck || exit 1

COPY ./docker/entry.sh $MEALIE_HOME/run.sh
RUN chmod +x $MEALIE_HOME/run.sh

ENTRYPOINT ["/app/run.sh"]
