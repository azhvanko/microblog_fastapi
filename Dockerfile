FROM python:3.9-slim AS builder

# Install pipenv and compilation dependencies
RUN pip install -U pip pipenv &&\
    apt-get update &&\
    apt-get install -y --no-install-recommends gcc python3-dev musl-dev libpq-dev

# Install python dependencies in /.venv
COPY Pipfile* ./
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy


FROM python:3.9-slim as runtime

# Setup env
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy virtual env from python-deps stage
COPY --from=builder /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Install dependencies and create a new user
RUN apt-get update &&\
    apt-get install -y netcat &&\
    rm -rf /var/lib/apt/lists/* &&\
    groupadd --gid 2000 app &&\
    useradd --uid 2000 --gid app --no-create-home app

WORKDIR usr/src/app

# Install application into container
COPY --chown=app . .

USER app

ENTRYPOINT ["./wait-for-postgres.sh"]
