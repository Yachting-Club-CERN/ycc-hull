ARG PYTHON_VERSION="312"
ARG UV_VERSION="0.10.10"

# Use uv to generate requirements.txt
FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv

FROM registry.access.redhat.com/ubi9/python-$PYTHON_VERSION AS builder

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /opt/app-root/src

COPY --chown=1001:0 pyproject.toml uv.lock ./
RUN uv export --no-dev --no-emit-project --format requirements-txt > requirements.txt

# Main image
FROM registry.access.redhat.com/ubi9/python-$PYTHON_VERSION

WORKDIR /opt/app-root/src

COPY --from=uv /uv /usr/local/bin/uv

USER root
RUN dnf install -y https://download.oracle.com/otn_software/linux/instantclient/2370000/oracle-instantclient-basic-23.7.0.25.01-1.el9.x86_64.rpm && \
    dnf clean all

USER 1001

COPY --chown=1001:0 --from=builder /opt/app-root/src/requirements.txt /opt/app-root/src/
RUN uv pip install --system --no-cache --python /opt/app-root/bin/python3 -r requirements.txt

COPY --chown=1001:0 "docker-entrypoint.sh" "pyproject.toml" "src" "./"
RUN mkdir conf/ && chmod 0777 conf/ && \
    mkdir log/ && chmod 0777 log/

EXPOSE 8080
ENTRYPOINT [ "/opt/app-root/src/docker-entrypoint.sh" ]
