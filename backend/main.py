from flask import Flask, jsonify, request, send_from_directory
from fyers_auth import get_fyers_model
import sqlite3
import os
import time

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Create logs directory if it doesn't exist
if not os.path.exists("backend/logs"):
    os.makedirs("backend/logs")

fyers = get_fyers_model()

# Database setup
DB_FILE = "backend/paper_trading.db"

def init_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE portfolio (
            symbol TEXT PRIMARY KEY,
            quantity INTEGER,
            avg_price REAL,
            notes TEXT
        )
    """)
    c.execute("""
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            symbol TEXT,
            quantity INTEGER,
            price REAL,
            order_type TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/api/profile")
def get_profile():
    return jsonify({
        "username": "YH06631",
        "account_id": "VR12345"
    })

@app.route("/api/quotes")
def get_quotes():
    symbols = request.args.get("symbols")
    if not symbols:
        return jsonify({"error": "No symbols provided"}), 400

    data = {
        "symbols": symbols
    }
    response = fyers.quotes(data)
    return jsonify(response)

@app.route("/api/portfolio")
def get_portfolio():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT symbol, quantity, avg_price, notes FROM portfolio")
    portfolio = [{"symbol": row[0], "quantity": row[1], "avg_price": row[2], "notes": row[3]} for row in c.fetchall()]
    conn.close()
    return jsonify(portfolio)

@app.route("/api/portfolio/notes", methods=["POST"])
def update_notes():
    data = request.get_json()
    symbol = data.get("symbol")
    notes = data.get("notes")

    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE portfolio SET notes=? WHERE symbol=?", (notes, symbol))
    conn.commit()
    conn.close()

    return jsonify({"message": "Notes updated successfully"})

@app.route("/api/orders", methods=["POST"])
def place_order():
    data = request.get_json()
    symbol = data.get("symbol")
    quantity = data.get("quantity")
    order_type = data.get("order_type")
    price = data.get("price", 0)

    if not all([symbol, quantity, order_type]):
        return jsonify({"error": "Missing required fields"}), 400

    # Fetch current price for market orders
    if order_type == "MARKET":
        quote_response = fyers.quotes({"symbols": symbol})
        if quote_response["code"] == 200 and quote_response["d"]:
            price = quote_response["d"][0]["v"]["lp"]
        else:
            return jsonify({"error": "Failed to fetch market price"}), 500

    # Simulate order execution
    order_id = f"paper_{symbol}_{quantity}_{order_type}_{int(time.time())}"
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO orders (order_id, symbol, quantity, price, order_type, status) VALUES (?, ?, ?, ?, ?, ?)",
              (order_id, symbol, quantity, price, order_type, "EXECUTED"))

    # Update portfolio
    c.execute("SELECT quantity, avg_price FROM portfolio WHERE symbol=?", (symbol,))
    row = c.fetchone()
    if row:
        new_quantity = row[0] + quantity
        if new_quantity > 0:
            if quantity > 0: # Buy order
                new_avg_price = ((row[0] * row[1]) + (quantity * price)) / new_quantity
            else: # Sell order
                new_avg_price = row[1]
            c.execute("UPDATE portfolio SET quantity=?, avg_price=? WHERE symbol=?", (new_quantity, new_avg_price, symbol))
        else:
            c.execute("DELETE FROM portfolio WHERE symbol=?", (symbol,))
    elif quantity > 0:
        c.execute("INSERT INTO portfolio (symbol, quantity, avg_price, notes) VALUES (?, ?, ?, ?)", (symbol, quantity, price, ""))
    else:
        return jsonify({"error": "Cannot sell a stock you don't own"}), 400

    conn.commit()
    conn.close()

    return jsonify({"message": "Order placed successfully", "order_id": order_id})

if __name__ == "__main__":
    app.run(debug=True)
