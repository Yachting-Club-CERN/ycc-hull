ARG PYTHON_VERSION="312"

# Use Poetry to generate requirements.txt as in the past there were various problems with micropipenv handling Poetry lock files with dependency groups
FROM registry.access.redhat.com/ubi9/python-$PYTHON_VERSION AS builder

WORKDIR /opt/app-root/src

RUN pip install --no-cache-dir -U pip setuptools poetry && \
    poetry self add poetry-plugin-export

COPY --chown=1001:0 "pyproject.toml" "poetry.lock" "./"
RUN poetry export --only main --format requirements.txt --output requirements.txt

# Main image
FROM registry.access.redhat.com/ubi9/python-$PYTHON_VERSION

WORKDIR /opt/app-root/src

RUN pip install --no-cache-dir -U pip setuptools micropipenv

COPY --chown=1001:0 --from=builder /opt/app-root/src/requirements.txt /opt/app-root/src/
RUN micropipenv install --method requirements

COPY --chown=1001:0 "docker-entrypoint.sh" "pyproject.toml" "src" "./"
RUN mkdir conf/ && chmod 0777 conf/ && \
    mkdir log/ && chmod 0777 log/

EXPOSE 8080
ENTRYPOINT [ "/opt/app-root/src/docker-entrypoint.sh" ]
