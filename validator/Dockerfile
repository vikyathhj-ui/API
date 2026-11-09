# -----------------------------------------------------------------------------
# Docker image: KoSIT e-invoice validator (EN 16931 core rules), HTTP mode.
#
# Before building, run:  bash scripts/fetch-dependencies.sh
# (it downloads the validator + rules into ./vendor and verifies checksums;
#  the build itself then needs no internet except pulling the base image)
# -----------------------------------------------------------------------------

# Base image: Eclipse Temurin Java 21 runtime on Ubuntu 22.04.
# Pinned by digest so every build uses exactly the same bytes (reproducible).
# The digest is a multi-platform index: works on Intel/AMD and Apple Silicon.
FROM eclipse-temurin:21-jre-jammy@sha256:1eac8b8fee11ca7d6725a48bc5d41992ed1561504ebae25490d2d062847e8269

# Create an unprivileged user. The app should never run as root.
RUN groupadd --system app && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Copy only what is needed (see .dockerignore). Files are owned by root and
# read-only for the app user, so a compromised process cannot change rules.
COPY vendor/validator.jar /app/validator.jar
COPY vendor/repository /app/repository
COPY vendor/LICENSE-* /app/licenses/

USER app

EXPOSE 8080

# Docker asks this every 30 s: "are you healthy?". /server/health is built into the validator.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8080/server/health > /dev/null || exit 1

# -D  = daemon (HTTP server) mode
# -H  = listen on all interfaces *inside* the container (compose limits who can reach it)
# MaxRAMPercentage lets Java size its memory to the container's memory limit.
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app/validator.jar", \
            "-s", "/app/repository/scenarios.xml", "-r", "/app/repository", \
            "-D", "-H", "0.0.0.0", "-P", "8080"]
