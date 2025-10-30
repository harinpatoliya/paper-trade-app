from flask import Flask, jsonify, request, send_from_directory
from fyers_auth import get_fyers_model
from flask_socketio import SocketIO
import sqlite3
import os
import time
import threading
from datetime import datetime
import pytz
from fyers_apiv3.FyersWebsocket import data_ws

app = Flask(__name__, static_folder='../frontend', static_url_path='')
socketio = SocketIO(app)

class WebSocketManager:
    def __init__(self, fyers_model, on_message_callback):
        self.fyers_model = fyers_model
        self.on_message = on_message_callback
        self.ws = None
        self.subscribed_symbols = set()
        self.lock = threading.Lock()
        self.thread = None

    def start(self):
        # Initial subscription from portfolio
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT symbol FROM portfolio")
        initial_symbols = [row[0] for row in c.fetchall()]
        conn.close()
        if initial_symbols:
            self.subscribed_symbols.update(initial_symbols)

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        self.ws = data_ws.FyersDataSocket(
            access_token=self.fyers_model.token,
            log_path="backend/logs"
        )
        self.ws.on_message = self.on_message
        self.ws.on_connect = self._on_connect
        self.ws.connect()

    def _on_connect(self):
        print("WebSocket connected. Resubscribing to symbols...")
        with self.lock:
            if self.subscribed_symbols:
                self.ws.subscribe(list(self.subscribed_symbols))

    def subscribe(self, symbols):
        with self.lock:
            new_symbols = [s for s in symbols if s not in self.subscribed_symbols]
            if not new_symbols:
                return

            self.subscribed_symbols.update(new_symbols)
            if self.ws and self.ws.is_connected():
                self.ws.subscribe(symbols=new_symbols)
            print(f"Subscribed to: {new_symbols}")

    def unsubscribe(self, symbols):
        with self.lock:
            symbols_to_unsubscribe = [s for s in symbols if s in self.subscribed_symbols]
            if not symbols_to_unsubscribe:
                return

            for s in symbols_to_unsubscribe:
                self.subscribed_symbols.remove(s)

            if self.ws and self.ws.is_connected():
                self.ws.unsubscribe(symbols=symbols_to_unsubscribe)
            print(f"Unsubscribed from: {symbols_to_unsubscribe}")

def on_price_update(message):
    socketio.emit('price_update', message)

fyers = get_fyers_model()
websocket_manager = WebSocketManager(fyers, on_price_update)

# Create logs directory if it doesn't exist
if not os.path.exists("backend/logs"):
    os.makedirs("backend/logs")

