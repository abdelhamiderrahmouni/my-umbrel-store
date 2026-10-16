# ErrahmouniSpace Store

A personal Umbrel community app store maintained by [Abdelhamid Errahmouni](https://github.com/abdelhamiderrahmouni).

- Website: https://errahmounispace.com
- Repository: https://github.com/abdelhamiderrahmouni/my-umbrel-store
- Target: umbrelOS 2.0. App compatibility will be checked as apps are added.

## Add the store

In the umbrelOS App Store, add this repository as a community app store:

```text
https://github.com/abdelhamiderrahmouni/my-umbrel-store
```

## Apps

No apps are published yet. OpenChamber is a candidate for the first app.

## Adding an app

Each app lives in a directory named after its app ID, prefixed with `errahmounispace-` (for example, `errahmounispace-openchamber`).

Include these files:

- `umbrel-app.yml`: app ID, listing details, version, icon, screenshots, and support links.
- `docker-compose.yml`: container services, networking, and persistent storage.

Confirm the app's supported hardware architectures and test installation, access, and data persistence on umbrelOS before publishing it.
