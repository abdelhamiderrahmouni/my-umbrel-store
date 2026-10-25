# Build upstream v2.3.3 first; see README.md for the pinned source commit.
ARG UPSTREAM_IMAGE=errahmounispace/openchamber:2.3.3-local
FROM ${UPSTREAM_IMAGE}

# Preserve upstream's license when redistributing the application image.
COPY LICENSE /home/openchamber/LICENSE
LABEL org.opencontainers.image.title="OpenChamber for ErrahmouniSpace Store" \
      org.opencontainers.image.version="2.3.3-umbrel.1" \
      org.opencontainers.image.source="https://github.com/abdelhamiderrahmouni/my-umbrel-store" \
      org.opencontainers.image.revision="7521e712e9dbe12cce3c05debaa6d356fedea19b" \
      org.opencontainers.image.licenses="MIT"
