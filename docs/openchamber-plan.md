# OpenChamber on ErrahmouniSpace Store

Status: package and licensed amd64 image built; local package smoke tests passed. Image published publicly with anonymous pull verified. Actual umbrelOS installation remains unverified.

## Steps

- [x] Research upstream deployment, OpenCode compatibility, storage, and authentication.
- [x] Confirm amd64 hardware, existing-project-folder support, and LAN preview access.
- [x] Create the Umbrel manifest, Compose package, persistent directories, and image build workflow.
- [x] Build the licensed image and verify local startup, authentication, preview mappings, and recreation persistence.
- [x] Publish the pinned image publicly and pass anonymous image checks.
- [ ] Install through umbrelOS 2.0 and verify proxy behavior, folder settings, and a real coding workflow.

## Implementation evidence (2026-10-25)

- Package: `errahmounispace-openchamber/`. UI port **3939**, internal web port **3000**, preview ports **5100–5119/TCP**. Owner explicitly approved exposing previews to the LAN despite their lack of proxy authentication. The description and README warn about trusted-network use and HTTP/HTTPS iframe limitations.
- Owner approved publishing the store-maintained image. The initial GHCR push failed with insufficient token scopes; after authorization was refreshed, the upload succeeded. GHCR visibility was changed from private to public and an anonymous Docker pull using an empty credentials directory succeeded. The registry digest matches the package's pinned digest.
- Built `ghcr.io/abdelhamiderrahmouni/openchamber:2.3.3-umbrel.1` locally. The wrapper adds only the upstream MIT license and image metadata. Index digest: `sha256:bd1c799a37ebdd5877318f6c4e5e603e4c9061644b0fd9b04baacb7bb6f7ae44`. Runnable platform: **linux/amd64 only**; ARM64 support remains deferred and is not claimed.
- `python3 scripts/test-openchamber.py` passed against the package's exact local image/configuration: UID 1000, license inclusion, package healthcheck, OpenCode readiness, password login using a 64-character hex password, unauthenticated session and Git API denial, UI HTML, all 20 preview mappings, and full container recreation preserving markers in all six data mounts plus generated SSH identity. It uses disposable fixtures and random loopback host ports, not the owner's live projects or LAN ports.
- Upstream Umbrel static linter: **0 errors**, one `ports.unresolved` warning because it cannot expand the preview range. Manually searched the official store's literal YAML/shell ports: no conflicts found for **3939** or **5100–5119**. Actual device port availability still needs testing.
- `--check-images` now resolves the public image successfully but reports `image.architecture`: the official-store linter requires both amd64 and arm64, whereas this approved personal-store package intentionally targets amd64 only. The preview range still produces the documented `ports.unresolved` warning. No claim of official-store multi-architecture compliance.
- GitHub workflow passed `actionlint` 1.7.12. `git diff --check` passed.
- No installation, changes, or runtime tests were performed on the owner's Umbrel device. Image layers contain no mounted project data, provider credentials, or app password; no working container was committed to an image.

## Goal

Install `errahmounispace-openchamber` from this community store on umbrelOS 2.0, open it from the Umbrel home screen, and use OpenChamber in a browser with persistent projects, configuration, and sessions.

Upstream deployment findings and citations: [OpenChamber research](openchamber-research.md).

## Research outcome and confirmed choices

