# Build upstream v2.5.1 first; see README.md for the pinned source commit.
ARG UPSTREAM_IMAGE=errahmounispace/openchamber:2.5.1-local
FROM ${UPSTREAM_IMAGE}

# Upstream bundles 2.1.3. Pin the requested compatible patch explicitly.
RUN npm install -g @opencode/cli@2.1.4

# Preserve upstream's license when redistributing the application image.
COPY LICENSE /home/openchamber/LICENSE
LABEL org.opencontainers.image.title="OpenChamber for ErrahmouniSpace Store" \
      org.opencontainers.image.version="2.5.1-umbrel.1" \
      org.opencontainers.image.source="https://github.com/abdelhamiderrahmouni/my-umbrel-store" \
      org.opencontainers.image.revision="3e9ef4db17bd184f1f2713eb6356261304d6aee7" \
      org.opencontainers.image.licenses="MIT"
