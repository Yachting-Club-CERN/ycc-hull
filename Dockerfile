ARG PYTHON_VERSION="311"

# Main image
FROM registry.access.redhat.com/ubi9/python-$PYTHON_VERSION

WORKDIR "/opt/app-root/src"

# Note: could not make ENABLE_MICROPIPENV work :-(
RUN pip install -U pip setuptools micropipenv[toml]
# 1001 = uid from parent container
COPY --chown=1001:0 "ycc_hull" "./ycc_hull/"
COPY --chown=1001:0 "poetry.lock" "pyproject.toml" "docker-entrypoint.sh" "./"
RUN mkdir conf/ && chmod 0777 conf/
RUN mkdir log/ && chmod 0777 log/
# --dev was added during the Pytho 3.11 upgrade (2024-01). It is ugly, but
# without it micropipenv does not install all the main transitive dependencies
# from the Poetry lock file. No idea why.
RUN micropipenv install --method poetry --dev

EXPOSE 8080
ENTRYPOINT [ "/opt/app-root/src/docker-entrypoint.sh" ]
