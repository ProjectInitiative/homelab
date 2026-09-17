FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends fio util-linux ca-certificates \
 && rm -rf /var/lib/apt/lists/*
COPY controller.py /opt/juicefs-bench/controller.py
ENTRYPOINT ["python3", "/opt/juicefs-bench/controller.py"]