- Canonical project: [openchamber/openchamber](https://github.com/openchamber/openchamber).
- Proposed release: **2.3.3**, commit `7521e712e9dbe12cce3c05debaa6d356fedea19b`, paired with bundled **OpenCode 2.0.29**.
- Owner's hardware: **x86-64 / amd64**. Test this architecture first; ARM64 support remains a separate build/test gate.
- Owner wants an **existing project folder**, not only an app-owned workspace. Offer an explicit writable `folderAccess` setting mapped to `/home/openchamber/workspaces`; select only the intended project directory. Keep a persistent app-owned workspace as the default before selection. Explain that agents can edit/delete the selected folder's contents. Validate UID/GID 1000 write access without recursively changing ownership of user files.
- No official upstream public image was verified. Upstream Compose builds from source. Our owner-approved `ghcr.io/abdelhamiderrahmouni/openchamber` image is now published publicly, and anonymous access is verified.

## Packaging approach

1. Verify the canonical OpenChamber project, its current release, and the supported OpenCode version. Do not substitute a newer OpenCode major version without upstream compatibility evidence.
2. Prefer a maintained upstream container that includes the required runtime. Pin a release tag and multi-architecture index digest, confirming public pulls and `linux/amd64` / `linux/arm64` support. If no acceptable image exists, agree on publishing a minimal image before implementing the package; do not build images during Umbrel installation.
3. Route the web service through Umbrel's `app_proxy`, keeping Umbrel login enabled. Set `APP_HOST` to `errahmounispace-openchamber_server_1` and `APP_PORT` to the verified internal listener. Choose a free host-facing manifest port separately.
4. Persist app-owned state under `${APP_DATA_DIR}/data/`: projects, OpenChamber settings, OpenCode configuration, provider credentials, and session storage. Map the exact upstream paths identified in research, not guessed generic paths. Use `storage: {dataRoot: data}` for relocatable storage.
5. Protect internal APIs as well as the browser route. Umbrel's shared Docker network is not an authentication boundary. Verify which listeners OpenChamber exposes, how backend credentials are configured, and whether proxy sessions protect direct API access. Do not publish a raw backend or terminal port.
6. Use app-owned storage as the initial default, then let the owner explicitly select their existing project folder through umbrelOS 2.0 `folderAccess`. No Docker socket, privileged mode, host networking, or broad host-directory mounts.
7. Make provider setup usable from the browser. Never commit provider credentials or request them in chat. Verify that the intended provider's login/key flow works and persists; document any limitation before shipping.

## Concrete runtime configuration

Build from the pinned upstream Dockerfile, retaining its non-root 1000:1000 user and bundled OpenCode. Proxy internal port **3000**. Set `OPENCHAMBER_UI_PASSWORD: ${APP_PASSWORD}` and manifest `deterministicPassword: true` after confirming login accepts the generated password; leave `defaultUsername` empty. Keep Umbrel authentication as an additional layer. No extra secret-generating script is needed for this password.

Translate the six upstream mounts into app-data bind mounts:

| App-data source | Container destination |
| --- | --- |
| `data/openchamber` | `/home/openchamber/.config/openchamber` |
| `data/opencode/share` | `/home/openchamber/.local/share/opencode` |
| `data/opencode/state` | `/home/openchamber/.local/state/opencode` |
| `data/opencode/config` | `/home/openchamber/.config/opencode` |
| `data/ssh` | `/home/openchamber/.ssh` |
| `data/workspaces` | `/home/openchamber/workspaces` |

The last mount is the initial default that the project-folder setting replaces. A user-selected external folder is not app-owned state: document its backup responsibility separately from app-data backups. Do not mount over the entire home directory, which would hide application files. Persist generated SSH keys; never publish private keys. Leave optional plugin auto-installation and public tunnels disabled.

Before publishing an image, test native dependency builds, actual Node/Bun versions, and the upstream daemon/log-following entrypoint's liveness and shutdown behavior. Record any necessary deviations from upstream. If a multi-architecture image cannot be built reliably, surface that limitation before deciding whether this personal store should carry an amd64-only package.

## Proposed package files

```text
errahmounispace-openchamber/
  umbrel-app.yml
  docker-compose.yml
  data/<verified-state-directories>/.gitkeep
  exports.sh  # only if additional derived credentials are required
```

Manifest: app ID and directory match; app name `OpenChamber`; accurate upstream developer, project, support, license-related attribution and version; submitter `Abdelhamid Errahmouni`; community-store icon from a stable permitted source; initial release notes and gallery may be empty. Explain that agents can execute commands and modify mounted project files, and that model-provider costs/accounts may apply.

Do not add databases, helper services, custom images, lifecycle hooks, or HTTPS-only requirements unless upstream behavior makes them necessary.

## Implementation sequence

1. Resolve image/runtime, authentication, and persistence questions from the research.
2. Confirm image publishing ownership, the selected project folder, and provider workflow. Architecture and preference for an existing project folder are already confirmed.
3. Create the minimal manifest and Compose package, including committed empty data directories.
4. Validate manifest YAML, image platforms/pinning, proxy wiring, writable mounts, and host-port availability. This template has no `npm run lint:apps` script; use the upstream Umbrel linter from a separate checkout if available rather than claiming it ran here. Run `git diff --check`.
5. With owner-approved device access or a suitable test environment, install through Umbrel and perform the acceptance checks below.
6. Update the store README with the app and tested limitations. Commit or publish only when requested.

## Acceptance checks

- Fresh install on umbrelOS 2.0; record actual CPU architecture and package/image version.
- Open through the Umbrel home screen, not a directly published container port. Test both HTTP and HTTPS.
- An unauthenticated browser cannot access protected UI, API, terminal, or streaming endpoints.
- Verify native app/backend authentication against direct access from the shared Docker network.
- Configure a provider in the browser, open a disposable project, send a prompt, receive a streaming reply, and verify a controlled file edit. Test terminal and Git features if included in the image.
- Restart through Umbrel: project files, settings, provider login, and sessions survive.
- Verify data directories are writable with the image's supported runtime user; do not blindly override its entrypoint user.
- Check logs for failures and accidental credential disclosure; do not include secrets in test evidence.
- Test relocation to external storage if offered, then reopen and verify the same state.
- Confirm supported image architectures separately from runtime-tested architectures. Do not label an untested architecture as verified.

## Owner decisions still needed

- Public image publishing and anonymous pull verification are complete. Committing/pushing the app package and actual Umbrel installation remain separate steps.
- Which existing project folder should be selected? Prefer selection in Umbrel's UI rather than hardcoding a host path.
- Which model provider/login flow should the first end-to-end test cover? No credentials needed for planning.
- Local network/private VPN only for previews, as approved. No internet port forwarding or public preview exposure is configured.

## Umbrel primary sources

- [Packaging rules](https://github.com/getumbrel/umbrel-apps/blob/master/.agents/skills/umbrel-package-app/SKILL.md): manifest, storage relocation, image pinning and architecture, shared-network risks, proxy auth, environment variables, and runtime constraints.
- [Testing rules](https://github.com/getumbrel/umbrel-apps/blob/master/.agents/skills/umbrel-test-app/SKILL.md): installation through Umbrel, HTTP/HTTPS, meaningful workflows, restart/persistence, and honest evidence reporting.
- [Code Server package](https://github.com/getumbrel/umbrel-apps/blob/master/code-server/docker-compose.yml): comparable browser development app using proxy routing, persistent home, and an Umbrel-generated app password.

These are current upstream sources, not proof of installation on this owner's device. Recheck behavior against the exact installed umbrelOS 2.0 build when implementing.
