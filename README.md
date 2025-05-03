# 🤖 PumpTrigger Trading Bot

An automated cryptocurrency trading bot that executes trades based on volume analysis on the Bybit exchange.

## Features

- 📊 Real-time volume analysis and tracking
- 🎯 Automated trade execution with configurable parameters
- 🛡️ Built-in risk management with Take Profit and Stop Loss
- 📈 Position management and tracking
- 🔄 Continuous market monitoring
- 📝 Detailed logging of all operations

## Requirements

- Python 3.8+
- Bybit API credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/adityajha2005/pumptrigger.git
cd pumptrigger
```

2. Install required packages:
```bash
pip install requests python-dotenv schedule
```

3. Create a `.env` file in the project root:
```env
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
```

## Configuration

The bot's behavior can be customized through the `TRADE_CONFIG` dictionary in `botscript.py`:

```python
TRADE_CONFIG = {
    "quantity": "0.001",              # Base trade size in BTC
    "volume_threshold": 1000,         # 24h volume threshold
    "volume_increase": 20,            # Volume increase % to trigger trade
    "take_profit_pct": 2.0,          # Take profit percentage
    "stop_loss_pct": 1.0,            # Stop loss percentage
    "max_positions": 3,              # Maximum concurrent positions
    "min_volume_samples": 5,         # Minimum samples for volume average
}
```

## Usage

1. Configure your API credentials in the `.env` file
2. Adjust trading parameters in `TRADE_CONFIG` if needed
3. Run the bot:
```bash
python botscript.py
```

## Trading Strategy

The bot implements a volume-based trading strategy:

1. **Volume Analysis**:
   - Tracks 24-hour trading volume
   - Calculates rolling volume average
   - Detects significant volume increases

2. **Trade Execution**:
   - Enters positions when volume increases significantly
   - Places market orders with automatic TP/SL
   - Manages multiple positions simultaneously

3. **Risk Management**:
   - Automatic Take Profit orders
   - Automatic Stop Loss orders
   - Position size limits
   - Maximum position count

## Sample Output

```
🤖 PumpTrigger Trading Bot Starting...

📊 Trading Configuration:
    quantity: 0.001
    volume_threshold: 1000
    volume_increase: 20
    take_profit_pct: 2.0
    stop_loss_pct: 1.0
    max_positions: 3
    min_volume_samples: 5

🚀 Executing initial trade check...
✅ Bot will now check for trades every minute
```

## Warning

This bot is for educational purposes only. Cryptocurrency trading carries significant risks. Always test thoroughly on testnet before using real funds.

## License

MIT License - feel free to modify and use as you wish.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. 