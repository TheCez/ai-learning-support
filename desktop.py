"""
Desktop launcher for KI-Lernunterstützung.
Uses pywebview (Edge WebView2 on Windows) to host the Flask app in a native window.

Run with:
    python desktop.py
"""
import sys
import os
import time
import threading
import urllib.request

# ── Import webview FIRST (must happen before GUI setup) ───────────────────
import webview

# ── Flask setup ────────────────────────────────────────────────────────────
os.environ.setdefault('FLASK_ENV', 'production')

from app import app as flask_app

FLASK_PORT = 5000
FLASK_URL  = f'http://127.0.0.1:{FLASK_PORT}'


def _run_flask():
    flask_app.run(host='127.0.0.1', port=FLASK_PORT, debug=False, use_reloader=False, threaded=True)


def _wait_for_flask(max_tries=50):
    for i in range(max_tries):
        try:
            urllib.request.urlopen(FLASK_URL, timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def _start_and_wait():
    """Start Flask in background, then set the webview URL once ready."""
    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()

    print('[Desktop] Waiting for server …')
    if _wait_for_flask():
        print('[Desktop] Server ready — loading app')
        window.load_url(FLASK_URL)
    else:
        print('[Desktop] Server did not start!')
        webview.windows[0].destroy()


# ── Create window (shows loading screen while Flask boots) ────────────────
window = webview.create_window(
    title='KI-Lernunterstützung',
    # Show inline splash until Flask is ready
    html="""
    <html><body style="
      margin:0; background:#1a5c8a; color:#fff;
      font-family:system-ui,sans-serif;
      display:flex; flex-direction:column;
      align-items:center; justify-content:center; height:100vh; gap:18px;">
      <div style="font-size:56px">🎓</div>
      <div style="font-size:24px;font-weight:700">KI-Lernunterstützung</div>
      <div style="font-size:14px;opacity:.7">App wird gestartet …</div>
    </body></html>""",
    width=1440,
    height=920,
    min_size=(1024, 700),
    text_select=True,
    zoomable=True,
)

# ── Start Flask + redirect window in a helper thread ──────────────────────
init_thread = threading.Thread(target=_start_and_wait, daemon=True)
init_thread.start()

# ── Run the WebView event loop (MUST be on main thread) ───────────────────
webview.start(
    gui='edgechromium',   # Edge WebView2 — full Chromium APIs incl. audio/mic
    debug=False,
)
