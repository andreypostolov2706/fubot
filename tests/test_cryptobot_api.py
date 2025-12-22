"""Quick test of CryptoBot API"""
import asyncio
import aiohttp
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Testnet API
API_URL = "https://testnet-pay.crypt.bot/api"
API_TOKEN = os.getenv("CRYPTOBOT_API_TOKEN", "23583:AAcMHMp7UCBlwTxMbYlp7iHxFCLfUWCt3GF")

async def test():
    if not API_TOKEN:
        print("Set CRYPTOBOT_API_TOKEN environment variable")
        return
    
    print(f"Testing CryptoBot Testnet API...")
    print(f"Token: {API_TOKEN[:10]}...")
    
    async with aiohttp.ClientSession() as session:
        # Test getMe
        async with session.get(
            f'{API_URL}/getMe',
            headers={'Crypto-Pay-API-Token': API_TOKEN}
        ) as response:
            print(f"\n=== getMe ===")
            print(f"Status: {response.status}")
            data = await response.json()
            if data.get("ok"):
                result = data.get("result", {})
                print(f"App ID: {result.get('app_id')}")
                print(f"Name: {result.get('name')}")
                print(f"Bot: @{result.get('payment_processing_bot_username')}")
            else:
                print(f"Error: {data}")
                return
        
        # Test getInvoices - check specific invoice
        invoice_id = input("\nEnter invoice_id to check (or press Enter to skip): ").strip()
        if invoice_id:
            async with session.get(
                f'{API_URL}/getInvoices',
                headers={'Crypto-Pay-API-Token': API_TOKEN},
                params={"invoice_ids": invoice_id}
            ) as response:
                print(f"\n=== getInvoices ({invoice_id}) ===")
                print(f"Status: {response.status}")
                data = await response.json()
                print(f"Response: {data}")
                if data.get("ok"):
                    items = data.get("result", {}).get("items", [])
                    if items:
                        inv = items[0]
                        print(f"Invoice status: {inv.get('status')}")
                        print(f"Amount: {inv.get('amount')} {inv.get('asset')}")
                        print(f"Paid at: {inv.get('paid_at')}")
                    else:
                        print("No invoices found!")
        
        # Test getBalance
        async with session.get(
            f'{API_URL}/getBalance',
            headers={'Crypto-Pay-API-Token': API_TOKEN}
        ) as response:
            print(f"\n=== getBalance ===")
            data = await response.json()
            if data.get("ok"):
                for bal in data.get("result", []):
                    if float(bal.get('available', 0)) > 0:
                        print(f"  {bal.get('currency_code')}: {bal.get('available')}")

if __name__ == "__main__":
    asyncio.run(test())
