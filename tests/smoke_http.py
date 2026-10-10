"""
[INPUT]: 依赖已安装的 MCP 客户端、子进程与临时目录
[OUTPUT]: 提供独立运行的无凭据 HTTP 冒烟检查
[POS]: tests 的发布验收入口；启动独立端口，不读取用户配置或调用 Google
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import asyncio
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def check(port):
    async with streamablehttp_client(f"http://127.0.0.1:{port}/mcp", timeout=10) as (read, write, _):
        async with ClientSession(read, write) as client:
            await client.initialize()
            tools = (await client.list_tools()).tools
            assert len(tools) == 30, f"Expected 30 tools, got {len(tools)}"
            assert all(tool.description for tool in tools)
            result = await client.call_tool("get_account_status", {})
            assert not result.isError
            payload = json.loads(result.content[0].text)
            assert payload == {"client_config_exists": False, "token_exists": False, "ready": False}
            print("HTTP smoke passed: 30 tools; isolated missing-credentials response verified.")


def main():
    with tempfile.TemporaryDirectory(prefix="gsc-smoke-") as directory:
        root = Path(directory)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        (root / "server.yaml").write_text(f"server:\n  host: 127.0.0.1\n  port: {port}\n")
        # JSON 是 YAML 的子集，保持 Windows 路径转义。
        (root / "paths.yaml").write_text(json.dumps({"paths": {
            "oauth_client_path": str(root / "missing-client.json"),
            "token_path": str(root / "missing-token.json"),
            "audit_log_path": str(root / "audit.jsonl"),
            "snapshot_root": str(root / "snapshots"),
        }}))
        with (root / "server.log").open("w+") as log:
            process = subprocess.Popen([
                sys.executable, "-m", "google_search_console_mcp.server",
                "--server-config", str(root / "server.yaml"), "--paths-config", str(root / "paths.yaml"),
            ], cwd=root, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("Smoke server exited during startup")
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                            break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise TimeoutError("Smoke server did not start within 20 seconds")
                asyncio.run(check(port))
            except Exception:
                log.seek(0)
                print(log.read(), file=sys.stderr)
                raise
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    main()
