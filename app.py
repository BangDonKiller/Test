"""
Flask Web Server for 記帳程式 (Accounting App)
Provides a REST API and serves the single-page front-end.
"""

import calendar
import json
import os
from datetime import date

from flask import Flask, abort, jsonify, render_template, request

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "transactions.json")


# ── Data helpers ───────────────────────────────────────────────────────────────

def load_data() -> dict:
    """Load transactions from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_data(data: dict) -> None:
    """Persist transactions to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _validate_transaction(payload: dict) -> tuple[dict | None, str]:
    """Validate and normalise a transaction payload. Returns (transaction, error)."""
    t_type = payload.get("type", "")
    if t_type not in ("income", "expense"):
        return None, "type 必須為 income 或 expense"

    category = str(payload.get("category", "")).strip()
    if not category:
        return None, "category 不可為空"

    try:
        amount = float(payload.get("amount", 0))
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return None, "amount 必須為正數"

    note = str(payload.get("note", "")).strip()

    return {
        "type": t_type,
        "category": category,
        "amount": amount,
        "note": note,
    }, ""


# ── Page route ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── API: all transactions ──────────────────────────────────────────────────────

@app.route("/api/transactions", methods=["GET"])
def get_all_transactions():
    """Return all transactions keyed by date string."""
    return jsonify(load_data())


# ── API: transactions for a specific month ─────────────────────────────────────

@app.route("/api/transactions/month/<int:year>/<int:month>", methods=["GET"])
def get_month_summary(year: int, month: int):
    """Return summary (income/expense/balance) and day markers for a month."""
    if not (1 <= month <= 12):
        abort(400, description="月份必須在 1-12 之間")

    data = load_data()
    income_total = 0.0
    expense_total = 0.0
    days_with_transactions: list[str] = []

    for date_str, transactions in data.items():
        try:
            d = date.fromisoformat(date_str)
        except ValueError:
            continue
        if d.year == year and d.month == month:
            for t in transactions:
                if t["type"] == "income":
                    income_total += t["amount"]
                else:
                    expense_total += t["amount"]
            if transactions:
                days_with_transactions.append(date_str)

    return jsonify({
        "year": year,
        "month": month,
        "income": income_total,
        "expense": expense_total,
        "balance": income_total - expense_total,
        "days_with_transactions": days_with_transactions,
    })


# ── API: transactions for a specific date ─────────────────────────────────────

@app.route("/api/transactions/<date_str>", methods=["GET"])
def get_transactions(date_str: str):
    """Return all transactions for a specific date (YYYY-MM-DD)."""
    try:
        date.fromisoformat(date_str)
    except ValueError:
        abort(400, description="日期格式錯誤，請使用 YYYY-MM-DD")
    data = load_data()
    return jsonify(data.get(date_str, []))


@app.route("/api/transactions/<date_str>", methods=["POST"])
def add_transaction(date_str: str):
    """Add a new transaction for the given date."""
    try:
        date.fromisoformat(date_str)
    except ValueError:
        abort(400, description="日期格式錯誤，請使用 YYYY-MM-DD")

    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="請傳送 JSON 格式的資料")

    transaction, error = _validate_transaction(payload)
    if error:
        abort(400, description=error)

    data = load_data()
    data.setdefault(date_str, []).append(transaction)
    save_data(data)
    return jsonify({"success": True, "transactions": data[date_str]}), 201


# ── API: modify / delete a specific transaction ────────────────────────────────

@app.route("/api/transactions/<date_str>/<int:index>", methods=["PUT"])
def edit_transaction(date_str: str, index: int):
    """Replace the transaction at [date_str][index] with the request body."""
    try:
        date.fromisoformat(date_str)
    except ValueError:
        abort(400, description="日期格式錯誤，請使用 YYYY-MM-DD")

    data = load_data()
    if date_str not in data or index < 0 or index >= len(data[date_str]):
        abort(404, description="找不到指定的記帳記錄")

    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="請傳送 JSON 格式的資料")

    transaction, error = _validate_transaction(payload)
    if error:
        abort(400, description=error)

    data[date_str][index] = transaction
    save_data(data)
    return jsonify({"success": True, "transactions": data[date_str]})


@app.route("/api/transactions/<date_str>/<int:index>", methods=["DELETE"])
def delete_transaction(date_str: str, index: int):
    """Delete the transaction at [date_str][index]."""
    try:
        date.fromisoformat(date_str)
    except ValueError:
        abort(400, description="日期格式錯誤，請使用 YYYY-MM-DD")

    data = load_data()
    if date_str not in data or index < 0 or index >= len(data[date_str]):
        abort(404, description="找不到指定的記帳記錄")

    data[date_str].pop(index)
    if not data[date_str]:
        del data[date_str]
    save_data(data)
    return jsonify({"success": True})


# ── Error handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(e):
    return jsonify({"error": str(e.description)}), e.code


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    app.run(debug=False, host=host, port=port)
