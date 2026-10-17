# OpenChamber web deployment research

Researched **2026-10-16**. Primary sources only; local container smoke-test results are recorded below.

## Local amd64 smoke test

Built the unmodified v2.3.3 Dockerfile from commit `7521e712e9dbe12cce3c05debaa6d356fedea19b` with Docker Engine 29.9.0 on Linux amd64. Local image tag: `errahmounispace/openchamber:2.3.3-local`; local build index digest: `sha256:f623dfb7cbd612f5e84b545177b0b005dea74b0d1ebae9c380f8f923897457c8`. This image has not been published and is not a verified multi-architecture release.

Started container `errahmounispace-openchamber-local` with an init process, a generated UI password, six disposable persistent bind mounts, and only `127.0.0.1:3000:3000` published. No real project folders or host credentials were mounted.

Verified by HTTP requests:

- `/health` reports OpenChamber 2.3.3, managed OpenCode running and ready, and a secure backend connection.
- Unauthenticated `/auth/session` returns 401.
- Password login succeeds and the resulting cookie authenticates `/auth/session`.
- The root page serves HTML with HTTP 200.

Not yet verified: rendered browser behavior, provider onboarding, AI responses, terminal/WebSocket/SSE workflows, protected API coverage, restart/recreation persistence, ARM64, or installation through Umbrel. Build success does not resolve all runtime concerns listed below.

## Decision summary

