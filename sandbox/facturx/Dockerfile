# -----------------------------------------------------------------------------
# Docker image: Factur-X / ZUGFeRD generator (sandbox spike)
#   JSON invoice -> CII XML -> PDF/A-3b -> Factur-X PDF
# -----------------------------------------------------------------------------
# Official Python image, Debian 12 "bookworm", slim variant (small, no compilers).
FROM python:3.13-slim-bookworm@sha256:281d39ff02e3b389401586134ff9e6572954687822a58055ec07a60ded4e0b7f

# WeasyPrint needs the Pango text-layout library; DejaVu is the font we embed
# into the PDF (PDF/A requires all fonts to be embedded).
# --no-install-recommends keeps the image small; the apt cache is deleted after.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

# Unprivileged user: the app never runs as root.
RUN groupadd --system app && useradd --system --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /work
# Install Python dependencies first (separate layer, so code changes rebuild fast).
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY app /work/app
COPY tests /work/tests
COPY samples /work/samples

USER app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Default: generate PDFs for every JSON in /work/samples into /work/out
ENTRYPOINT ["python", "-m", "app.cli"]
CMD ["--help"]
