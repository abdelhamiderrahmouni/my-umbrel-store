#!/usr/bin/env python3
"""Isolated amd64 container smoke test; not an umbrelOS integration test."""

import http.cookiejar
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener
import uuid


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True)


def main():
    repo = Path(__file__).resolve().parents[1]
    name = "openchamber-package-test-" + uuid.uuid4().hex[:10]
    password = secrets.token_hex(32)  # Same length/format as Umbrel APP_PASSWORD.
    with tempfile.TemporaryDirectory(prefix="openchamber-test-") as temporary:
        root = Path(temporary)
        env = dict(os.environ, APP_DATA_DIR=str(root), APP_PASSWORD=password)
        config = json.loads(subprocess.check_output([
            "docker", "compose", "-f",
            str(repo / "errahmounispace-openchamber/docker-compose.yml"),
            "config", "--no-consistency", "--format", "json",
        ], env=env, text=True))
        server = config["services"]["server"]
        assert server["platform"] == "linux/amd64"
        assert server["environment"]["OPENCHAMBER_UI_PASSWORD"] == password
        assert config["services"]["app_proxy"]["environment"]["APP_HOST"] == "errahmounispace-openchamber_server_1"
        assert int(config["services"]["app_proxy"]["environment"]["APP_PORT"]) == 3000
        assert len(server["volumes"]) == 6
        assert [(int(port["published"]), port["target"]) for port in server["ports"]] == [
            (port, port) for port in range(5100, 5120)
        ]
        command = ["run", "--detach", "--name", name, "--init",
                   "--platform", server["platform"],
                   "--env-file", str(root / "container.env")]
        with open(root / "container.env", "w", opener=lambda p, f: os.open(p, f, 0o600)) as output:
            for key, value in server["environment"].items():
                output.write(f"{key}={value}\n")
        targets = []
        for mount in server["volumes"]:
            source = Path(mount["source"])
            source.mkdir(parents=True)
            # Only these disposable fixture directories are changed.
            if os.getuid() != 1000:
                os.chown(source, 1000, 1000)
            targets.append(mount["target"])
            command += ["--mount", f"type=bind,src={source},dst={mount['target']}"]
        # Use temporary loopback host ports so the user's live container is untouched.
        for port in [3000, *range(5100, 5120)]:
            command += ["--publish", f"127.0.0.1::{port}"]
        command.append(server["image"])
        created = False
        try:
            docker(*command)
            created = True

            def ready_and_login():
                bindings = json.loads(docker("inspect", name))[0]["NetworkSettings"]["Ports"]
                base = "http://127.0.0.1:" + bindings["3000/tcp"][0]["HostPort"]
                opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
                for _ in range(60):
                    try:
                        with opener.open(base + "/health", timeout=3) as response:
                            if json.load(response).get("isOpenCodeReady"):
                                break
                    except (URLError, TimeoutError, ConnectionError):
                        pass
                    time.sleep(2)
                else:
                    raise AssertionError("OpenChamber/OpenCode did not become ready")
                for path in ["/auth/session", "/api/git/file-diff?path=test&directory=/home/openchamber/workspaces"]:
                    try:
                        opener.open(base + path, timeout=5)
                        raise AssertionError(f"Unauthenticated access allowed: {path}")
                    except HTTPError as error:
                        assert error.code == 401, (path, error.code)
                request = Request(base + "/auth/session", data=json.dumps({"password": password}).encode(),
                                  headers={"Content-Type": "application/json"})
                with opener.open(request, timeout=10) as response:
                    assert response.status == 200
                with opener.open(base + "/auth/session", timeout=5) as response:
                    assert json.load(response)["authenticated"]
                with opener.open(base + "/", timeout=5) as response:
                    assert response.status == 200 and "text/html" in response.headers["Content-Type"]
                # Execute the exact package healthcheck in the running container.
                docker("exec", name, *server["healthcheck"]["test"][1:])
                return bindings

            bindings = ready_and_login()
            assert docker("exec", name, "opencode", "--version").strip().removeprefix("opencode ").removeprefix("v") == "2.1.4"
            assert docker("exec", name, "bun", "-e",
                          "console.log((await Bun.file('packages/web/package.json').json()).version)").strip() == "2.5.1"
            assert docker("exec", name, "id", "-u").strip() == "1000"
            assert "MIT License" in docker("exec", name, "cat", "/home/openchamber/LICENSE")
            print("PASS: package image, non-root user, license, healthcheck, login and API auth")

            # Verify all 20 mappings using short-lived HTTP listeners in the fixture.
            code = '''import http.server, threading, sys
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'preview-ok')
    def log_message(self, *args): pass
for port in range(5100, 5120):
    server = http.server.ThreadingHTTPServer(('0.0.0.0', port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
print('ready', flush=True)
sys.stdin.read(1)
'''
            process = subprocess.Popen(["docker", "exec", "-i", name, "python3", "-u", "-c", code],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            try:
                assert process.stdout.readline().strip() == "ready"
                for port in range(5100, 5120):
                    host_port = bindings[f"{port}/tcp"][0]["HostPort"]
                    with build_opener().open(f"http://127.0.0.1:{host_port}/", timeout=5) as response:
                        assert response.read() == b"preview-ok"
            finally:
                process.communicate(input="x", timeout=10)
            print("PASS: all 20 preview container ports reachable through Docker mappings")

            for target in targets:
                docker("exec", name, "python3", "-c",
                       "from pathlib import Path; import sys; (Path(sys.argv[1])/'package-smoke-marker').write_text('persisted')", target)
            ssh_key = docker("exec", name, "cat", "/home/openchamber/.ssh/id_ed25519.pub")
            docker("stop", "--timeout", "30", name)
            docker("rm", name)
            created = False
            docker(*command)
            created = True
            ready_and_login()
            for target in targets:
                assert docker("exec", name, "cat", target + "/package-smoke-marker") == "persisted"
            assert docker("exec", name, "cat", "/home/openchamber/.ssh/id_ed25519.pub") == ssh_key
            print("PASS: full recreation preserves six data mounts and generated SSH identity")
        finally:
            if created:
                subprocess.run(["docker", "rm", "--force", name], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