- **Official project:** [`openchamber/openchamber`](https://github.com/openchamber/openchamber). The proposed `btriapitsyn/openchamber` URL redirects there; GitHub's [repository API](https://api.github.com/repos/btriapitsyn/openchamber) returns `full_name: openchamber/openchamber`, homepage `https://openchamber.dev/`, and MIT license metadata.
- **Current stable release:** [v2.3.3](https://github.com/openchamber/openchamber/releases/tag/v2.3.3), published 2026-10-14 23:28:53 UTC. Exact release commit: **`7521e712e9dbe12cce3c05debaa6d356fedea19b`**, verified through the [tag-ref API](https://api.github.com/repos/openchamber/openchamber/git/ref/tags/v2.3.3).
- **No verified official prebuilt container image was found.** Upstream supplies a Dockerfile and Compose file that uses `build:`, not `image:`. Do not invent `ghcr.io/btriapitsyn/openchamber:latest` or substitute a third-party image as official.
- **OpenCode V2 support is positively established for this release**, not assumed: the Dockerfile installs **`@opencode/cli@2.0.29`**, matching client/schema dependencies. Runtime accepts only major **2**, minimum **2.0.20**; 1.x and future majors are rejected. Use the paired **2.0.29**, not merely any V2 binary. [Dockerfile][dockerfile] [package manifest][web-package] [compatibility implementation][compatibility]
- **Recommended Umbrel direction:** build and publish a store-maintained image from the pinned stable upstream commit, initially test `linux/amd64` and `linux/arm64`, then use its verified immutable multi-platform digest in the app. Keep the bundled OpenCode process in the same container, expose only web port **3000** through Umbrel's proxy, retain OpenChamber's password protection, and persist the six upstream mount targets below. This is a recommendation, not an upstream-published image or a claim that the build has passed.

## 1. Source and version scope

The checked-out main snapshot was `2b94db8470ca77d946917e937e3b04d7b0b678bc`. A direct `git diff v2.3.3 HEAD` confirmed no changes in the Dockerfile, Compose file, entrypoint, web package manifest, or OpenCode compatibility implementation. Deployment citations below use the stable release commit rather than moving `main`.

The [latest-release API](https://api.github.com/repos/openchamber/openchamber/releases/latest) lists desktop/mobile artifacts, a VS Code extension, and `openchamber-web-2.3.3.tgz`. Release notes explicitly say **“Bundled OpenCode updated to 2.0.29.”** Desktop artifacts for ARM64 and x86_64 do **not** prove container architecture support.

## 2. Image, tags, digests, architectures

### Verified upstream evidence

- Upstream [`docker-compose.yml`][compose] uses a local context and `Dockerfile`; it names no registry image.
- [`Dockerfile`][dockerfile] uses `oven/bun:1.4.3` in build and runtime stages, installs `@opencode/cli@2.0.29`, and copies cloudflared from a digest-pinned image.
- The cloudflared source reference is `cloudflare/cloudflared@sha256:6d91c121b803126f7a5344005d17a9324788fc09d305b6e2560ec6040a7ae283` (comment: 2026.3.0). **That is a dependency digest, not an OpenChamber image digest.**
- Inspection of checked-in workflows found no Docker registry publishing job or `ghcr.io` reference. The [release workflow][release-workflow] publishes npm packages and app artifacts, not a documented container image.

### Anonymous registry checks on 2026-10-16

| Candidate | First-party endpoint | Result |
| --- | --- | --- |
| `ghcr.io/openchamber/openchamber` | `https://ghcr.io/token?service=ghcr.io&scope=repository:openchamber/openchamber:pull` | HTTP 403 `DENIED` |
| `ghcr.io/btriapitsyn/openchamber` | `https://ghcr.io/token?service=ghcr.io&scope=repository:btriapitsyn/openchamber:pull` | HTTP 403 `DENIED` |
| `docker.io/openchamber/openchamber` | `https://hub.docker.com/v2/repositories/openchamber/openchamber/tags?page_size=10` | HTTP 404 `object not found` |
| `docker.io/btriapitsyn/openchamber` | `https://hub.docker.com/v2/repositories/btriapitsyn/openchamber/tags?page_size=10` | HTTP 404 `object not found` |

These are observations, **not proof that no private image or differently named image exists**. No publicly pullable official application tags, application manifest digest, or platform manifest list could be verified. Consequently:

| Item | Finding |
| --- | --- |
| Official application image | Not established |
| Application container tags | Not established; `v2.3.3` is a Git release tag, not a verified image tag |
| Application image digest | Not available |
| Confirmed container architectures | None verified by pull/build/run |
| Packaging targets | Recommend `linux/amd64` and `linux/arm64`, subject to successful native builds and tests |

Avoid declaring ARMv7 support. Native dependencies include `node-pty`, `bun-pty`, and `sherpa-onnx-node`; a build's success depends on their platform assets as well as Bun, OpenCode, and cloudflared. [web package manifest][web-package]

## 3. Upstream Docker instructions and runtime

The official local-build deployment is the repository-root [Compose file][compose]. It maps host 3000 to container 3000, requires a password through Compose interpolation, adds `host.docker.internal:host-gateway`, and sets `restart: unless-stopped`. From a checkout of the pinned release, the equivalent documented startup is:

```sh
OPENCHAMBER_UI_PASSWORD="$(openssl rand -base64 24)" docker compose up -d --build
```

The upstream file's comment demonstrates the same password-generation approach with `docker compose up -d`; `--build` makes the first-party `build:` behavior explicit. This is **not** an instruction to run a published image. For ongoing deployment, provision and securely retain a generated password rather than unknowingly generating a different one on each restart.

### Process, dependencies, and ports

- Runtime working directory and home: `/home/openchamber`; non-root user/group **1000:1000**. Bind-mounted data must be writable by that identity. [Dockerfile][dockerfile]
- Container includes Bash, bzip2, CA certificates, Git, less, Node.js, npm, OpenSSH client, Python 3, Bun, OpenCode CLI, and cloudflared. No external database is declared by upstream Compose. [Dockerfile][dockerfile] [Compose][compose]
- Container entrypoint defaults **`OPENCHAMBER_HOST=0.0.0.0`**, starts `bun packages/web/bin/cli.js`, and then follows logs with `exec bun packages/web/bin/cli.js logs`. It is not simply a foreground `opencode web` process. [entrypoint][entrypoint]
- Public application port: **3000/tcp** (`EXPOSE 3000` and Compose mapping). Host port is independently selectable by the eventual Umbrel package. [Dockerfile][dockerfile] [Compose][compose]
- Managed OpenCode binds **127.0.0.1** by default. Leave it private in the same container; no separate OpenCode port publication is necessary. The lifecycle allocates a managed port rather than treating the example 4096 as a fixed public application port. [environment config][env-config] [lifecycle implementation][lifecycle]
- An external server is possible using `OPENCODE_HOST=http://hostname:4096` and `OPENCODE_SKIP_START=true`; the URL parser requires an explicit port and disallows a path, query, or fragment. External filesystem visibility and credential handling need independent validation. Prefer the bundled process for this package. [Compose][compose] [environment config][env-config]
- `OH_MY_OPENCODE=true` triggers optional runtime installation of `oh-my-opencode` without a version pin; leave it disabled for a controlled release. [entrypoint][entrypoint]
- For CLI/npm installation outside this container, the [web package manifest][web-package] requires **Node >=24.14.0**. The Dockerfile runs the app using Bun and installs distribution `nodejs`/`npm`; it does not explicitly install Node 24.14. This is a build/runtime verification item, not grounds to silently assume the image meets the npm engine requirement.

## 4. OpenCode compatibility: explicit evidence

The release's [`compatibility.js`][compatibility] defines:

```js
const MINIMUM_OPENCODE_VERSION = '2.0.20';
// isSupportedOpenCodeVersion also requires releaseParts(version)[0] === 2
```

Its comment explains that 2.0.20 added `GET /api/credential`; 2.0.15 had added session metadata patching. The [Dockerfile][dockerfile] pins `@opencode/cli@2.0.29`, and the [web manifest][web-package] pins both `@opencode/client` and `@opencode/schema` to `2.0.29`. This is stronger evidence than a generic README statement that OpenChamber uses OpenCode.

External readiness/version detection uses **`GET /api/info`**, with a legacy `/global/health` probe to identify incompatible V1 servers. A successful HTML response is not compatibility evidence. The [lifecycle documentation][lifecycle-doc] says an incompatible external server is attached as external but not ready rather than transparently replaced with a managed one.

**Deployment consequence:** do not reuse an existing Umbrel OpenCode 1.x service, old `opencode-ai` recipe, or arbitrary V2 latest tag. Use the paired 2.0.29 in this release and test `/api/opencode/compatibility` plus an actual session. Runtime allows 2.x >=2.0.20; that does not establish that all future 2.x releases are tested.

## 5. Persistence and ownership

These are the exact upstream [Compose][compose] mounts:

| Upstream host directory | Container target | Intended retained state |
| --- | --- | --- |
| `./data/openchamber` | `/home/openchamber/.config/openchamber` | OpenChamber settings, projects/chats, app auth/passkeys, integrations, other app state |
| `./data/opencode/share` | `/home/openchamber/.local/share/opencode` | OpenCode durable data |
| `./data/opencode/state` | `/home/openchamber/.local/state/opencode` | OpenCode state |
| `./data/opencode/config` | `/home/openchamber/.config/opencode` | OpenCode configuration |
| `./data/ssh` | `/home/openchamber/.ssh` | Git SSH identity and known hosts |
| `./workspaces` | `/home/openchamber/workspaces` | User repositories/files |

Use dedicated app-data host directories with **1000:1000 ownership**. Back up all six targets together; these contain sensitive keys, provider credentials, code, and conversations. The OpenChamber data root can be overridden by `OPENCHAMBER_DATA_DIR`; keeping the upstream default avoids partial path overrides. [projects storage documentation][projects-doc]

The entrypoint exports `OPENCODE_CONFIG_DIR` with default `/home/openchamber/.config/opencode`. It generates an **unencrypted Ed25519 SSH key** if the public/private pair is absent, attempts `.ssh` permissions 0700, private key 0600/public key 0644, and prints only the public key. Persist that directory rather than generating a new identity at every recreation. [entrypoint][entrypoint]

Do not mount a data volume over all of `/home/openchamber`: the Dockerfile installs application code, dependencies, and the OpenCode npm prefix there, so such a mount can hide the application. Preserve targeted subdirectories instead. [Dockerfile][dockerfile]

The npm prefix `/home/openchamber/.npm-global` is **not** a persisted upstream mount. In-app CLI upgrades or optional global package installations there can be lost when replacing the container. Treat upgrades as image rebuilds; the process should not drift away from the pinned release pairing. [Dockerfile][dockerfile] [CLI upgrade behavior][lifecycle-doc]

## 6. Authentication, network boundary, and proxy

- Set **`OPENCHAMBER_UI_PASSWORD`**. Upstream Compose fails interpolation if it is unset/empty; the entrypoint also supports legacy `UI_PASSWORD`, but the canonical variable is `OPENCHAMBER_UI_PASSWORD`. [Compose][compose] [entrypoint][entrypoint]
- Password enforcement by Compose is not identical to enforcement for someone launching the Dockerfile directly: the entrypoint conditionally supplies the password only when present. An Umbrel image wrapper must configure a password itself rather than assuming Compose interpolation runs. [entrypoint][entrypoint]
- Upstream warns that this UI gives access to the machine and its code. Treat it as an administrator-grade coding/terminal interface, not an isolated multi-user SaaS. Grant only its own workspaces and data; do not mount the host filesystem, Docker socket, or unrelated app secrets. The mounting restriction is a packaging recommendation based on that capability warning. [security guide][security]
- Password login supports passkeys, which depend on the current password and are cleared on password changes/removal. Paired devices use revocable per-device tokens; preserve app auth state. [security guide][security]
- [`ui-auth.js`][ui-auth] implements login rate limiting and session cookies; [`ui-passkeys.js`][ui-passkeys] stores `ui-passkeys.json` under the app data root. HTTPS and correct forwarded scheme remain important; do not promise that plain `http://umbrel.local` provides passkey/PWA feature parity with a secure origin.
- Prefer Umbrel's proxy/private network, with **no public direct port forwarding**, retain app-level auth, and use HTTPS for remote browser access. Umbrel's login layer is additional defense, not a substitute for configuring the app's own authentication.
- The official [reverse-proxy guide][proxy] requires WebSockets at `/api/event/ws`, `/api/global/event/ws`, `/api/terminal/ws`; unbuffered SSE at `/api/event`, `/api/global/event`, `/api/notifications/stream`, `/api/openchamber/events`; large upload allowance; long read timeouts; and forwarding `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto`. Avoid double compression. Validate those through the actual Umbrel proxy, not just a direct browser request.
- Outbound model-provider access is required for normal AI use unless using reachable local providers. Cloudflare/ngrok/relay and optional integrations add other network paths; don't enable tunnels by default in a home-server package. [security guide][security]
- Optional enterprise mode is documented via `OPENCHAMBER_ENTERPRISE_MODE=1`; a container also needs `OPENCHAMBER_ALLOW_NETWORK_ACCESS=1` in that mode to permit its network bind. This mode changes provider onboarding and external integrations, so it should not be enabled without a product decision. [security guide][security]

## 7. License and official icon assets

The project [LICENSE][license] is **MIT**, copyright **2025 Bohdan Triapitsyn**. Retain its copyright and license notice when redistributing substantial software. Repository-level MIT is evidence for code redistribution; it is not an explicit trademark endorsement or a separately documented logo usage policy.

Official assets at the stable commit:

| Asset | Use |
| --- | --- |
| [`packages/electron/resources/icons/app-icon.png`](https://raw.githubusercontent.com/openchamber/openchamber/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/electron/resources/icons/app-icon.png) | **512×512 PNG**, useful app-store icon candidate |
| [`packages/electron/resources/icons/icon.png`](https://raw.githubusercontent.com/openchamber/openchamber/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/electron/resources/icons/icon.png) | **1024×1024 PNG**, higher-resolution candidate |
| [`packages/web/public/logo-light-512x512.svg`](https://raw.githubusercontent.com/openchamber/openchamber/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/public/logo-light-512x512.svg) | Web logo, light variant |
| [`packages/web/public/logo-dark-512x512.svg`](https://raw.githubusercontent.com/openchamber/openchamber/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/public/logo-dark-512x512.svg) | Web logo, dark variant |
| [`packages/web/public/logo-light-192x192.png`](https://raw.githubusercontent.com/openchamber/openchamber/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/public/logo-light-192x192.png) | **192×192 PNG**, existing PWA asset |
| [`docs/references/badges/openchamber-logo-light.svg`](https://raw.githubusercontent.com/openchamber/openchamber/7521e712e9dbe12cce3c05debaa6d356fedea19b/docs/references/badges/openchamber-logo-light.svg) | Logo used by the official README |

PNG dimensions were inspected from checked-out files, not inferred from filenames. Prefer a pinned raw asset URL or a locally vendored copy with attribution over a mutable avatar URL.

## 8. Concrete unresolved items / release gate

1. **Image publishing ownership:** obtain confirmation of an official public image if desired, or explicitly own a store-maintained build. No usable upstream image digest has been established.
2. **Buildability:** build the pinned Dockerfile on amd64 and arm64, including frozen Bun lockfile, workspace SDK output, native terminal/voice modules, and pinned cloudflared copy. Source review is not a successful build. Record per-platform and index digests after publication.
3. **Runtime dependency mismatch:** inspect actual Node/Bun versions in the built image; test the Node >=24.14 engine requirement versus the Dockerfile's distribution `nodejs` installation.
4. **Entrypoint/liveness:** test daemon startup, failure behavior while following logs, stop/restart signal handling, and a real healthcheck. The current Dockerfile/Compose declare no healthcheck. If reliable container lifecycle requires foreground startup, evaluate that as a deliberate packaging change, not assumed upstream behavior.
5. **Proxy integration:** verify password login, unauthenticated API/WebSocket denial, terminal input/output, SSE reconnects, attachment uploads, session streaming, and forwarded protocol behind Umbrel's exact proxy. Decide an unused host-facing app port separately from internal 3000.
6. **Persistent data:** recreate the container and verify sessions, provider auth, app settings/passkeys, repositories, and generated SSH identity survive; validate migrations and backup/restore on the six data directories.
7. **Filesystem boundaries:** decide whether to offer access beyond dedicated workspaces. Do not silently share the host's home or another app's OpenCode state. External OpenCode deployments need matching workspace paths and explicit authentication tests.
8. **Update discipline:** verify whether in-app OpenCode/app upgrade actions should be disabled or documented as ephemeral. Rebuild with a reviewed OpenChamber/OpenCode pair instead of unpinned runtime updates.
9. **Authentication provisioning:** choose secure per-install password generation/storage/display compatible with Umbrel. Never hard-code a shared default or rely only on the app-store proxy's login.
10. **PWA/passkeys and assets:** verify secure-origin behavior on the intended access URL; confirm app-store artwork format requirements and any branding conditions before distribution.

## Source notes

Context7 was consulted for OpenChamber documentation as required for tool/framework documentation lookup. Its results included both old experimental recipes (`@openchamber/web@1.24.2` with `opencode-ai@1.18.31`) and V2 documentation. Those older recipes were **not** treated as current deployment instructions. Final compatibility and deployment claims above are anchored to first-party release/source files.

[dockerfile]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/Dockerfile
[compose]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/docker-compose.yml
[entrypoint]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/scripts/docker-entrypoint.sh
[web-package]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/package.json
[compatibility]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/server/lib/opencode/compatibility.js
[env-config]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/server/lib/opencode/env-config.js
[lifecycle]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/server/lib/opencode/lifecycle.js
[lifecycle-doc]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/server/lib/opencode/DOCUMENTATION.md
[projects-doc]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/server/lib/projects/DOCUMENTATION.md
[security]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/docs/content/docs/security.mdx
[ui-auth]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/server/lib/ui-auth/ui-auth.js
[ui-passkeys]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/packages/web/server/lib/ui-auth/ui-passkeys.js
[proxy]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/docs/REVERSE_PROXY.md
[license]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/LICENSE
[release-workflow]: https://github.com/openchamber/openchamber/blob/7521e712e9dbe12cce3c05debaa6d356fedea19b/.github/workflows/release.yml
