"""Fetch official PDFs/HTML with legacy-renegotiation TLS tolerated (eduhk.hk needs it)."""
import os
import ssl
import sys
import requests
from requests.adapters import HTTPAdapter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RAW = os.path.join(ROOT, "work", "2027", "raw")


def session():
    ctx = ssl.create_default_context()
    ctx.options |= 0x4  # SSL_OP_LEGACY_SERVER_CONNECT
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    class A(HTTPAdapter):
        def init_poolmanager(self, *a, **kw):
            kw["ssl_context"] = ctx
            super().init_poolmanager(*a, **kw)

        def proxy_manager_for(self, *a, **kw):
            kw["ssl_context"] = ctx
            return super().proxy_manager_for(*a, **kw)

    s = requests.Session()
    s.mount("https://", A())
    s.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
    return s


def get(url, out=None, timeout=90):
    r = session().get(url, timeout=timeout)
    print(r.status_code, len(r.content), r.headers.get("content-type"), url)
    if out:
        with open(os.path.join(RAW, out), "wb") as f:
            f.write(r.content)
    return r


if __name__ == "__main__":
    args = sys.argv[1:]
    get(args[0], args[1] if len(args) > 1 else None)
