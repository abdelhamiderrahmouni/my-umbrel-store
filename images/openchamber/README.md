# OpenChamber image

This image redistributes OpenChamber **v2.5.1**, commit `3e9ef4db17bd184f1f2713eb6356261304d6aee7`, using its upstream Dockerfile. The wrapper explicitly replaces upstream's OpenCode **2.1.3** with **2.1.4** and adds the MIT notice and image metadata. OpenChamber's compatibility check accepts OpenCode 2.x >=2.1.0; runtime tests must still pass before release. The image targets **linux/amd64 only**. ARM64 has not been built or tested.

## Rebuild

In a separate checkout (not a directory containing private settings or project data):

```sh
git clone https://github.com/openchamber/openchamber.git openchamber-upstream
git -C openchamber-upstream checkout --detach 3e9ef4db17bd184f1f2713eb6356261304d6aee7
docker build --platform linux/amd64 -t errahmounispace/openchamber:2.5.1-local openchamber-upstream
docker build --platform linux/amd64 -t ghcr.io/abdelhamiderrahmouni/openchamber:2.5.1-umbrel.1 images/openchamber
```

The last command runs from this store's repository root. Upstream pins its application source, OpenCode version, Bun version, and cloudflared digest, but distro/npm dependencies can still change between builds. **A rebuild can produce a different digest**: inspect it, test it, and update the package's digest deliberately. Never assume a new build matches the initial local digest.

The manual [GitHub Actions workflow](../../.github/workflows/build-openchamber.yml) performs the two builds with `packages: write` and publishes a uniquely tagged image. It does not run automatically on pushes and does not rewrite the app package. After running it, verify public pullability and replace the package image tag and digest together.

## Publish the locally built image

Only the image layers are published. Never use `docker commit` on a working container: that could include code, sessions, or credentials.

The GHCR repository is public. **2.5.1-umbrel.1** is published and passed anonymous pull verification with an empty Docker credentials directory. Exact runtime version assertions and isolated container tests passed before publication. For future publishing with GitHub CLI's OAuth login, authorize package access interactively if needed:

```sh
gh auth refresh --hostname github.com --scopes write:packages,read:packages
```

For other token types, provision an appropriate registry credential through your normal secure login flow; do not paste tokens into this repo or chat. Then publish the already built licensed image:

```sh
gh auth token | docker login ghcr.io --username abdelhamiderrahmouni --password-stdin
docker push ghcr.io/abdelhamiderrahmouni/openchamber:2.5.1-umbrel.1
```

New GHCR packages may default to private. Change **openchamber → Package settings → Change visibility → Public** on your GitHub profile's Packages page. This is required for Umbrel installations without registry credentials.

Use an empty Docker config directory to verify anonymous access, then check the reported platform/digest:

```sh
mkdir -p /tmp/opencode/ghcr-anonymous
DOCKER_CONFIG=/tmp/opencode/ghcr-anonymous docker manifest inspect ghcr.io/abdelhamiderrahmouni/openchamber:2.5.1-umbrel.1
DOCKER_CONFIG=/tmp/opencode/ghcr-anonymous docker pull ghcr.io/abdelhamiderrahmouni/openchamber:2.5.1-umbrel.1@sha256:49166477b91d4050fe73f04caec59717e3153dc544065eb13a424d5658b2ce40
```

The published and anonymously verified index digest is `sha256:49166477b91d4050fe73f04caec59717e3153dc544065eb13a424d5658b2ce40`. Replace the tag and digest together when verifying another build. An OCI index with a provenance attestation does not prove multiple runnable architectures: this package is **amd64**, not ARM64. A public pull of each new pinned digest remains a release gate.
