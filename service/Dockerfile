# -----------------------------------------------------------------------------
# InvoiceFormat API: web service image
# -----------------------------------------------------------------------------
# Official Python image (Debian 12 "bookworm", slim), pinned by digest for reproducible builds.
FROM python:3.13-slim-bookworm@sha256:281d39ff02e3b389401586134ff9e6572954687822a58055ec07a60ded4e0b7f

# System libraries for PDF drawing (Pango) and the font embedded in every invoice PDF.
# The font cache is built now (fc-cache), so nothing needs writing at runtime (read-only container).
# Packages are fetched over HTTPS. The optional "build_ca" secret is ONLY for build machines behind a
# TLS-inspecting proxy (e.g. corporate networks); it is used for this step and never stored in the image.
#   docker build --secret id=build_ca,src=/path/to/ca.crt ...
RUN --mount=type=secret,id=build_ca,required=false \
    CA=/etc/ssl/certs/ca-certificates.crt; \
    if [ -s /run/secrets/build_ca ]; then \
      cp /run/secrets/build_ca /tmp/build_ca.crt && chmod 644 /tmp/build_ca.crt && CA=/tmp/build_ca.crt; fi; \
    sed -i 's#http://deb.debian.org#https://deb.debian.org#g' /etc/apt/sources.list.d/debian.sources \
 && apt-get -o Acquire::https::CaInfo="$CA" update \
 && apt-get -o Acquire::https::CaInfo="$CA" install -y --no-install-recommends \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core fontconfig \
 && fc-cache -f \
 && rm -rf /var/lib/apt/lists/* /tmp/build_ca.crt

# The app never runs as root.
RUN groupadd --system app && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /srv
COPY requirements.txt .
RUN --mount=type=secret,id=build_ca,required=false \
    if [ -s /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca; fi; \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests
COPY samples ./samples

USER app
# Caches (fonts) go to /tmp, the only writable place in the read-only container.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 XDG_CACHE_HOME=/tmp/.cache
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/v1/health', timeout=4).status == 200 else 1)"

# 2 worker processes; PDF drawing is CPU-heavy, so roughly one worker per CPU core.
# --proxy-headers: trust X-Forwarded-For from the reverse proxy (Caddy) for client IPs.
# The font cache folder is created first, so the two workers don't race to create it.
CMD ["sh", "-c", "mkdir -p /tmp/.cache/fontconfig && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips '*' --no-server-header"]
