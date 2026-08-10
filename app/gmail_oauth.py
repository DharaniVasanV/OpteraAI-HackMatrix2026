import json
import os
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


def _load_env_file():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        return {}
    values = {}
    with open(env_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


ENV_VALUES = _load_env_file()
CLIENT_ID = os.getenv("GMAIL_CLIENT_ID") or ENV_VALUES.get("GMAIL_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET") or ENV_VALUES.get("GMAIL_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI") or ENV_VALUES.get("GMAIL_REDIRECT_URI", "http://127.0.0.1:8001/")
SCOPES = "https://www.googleapis.com/auth/gmail.readonly"

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        self.server.auth_code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OAuth flow complete. You can close this window.")

    def log_message(self, format, *args):
        return


def run_oauth_flow():
    print("Loading Gmail OAuth configuration...")
    print(f"Client ID loaded: {'yes' if CLIENT_ID else 'no'}")
    if not CLIENT_ID:
        raise RuntimeError("GMAIL_CLIENT_ID is not set")
    if not CLIENT_SECRET:
        raise RuntimeError("GMAIL_CLIENT_SECRET is not set")

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    })

    print("Open this URL in your browser to continue:")
    print(auth_url)
    webbrowser.open(auth_url)

    server = HTTPServer(("127.0.0.1", 8001), OAuthCallbackHandler)
    server.auth_code = None
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    while server.auth_code is None:
        time.sleep(0.1)

    server.shutdown()
    server.server_close()
    thread.join(timeout=1)

    if not server.auth_code:
        raise RuntimeError("OAuth flow did not complete")

    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": server.auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    print("Exchanging authorization code for tokens...")

    try:
        request = Request(
            token_url,
            data=urlencode(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
        data = json.loads(body)
    except (HTTPError, URLError) as exc:
        print("Token exchange failed:")
        if hasattr(exc, "read"):
            try:
                print(exc.read().decode("utf-8"))
            except Exception:
                print(str(exc))
        else:
            print(str(exc))
        raise

    print(f"GMAIL_ACCESS_TOKEN={data.get('access_token', '')}")
    print(f"GMAIL_REFRESH_TOKEN={data.get('refresh_token', '')}")
    print(f"GMAIL_CLIENT_ID={CLIENT_ID}")
    print(f"GMAIL_CLIENT_SECRET={CLIENT_SECRET}")

    env_path = os.path.join(os.getcwd(), ".env")

    # Read existing .env, replace token lines in-place (avoid duplicates on re-auth)
    existing_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as handle:
            existing_lines = handle.readlines()

    skip_keys = {"GMAIL_ACCESS_TOKEN", "GMAIL_REFRESH_TOKEN", "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET"}
    filtered = [ln for ln in existing_lines if not any(ln.startswith(k + "=") for k in skip_keys)]

    new_token_lines = [
        f"GMAIL_ACCESS_TOKEN={data.get('access_token', '')}\n",
        f"GMAIL_REFRESH_TOKEN={data.get('refresh_token', '')}\n",
        f"GMAIL_CLIENT_ID={CLIENT_ID}\n",
        f"GMAIL_CLIENT_SECRET={CLIENT_SECRET}\n",
    ]

    with open(env_path, "w", encoding="utf-8") as handle:
        handle.writelines(filtered)
        if filtered and not filtered[-1].endswith("\n"):
            handle.write("\n")
        handle.writelines(new_token_lines)

    print(f"Saved Gmail credentials to {env_path}")

    return data


if __name__ == "__main__":
    run_oauth_flow()
