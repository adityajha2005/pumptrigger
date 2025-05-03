import requests
import time
import hashlib
import hmac
import uuid
import json
from dotenv import load_dotenv
import schedule
import os
from datetime import datetime
import logging
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

# Trading Constants
BASE_URL = "https://api-testnet.bybit.com"
SYMBOL = "BTCUSDT"
RECV_WINDOW = str(5000)

# Trading Configuration
TRADE_CONFIG = {
    "quantity": "0.001",              # Base trade size in BTC
    "volume_threshold": 1000,         # 24h volume threshold
    "volume_increase": 20,            # Volume increase % to trigger trade
    "take_profit_pct": 2.0,          # Take profit percentage
    "stop_loss_pct": 1.0,            # Stop loss percentage
    "max_positions": 3,              # Maximum number of concurrent positions
    "min_volume_samples": 5,         # Minimum samples for volume average
}

# Global state
volume_history = deque(maxlen=TRADE_CONFIG["min_volume_samples"])
active_positions = {}

def get_timestamp():
    return str(int(time.time() * 10 ** 3))

def generate_signature(payload, timestamp):
    param_str = timestamp + api_key + RECV_WINDOW + payload
    signature = hmac.new(
        bytes(api_secret, "utf-8"),
        param_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return signature

def http_request(endpoint, method, params):
    url = f"{BASE_URL}{endpoint}"
    timestamp = get_timestamp()
    
    if isinstance(params, dict):
        payload = json.dumps(params)
    else:
        payload = params

    signature = generate_signature(payload, timestamp)
    
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': timestamp,
        'X-BAPI-RECV-WINDOW': RECV_WINDOW,
        'Content-Type': 'application/json'
    }

    try:
        if method == "POST":
            response = requests.request(method, url, headers=headers, data=payload)
        else:
            response = requests.request(method, url + "?" + payload, headers=headers)
        
        response_json = response.json()
        if response_json.get("retCode") != 0:
            logging.error(f"API Error: {response_json.get('retMsg', 'Unknown error')}")
            logging.error(f"Full Response: {response_json}")
            return None
            
        return response_json
    except Exception as e:
        logging.error(f"Request failed: {str(e)}")
        if 'response' in locals() and hasattr(response, 'text'):
            logging.error(f"Response: {response.text}")
        return None

def get_market_data():
    endpoint = "/v5/market/tickers"
    params = f"category=linear&symbol={SYMBOL}"
    return http_request(endpoint, "GET", params)

def get_positions():
    endpoint = "/v5/position/list"
    params = f"category=linear&symbol={SYMBOL}"
    return http_request(endpoint, "GET", params)

def place_order(side, order_type, quantity, price=None, take_profit=None, stop_loss=None):
    endpoint = "/v5/order/create"
    order_link_id = uuid.uuid4().hex
    
    params = {
        "category": "linear",
        "symbol": SYMBOL,
        "side": side,
        "positionIdx": 0,
        "orderType": order_type,
        "qty": str(quantity),
        "timeInForce": "GTC",
        "orderLinkId": order_link_id
    }
    
    if price:
        params["price"] = str(price)
    if take_profit:
        params["takeProfit"] = str(take_profit)
        params["tpTriggerBy"] = "MarkPrice"
    if stop_loss:
        params["stopLoss"] = str(stop_loss)
        params["slTriggerBy"] = "MarkPrice"
    
    return http_request(endpoint, "POST", params)

def analyze_volume(current_volume):
    """Analyze volume trends and decide if we should trade"""
    volume_history.append(current_volume)
    
    if len(volume_history) < TRADE_CONFIG["min_volume_samples"]:
        return False, 0
    
    avg_volume = sum(list(volume_history)[:-1]) / (len(volume_history) - 1)
    volume_increase = ((current_volume - avg_volume) / avg_volume) * 100
    
    should_trade = (volume_increase >= TRADE_CONFIG["volume_increase"] and 
                   current_volume >= TRADE_CONFIG["volume_threshold"])
    
    return should_trade, volume_increase

def manage_positions(current_price):
    """Manage existing positions"""
    positions = get_positions()
    if not positions or "result" not in positions:
        return
    
    position_data = positions["result"].get("list", [])
    for position in position_data:
        size = float(position.get("size", 0))
        if size > 0:
            entry_price = float(position.get("avgPrice", 0))
            current_pnl = float(position.get("unrealisedPnl", 0))
            
            print("\nPosition:")
            print(f"Entry: ${entry_price:.2f}")
            print(f"Current: ${current_price:.2f}")
            print(f"PnL: ${current_pnl:.2f}")

def trade_logic():
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] Checking market conditions...")

        market_data = get_market_data()
        if not market_data or "result" not in market_data:
            print("Error: Could not get market data")
            return

        ticker = market_data["result"]["list"][0]
        volume_24h = float(ticker.get("volume24h", 0))
        last_price = float(ticker.get("lastPrice", 0))
        
        print(f"\nBTC/USDT")
        print(f"24h Volume: {volume_24h:.2f}")
        print(f"Price: ${last_price:.2f}")

        manage_positions(last_price)

        should_trade, volume_increase = analyze_volume(volume_24h)
        print(f"Volume Change: {volume_increase:.2f}%")

        if should_trade:
            print("\nVolume spike detected!")
            print(f"Volume increased by {volume_increase:.2f}%")
            print("Placing trade...")

            try:
                take_profit_price = last_price * (1 + TRADE_CONFIG["take_profit_pct"] / 100)
                stop_loss_price = last_price * (1 - TRADE_CONFIG["stop_loss_pct"] / 100)
                
                order = place_order(
                    side="Buy",
                    order_type="Market",
                    quantity=TRADE_CONFIG["quantity"],
                    take_profit=take_profit_price,
                    stop_loss=stop_loss_price
                )
                
                if order and order.get("retCode") == 0:
                    print("\nOrder placed!")
                    print(f"Order ID: {order['result'].get('orderId', 'N/A')}")
                    print(f"Size: {TRADE_CONFIG['quantity']} BTC")
                    print(f"TP: ${take_profit_price:.2f}")
                    print(f"SL: ${stop_loss_price:.2f}")
                else:
                    print("Failed to place order")

            except Exception as e:
                print(f"Order error: {str(e)}")
        else:
            print("\nNo significant volume change")

    except Exception as e:
        print(f"Error: {str(e)}")

# Main execution
if __name__ == "__main__":
    print("Starting PumpTrigger Bot...")
    print("\nTrading Config:")
    for key, value in TRADE_CONFIG.items():
        print(f"{key}: {value}")

    print("\nStarting initial check...")
    trade_logic()

    print("\nSetting up scheduler...")
    schedule.every(1).minute.do(trade_logic)
    print("Bot running. Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBot stopped.")
    except Exception as e:
        print(f"\nError: {str(e)}")
