import os
import asyncio
import threading
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename

from config import Config
from automation import (browser_pool, AccountSession,
                        ChurchReportFiller, CellReportFiller)

app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------
def push_log(msg: str):
    socketio.emit("log", {"message": msg})


def read_table(file_storage) -> pd.DataFrame:
    filename = secure_filename(file_storage.filename)
    path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file_storage.save(path)
    if filename.lower().endswith(".csv"):
        return pd.read_csv(path)
    return pd.read_excel(path)


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload/accounts", methods=["POST"])
def upload_accounts():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file"}), 400
    try:
        df = read_table(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    required = {"account_id", "username", "password"}
    if not required.issubset(df.columns):
        return jsonify({"error": f"CSV must have columns {required}"}), 400
    return jsonify({"ok": True, "accounts": df.to_dict(orient="records")})


@app.route("/upload/church", methods=["POST"])
def upload_church():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file"}), 400
    try:
        df = read_table(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    if "event_date" not in df.columns:
        return jsonify({"error": "Missing 'event_date' column"}), 400
    return jsonify({"ok": True, "count": len(df),
                    "rows": df.fillna("").astype(str).to_dict(orient="records")})


@app.route("/upload/cell", methods=["POST"])
def upload_cell():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file"}), 400
    try:
        df = read_table(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    if "date_of_meeting" not in df.columns:
        return jsonify({"error": "Missing 'date_of_meeting' column"}), 400
    return jsonify({"ok": True, "count": len(df),
                    "rows": df.fillna("").astype(str).to_dict(orient="records")})


@app.route("/run", methods=["POST"])
def run():
    payload = request.json
    accounts = payload.get("accounts", [])
    church_rows = payload.get("church_rows", [])
    cell_rows = payload.get("cell_rows", [])
    if not accounts:
        return jsonify({"error": "No accounts"}), 400
    if not church_rows and not cell_rows:
        return jsonify({"error": "No report rows"}), 400

    threading.Thread(
        target=lambda: asyncio.run(_run_all(accounts, church_rows, cell_rows)),
        daemon=True,
    ).start()

    return jsonify({
        "ok": True,
        "message": f"Started — {len(accounts)} account(s), "
                   f"{len(church_rows)} church report(s), "
                   f"{len(cell_rows)} cell report(s)"
    })


# ------------------------------------------------------------------
# Async runner
# ------------------------------------------------------------------
async def _run_all(accounts, church_rows, cell_rows):
    push_log("[system] Launching browser pool...")
    await browser_pool.start()
    sem = asyncio.Semaphore(Config.MAX_CONCURRENT_ACCOUNTS)

    async def worker(account):
        async with sem:
            sess = AccountSession(
                account["account_id"], account["username"], account["password"]
            )
            if not await sess.login(browser_pool, log=push_log):
                await sess.close()
                return

            # Run church reports for this account
            if church_rows:
                cf = ChurchReportFiller(sess, log=push_log)
                for i, row in enumerate(church_rows):
                    push_log(f"[{sess.account_id}] Church {i+1}/{len(church_rows)}")
                    res = await cf.submit(row)
                    socketio.emit("result", res)
                    await asyncio.sleep(1)

            # Run cell reports for this account
            if cell_rows:
                cel = CellReportFiller(sess, log=push_log)
                for i, row in enumerate(cell_rows):
                    push_log(f"[{sess.account_id}] Cell {i+1}/{len(cell_rows)}")
                    res = await cel.submit(row)
                    socketio.emit("result", res)
                    await asyncio.sleep(1)

            await sess.close()
            push_log(f"[{sess.account_id}] Session closed")

    try:
        await asyncio.gather(*(worker(a) for a in accounts))
        push_log("[system] ✅ All reports finished.")
        socketio.emit("done", {})
    finally:
        await browser_pool.stop()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)