# Database setup
DB_FILE = "backend/paper_trading.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            symbol TEXT PRIMARY KEY,
            quantity INTEGER,
            avg_price REAL,
            notes TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            symbol TEXT,
            quantity INTEGER,
            price REAL,
            order_type TEXT,
            status TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS account (
            balance REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            quantity INTEGER,
            buy_price REAL,
            sell_price REAL,
            pnl REAL
        )
    """)
    # Check if account exists
    c.execute("SELECT * FROM account")
    if not c.fetchone():
        c.execute("INSERT INTO account (balance) VALUES (?)", (300000,))
    conn.commit()
    conn.close()

init_db()

def is_market_open():
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def execute_pending_orders():
    while True:
        if is_market_open():
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT * FROM orders WHERE status='PENDING'")
            pending_orders = c.fetchall()

            for order in pending_orders:
                order_id, symbol, quantity, price, order_type, _ = order
                quote_response = fyers.quotes({"symbols": symbol})
                if quote_response["code"] == 200 and quote_response["d"]:
                    current_price = quote_response["d"][0]["v"]["lp"]

                    # Check if limit price is reached
                    if (quantity > 0 and current_price <= price) or (quantity < 0 and current_price >= price):
                        # Execute the order
                        c.execute("UPDATE orders SET status='EXECUTED' WHERE order_id=?", (order_id,))

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
                                pnl = (price - row[1]) * abs(quantity)
                                c.execute("INSERT INTO trade_history (symbol, quantity, buy_price, sell_price, pnl) VALUES (?, ?, ?, ?, ?)",
                                          (symbol, abs(quantity), row[1], price, pnl))
                                c.execute("DELETE FROM portfolio WHERE symbol=?", (symbol,))
                        elif quantity > 0:
                            c.execute("INSERT INTO portfolio (symbol, quantity, avg_price, notes) VALUES (?, ?, ?, ?)", (symbol, quantity, price, ""))

                        # Update account balance
                        c.execute("SELECT balance FROM account")
                        balance = c.fetchone()[0]
                        new_balance = balance - (quantity * price)
                        c.execute("UPDATE account SET balance=?", (new_balance,))

            conn.commit()
            conn.close()
        time.sleep(10) # Check every 10 seconds

threading.Thread(target=execute_pending_orders, daemon=True).start()
websocket_manager.start()

@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/api/account")
def get_account():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance FROM account")
    balance = c.fetchone()[0]
    conn.close()
    return jsonify({"balance": balance})

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
    portfolio_data = c.fetchall()
    conn.close()

    portfolio = []
    for row in portfolio_data:
        symbol, quantity, avg_price, notes = row
        position_size = quantity * avg_price
        portfolio.append({
            "symbol": symbol,
            "quantity": quantity,
            "avg_price": avg_price,
            "notes": notes,
            "position_size": position_size
        })

    return jsonify(portfolio)

@app.route("/api/pending_orders")
def get_pending_orders():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE status='PENDING'")
    orders = [{"order_id": row[0], "symbol": row[1], "quantity": row[2], "price": row[3], "order_type": row[4], "status": row[5]} for row in c.fetchall()]
    conn.close()
    return jsonify(orders)

@app.route("/api/trade_history")
def get_trade_history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM trade_history")
    history = [{"trade_id": row[0], "symbol": row[1], "quantity": row[2], "buy_price": row[3], "sell_price": row[4], "pnl": row[5]} for row in c.fetchall()]
    conn.close()
    return jsonify(history)

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
    if not is_market_open():
        return jsonify({"error": "Market is closed"}), 400

    data = request.get_json()
    symbol = data.get("symbol")
    quantity = data.get("quantity")
    order_type = data.get("order_type")
    price = data.get("price", 0)

    if not all([symbol, quantity, order_type]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if order_type == "MARKET":
        quote_response = fyers.quotes({"symbols": symbol})
        if quote_response["code"] == 200 and quote_response["d"]:
            price = quote_response["d"][0]["v"]["lp"]
        else:
            conn.close()
            return jsonify({"error": "Failed to fetch market price"}), 500
        status = "EXECUTED"
    else:
        status = "PENDING"

    # Check for sufficient funds for buy orders
    if quantity > 0:
        c.execute("SELECT balance FROM account")
        balance = c.fetchone()[0]
        if balance < quantity * price:
            conn.close()
            return jsonify({"error": "Insufficient funds"}), 400

    order_id = f"paper_{symbol}_{quantity}_{order_type}_{int(time.time())}"
    c.execute("INSERT INTO orders (order_id, symbol, quantity, price, order_type, status) VALUES (?, ?, ?, ?, ?, ?)",
              (order_id, symbol, quantity, price, order_type, status))

    if status == "EXECUTED":
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
                pnl = (price - row[1]) * abs(quantity)
                c.execute("INSERT INTO trade_history (symbol, quantity, buy_price, sell_price, pnl) VALUES (?, ?, ?, ?, ?)",
                          (symbol, abs(quantity), row[1], price, pnl))
                c.execute("DELETE FROM portfolio WHERE symbol=?", (symbol,))
        elif quantity > 0:
            c.execute("INSERT INTO portfolio (symbol, quantity, avg_price, notes) VALUES (?, ?, ?, ?)", (symbol, quantity, price, ""))

        # Update account balance
        c.execute("SELECT balance FROM account")
        balance = c.fetchone()[0]
        new_balance = balance - (quantity * price)
        c.execute("UPDATE account SET balance=?", (new_balance,))

        # Subscribe/Unsubscribe from WebSocket
        if quantity > 0:
            websocket_manager.subscribe([symbol])
        elif new_quantity <= 0:
            websocket_manager.unsubscribe([symbol])

    conn.commit()
    conn.close()

    return jsonify({"message": "Order placed successfully", "order_id": order_id})

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
