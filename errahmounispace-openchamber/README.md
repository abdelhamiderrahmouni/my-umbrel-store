# OpenChamber for umbrelOS 2.0

Package ID: `errahmounispace-openchamber`. OpenChamber **2.3.3**, OpenCode **2.0.29**, image build **2.3.3-umbrel.1**. This personal-store package is **amd64 only**, not an official Umbrel App Store submission or an ARM64-compatible release.

## Release status

The pinned image was published to GHCR on 2026-10-25, made public, and successfully pulled with an empty Docker credentials directory. Its registry digest matches this package. Local package tests passed; actual installation through umbrelOS is still unverified. See [image publishing](../images/openchamber/README.md).

## First use

1. Install through your ErrahmouniSpace community store and open the app from Umbrel (port **3939**).
2. Keep Umbrel's "Require Umbrel login" enabled. OpenChamber also requires the per-install app password shown by Umbrel; no username is required.
3. Connect a model provider in OpenChamber. Never put provider credentials in this repository. Provider usage may cost money.
4. Create/open a project under `/home/openchamber/workspaces`. To work on an existing directory, select it in Umbrel's app settings → Projects. This replaces the default workspace mount; it does not copy or delete the previous workspace.

The image runs as UID/GID **1000:1000**. Selected project folders must allow that identity to write. Do not recursively change permissions on a whole drive to work around a denied folder. Only select folders the coding agent should be allowed to modify, and back up selected folders separately.

## Project previews

Ports **5100–5119/TCP** are reserved for your development servers. They must be free on the Umbrel device at installation; port conflicts can prevent startup. OpenChamber's UI uses `app_proxy` instead of a directly published container port.

Start your dev server inside OpenChamber on `0.0.0.0`, for example:

```sh
# In your project terminal; example for a project that already uses Vite:
npm run dev -- --host 0.0.0.0 --port 5100
```

Open `http://YOUR-UMBREL-IP:5100` in OpenChamber's browser panel or a separate tab. Your laptop's `localhost` is not your Umbrel. Some frameworks require explicitly allowing your Umbrel hostname; use a narrow allowlist, not a wildcard.

**These ports bypass both Umbrel and OpenChamber authentication and use plain HTTP.** Use a trusted LAN/private VPN only; never expose them through internet port forwarding. Protect sensitive dev apps with their own authentication. The app password protects OpenChamber, not your preview servers.

Browsers can block HTTP iframes inside an HTTPS page. Use a separate HTTP tab rather than disabling browser security; an authenticated HTTPS preview proxy would be a separate future feature. External websites may forbid framing with their own headers. Port mappings do not bypass these restrictions or enable agent control of a cross-origin iframe. In web mode, agent-driven testing requires a compatible browser-provider extension; none is bundled here.

## Data and updates

All six upstream persistent directories use `${APP_DATA_DIR}/data/`: OpenChamber configuration, OpenCode share/state/config, SSH identity, and the default workspace. No runtime data belongs in `/tmp`. Umbrel can relocate this app-data folder using `storage.dataRoot`.

Backups contain credentials, private SSH keys, conversations, and source code: keep them private. An externally selected project folder is not part of the default app-data workspace backup. Data written elsewhere in the container, additional globally installed tools, and in-app CLI upgrades may be lost during recreation. Upgrade OpenChamber/OpenCode together through a reviewed image, not an unpinned runtime upgrade.

The healthcheck reports whether the managed OpenCode service is ready. Docker's `on-failure` policy restarts a crashed entrypoint, but an `unhealthy` status alone does not restart the container; check logs/restart through Umbrel if needed.

No Docker socket, privileged mode, host networking, browser engine, or public tunnel is included.

## Verification

Run the isolated package smoke test from the repository root:

```sh
python3 scripts/test-openchamber.py
```

It requires Docker with Compose, the pinned image available locally, and directory write access for UID 1000. It creates disposable test data and random loopback port mappings, then removes only its own test container and data; it does not touch your live OpenChamber container.

The licensed package image passed local amd64 checks: startup, password login, UI HTML, OpenCode readiness, non-root runtime, healthcheck, API authentication, all 20 preview mappings, and full recreation preserving all six mount contents and generated SSH identity. Package-specific evidence and remaining release gates are tracked in [the plan](../docs/openchamber-plan.md). An actual umbrelOS install, Umbrel proxy HTTP/HTTPS, Projects folder setting, and external-storage relocation still require device testing. Source review and raw Docker checks are not Umbrel verification.

Upstream: https://github.com/openchamber/openchamber. MIT license: [redistribution notice](../images/openchamber/LICENSE).
