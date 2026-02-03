import os
import asyncio
import yfinance as yf
from telegram import Bot

# ==========================================
# 1. SECURE CONFIGURATION
# ==========================================
TOKEN = os.getenv('TELE_TOK')
CHAT_ID = os.getenv('TELE_ID')

# Validate required environment variables
if not TOKEN:
    raise ValueError("❌ TELE_TOK environment variable is not set!")
if not CHAT_ID:
    raise ValueError("❌ TELE_ID environment variable is not set!")

INVESTED_AMOUNT = 50000  
TARGET_AMOUNT = 100000    
ENTRY_PRICE_MCX = 265000  

# ==========================================
# 2. THE INTELLIGENCE ENGINE
# ==========================================

def calculate_exit_strategy(current_mcx_price):
    current_value = (current_mcx_price / ENTRY_PRICE_MCX) * INVESTED_AMOUNT
    pnl_percent = ((current_value - INVESTED_AMOUNT) / INVESTED_AMOUNT) * 100
    
    status_msg = f"📈 Portfolio: ₹{current_value:,.0f} ({pnl_percent:+.2f}%)"
    
    if current_value >= TARGET_AMOUNT:
        advice = "🎯 **TARGET REACHED! SELL NOW.**"
    elif pnl_percent <= -10:
        advice = "⚠️ **STOP LOSS: Exit to save capital.**"
    else:
        advice = "💎 **HODL: Road to ₹1 Lakh.**"
        
    return status_msg, advice

async def run_sentinel():
    bot = Bot(token=TOKEN)
    
    try:
        # Fetching Data
        silver_df = yf.download("SI=F", period="100d", interval="1d")
        gold_data = yf.download("GC=F", period="1d")
        
        # 50-Day Moving Average
        silver_df['50DMA'] = silver_df['Close'].rolling(window=50).mean()
        
        curr_price_usd = silver_df['Close'].iloc[-1].item()
        curr_dma_usd = silver_df['50DMA'].iloc[-1].item()
        gold_price_usd = gold_data['Close'].iloc[-1].item()
        
        # Calculations
        gs_ratio = gold_price_usd / curr_price_usd
        approx_mcx = curr_price_usd * 3300 
        
        # 3-Day Rule
        green_light = (silver_df['Close'].iloc[-3:] > silver_df['50DMA'].iloc[-3:]).all()
        
        # Portfolio Stats
        portfolio_stats, exit_advice = calculate_exit_strategy(approx_mcx)

        # Signals
        status = "🔴 STANDBY"
        action = "Wait for better entry."
        if approx_mcx < 265000:
            status = "🟡 BUY WINDOW A"
            action = "Floor reached. Deploy ₹12,500."
        elif green_light:
            status = "🟢 GREEN LIGHT"
            action = "Trend confirmed. Deploy remaining capital."

        # THE MESSAGE
        report = (
            f"🤖 **SILVER SENTINEL CLOUD**\n"
            f"Status: {status}\n"
            f"MCX Estimate: ₹{approx_mcx:,.0f}/kg\n"
            f"---------------------------\n"
            f"{portfolio_stats}\n"
            f"Exit Signal: {exit_advice}\n"
            f"---------------------------\n"
            f"Gold-Silver Ratio: {gs_ratio:.2f}\n"
            f"50-DMA: ${curr_dma_usd:.2f}\n"
            f"---------------------------\n"
            f"💡 **STRATEGY:** {action}"
        )

        async with bot:
            await bot.send_message(chat_id=CHAT_ID, text=report, parse_mode='Markdown')

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':

    asyncio.run(run_sentinel())
