# OpenChamber image

This image redistributes OpenChamber **v2.3.3**, commit `7521e712e9dbe12cce3c05debaa6d356fedea19b`, using its upstream Dockerfile and bundled OpenCode **2.0.29**. A minimal wrapper adds the MIT notice and image metadata; it does not change the runtime. The first release targets **linux/amd64 only**. ARM64 has not been built or tested.

## Rebuild

In a separate checkout (not a directory containing private settings or project data):

```sh
git clone https://github.com/openchamber/openchamber.git openchamber-upstream
git -C openchamber-upstream checkout --detach 7521e712e9dbe12cce3c05debaa6d356fedea19b
docker build --platform linux/amd64 -t errahmounispace/openchamber:2.3.3-local openchamber-upstream
docker build --platform linux/amd64 -t ghcr.io/abdelhamiderrahmouni/openchamber:2.3.3-umbrel.1 images/openchamber
```

The last command runs from this store's repository root. Upstream pins its application source, OpenCode version, Bun version, and cloudflared digest, but distro/npm dependencies can still change between builds. **A rebuild can produce a different digest**: inspect it, test it, and update the package's digest deliberately. Never assume a new build matches the initial local digest.

The manual [GitHub Actions workflow](../../.github/workflows/build-openchamber.yml) performs the two builds with `packages: write` and publishes a uniquely tagged image. It does not run automatically on pushes and does not rewrite the app package. After running it, verify public pullability and replace the package image tag and digest together.

## Publish the initial locally built image

Only the image layers are published. Never use `docker commit` on a working container: that could include code, sessions, or credentials.

The initial upload was blocked by the `gh` token's scopes, then succeeded after the owner granted package access. The image is now public, and an anonymous pull of the pinned digest passed on 2026-10-25. For future publishing with GitHub CLI's OAuth login, authorize package access interactively if needed:

```sh
gh auth refresh --hostname github.com --scopes write:packages,read:packages
```

For other token types, provision an appropriate registry credential through your normal secure login flow; do not paste tokens into this repo or chat. Then publish the already built licensed image:

```sh
gh auth token | docker login ghcr.io --username abdelhamiderrahmouni --password-stdin
docker push ghcr.io/abdelhamiderrahmouni/openchamber:2.3.3-umbrel.1
```

New GHCR packages may default to private. Change **openchamber → Package settings → Change visibility → Public** on your GitHub profile's Packages page. This is required for Umbrel installations without registry credentials.

Use an empty Docker config directory to verify anonymous access, then check the reported platform/digest:

```sh
mkdir -p /tmp/opencode/ghcr-anonymous
DOCKER_CONFIG=/tmp/opencode/ghcr-anonymous docker manifest inspect ghcr.io/abdelhamiderrahmouni/openchamber:2.3.3-umbrel.1
DOCKER_CONFIG=/tmp/opencode/ghcr-anonymous docker pull ghcr.io/abdelhamiderrahmouni/openchamber:2.3.3-umbrel.1@sha256:bd1c799a37ebdd5877318f6c4e5e603e4c9061644b0fd9b04baacb7bb6f7ae44
```

For the original local build, the index digest is `sha256:bd1c799a37ebdd5877318f6c4e5e603e4c9061644b0fd9b04baacb7bb6f7ae44`. Although it is an OCI index with a provenance attestation, its only runnable platform is **amd64**, not ARM64. A public pull is still a release gate.
