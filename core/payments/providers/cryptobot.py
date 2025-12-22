"""
CryptoBot Payment Provider

Integration with @CryptoBot for cryptocurrency payments.
API Docs: https://help.crypt.bot/crypto-pay-api
"""
from __future__ import annotations
import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

import aiohttp
from loguru import logger

from .base import (
    BasePaymentProvider, 
    ProviderPaymentResult, 
    PaymentStatus,
    WebhookResult
)


# CryptoBot API endpoints
CRYPTOBOT_API_URL = "https://pay.crypt.bot/api"
CRYPTOBOT_TESTNET_URL = "https://testnet-pay.crypt.bot/api"


@dataclass
class CryptoBotInvoice:
    """CryptoBot invoice data"""
    invoice_id: int
    hash: str
    currency_type: str
    asset: Optional[str]
    fiat: Optional[str]
    amount: str
    pay_url: str
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    paid_amount: Optional[str] = None
    paid_asset: Optional[str] = None


class CryptoBotProvider(BasePaymentProvider):
    """
    CryptoBot payment provider.
    
    Supports payments in TON, USDT, BTC, ETH and other cryptocurrencies.
    
    Config:
        api_token: CryptoBot API token
        testnet: Use testnet (default: False)
    """
    
    # Supported cryptocurrencies
    SUPPORTED_ASSETS = ["TON", "USDT", "BTC", "ETH", "LTC", "BNB", "TRX", "USDC"]
    
    @property
    def id(self) -> str:
        return "cryptobot"
    
    @property
    def name(self) -> str:
        return "CryptoBot"
    
    @property
    def currencies(self) -> List[str]:
        return self.SUPPORTED_ASSETS
    
    @property
    def icon(self) -> str:
        return "🤖"
    
    @property
    def api_url(self) -> str:
        """Get API URL based on config"""
        if self.config.get("testnet", False):
            return CRYPTOBOT_TESTNET_URL
        return CRYPTOBOT_API_URL
    
    @property
    def api_token(self) -> str:
        """Get API token from config"""
        return self.config.get("api_token", "")
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate CryptoBot config"""
        if not self.api_token:
            return False, "API token is required"
        return True, None
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: dict = None
    ) -> dict:
        """
        Make API request to CryptoBot.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response JSON
        """
        url = f"{self.api_url}/{endpoint}"
        headers = {
            "Crypto-Pay-API-Token": self.api_token,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=headers, params=data) as response:
                    result = await response.json()
            else:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()
        
        if not result.get("ok"):
            error = result.get("error", {})
            error_msg = error.get("name", "Unknown error")
            logger.error(f"CryptoBot API error: {error_msg}")
            raise Exception(f"CryptoBot API error: {error_msg}")
        
        return result.get("result", {})
    
    async def get_me(self) -> dict:
        """Get bot info (for testing connection)"""
        return await self._request("GET", "getMe")
    
    async def get_balance(self) -> List[dict]:
        """Get bot balance"""
        return await self._request("GET", "getBalance")
    
    async def get_exchange_rates(self) -> List[dict]:
        """Get current exchange rates"""
        return await self._request("GET", "getExchangeRates")
    
    async def create_payment(
        self,
        amount: Decimal,
        currency: str,
        user_id: int,
        payment_uuid: str,
        description: str = None,
        **kwargs
    ) -> ProviderPaymentResult:
        """
        Create CryptoBot invoice.
        
        Args:
            amount: Amount in cryptocurrency
            currency: Crypto asset (TON, USDT, etc.)
            user_id: Internal user ID
            payment_uuid: Internal payment UUID
            description: Invoice description
            
        Returns:
            ProviderPaymentResult with pay_url
        """
        try:
            # Validate currency
            if currency not in self.SUPPORTED_ASSETS:
                return ProviderPaymentResult(
                    success=False,
                    error=f"Unsupported currency: {currency}. Supported: {', '.join(self.SUPPORTED_ASSETS)}"
                )
            
            # Prepare invoice data
            invoice_data = {
                "asset": currency,
                "amount": str(amount),
                "description": description or f"Payment #{payment_uuid[:8]}",
                "payload": payment_uuid,  # Our internal payment UUID
                "allow_comments": False,
                "allow_anonymous": True,
            }
            
            # Optional: expires_in (seconds)
            expires_in = kwargs.get("expires_in", 3600)  # 1 hour default
            if expires_in:
                invoice_data["expires_in"] = expires_in
            
            # Create invoice
            result = await self._request("POST", "createInvoice", invoice_data)
            
            logger.info(f"CryptoBot invoice created: {result.get('invoice_id')} for {amount} {currency}")
            
            return ProviderPaymentResult(
                success=True,
                payment_url=result.get("pay_url") or result.get("bot_invoice_url"),
                provider_payment_id=str(result.get("invoice_id")),
                raw_response=result
            )
            
        except Exception as e:
            logger.error(f"CryptoBot create_payment error: {e}")
            return ProviderPaymentResult(
                success=False,
                error=str(e)
            )
    
    async def check_payment(
        self,
        provider_payment_id: str
    ) -> PaymentStatus:
        """
        Check invoice status.
        
        Args:
            provider_payment_id: CryptoBot invoice_id
            
        Returns:
            Payment status
        """
        try:
            logger.debug(f"Checking payment status for invoice: {provider_payment_id}")
            
            result = await self._request("GET", "getInvoices", {
                "invoice_ids": provider_payment_id
            })
            
            logger.debug(f"CryptoBot getInvoices response: {result}")
            
            # Result can be a list directly or have 'items' key
            invoices = result if isinstance(result, list) else result.get("items", [])
            if not invoices:
                logger.warning(f"No invoices found for id: {provider_payment_id}")
                return PaymentStatus.PENDING  # Return pending instead of failed
            
            invoice = invoices[0]
            status = invoice.get("status", "").lower()
            
            logger.info(f"CryptoBot invoice {provider_payment_id} status: {status}")
            
            status_map = {
                "active": PaymentStatus.PENDING,
                "paid": PaymentStatus.COMPLETED,
                "expired": PaymentStatus.EXPIRED,
            }
            
            return status_map.get(status, PaymentStatus.PENDING)
            
        except Exception as e:
            logger.error(f"CryptoBot check_payment error: {e}")
            return PaymentStatus.PENDING  # Return pending on error, not failed
    
    async def handle_webhook(
        self,
        data: dict,
        headers: dict = None
    ) -> WebhookResult:
        """
        Handle CryptoBot webhook.
        
        CryptoBot sends webhooks when invoice status changes.
        
        Args:
            data: Webhook payload
            headers: HTTP headers with signature
            
        Returns:
            WebhookResult
        """
        try:
            # Verify signature
            if headers:
                signature = headers.get("crypto-pay-api-signature", "")
                if signature and not self._verify_signature(data, signature):
                    return WebhookResult(
                        success=False,
                        error="Invalid signature"
                    )
            
            # Parse update
            update_type = data.get("update_type")
            payload = data.get("payload", {})
            
            if update_type != "invoice_paid":
                return WebhookResult(
                    success=False,
                    error=f"Unknown update type: {update_type}"
                )
            
            # Extract payment info
            invoice_id = payload.get("invoice_id")
            payment_uuid = payload.get("payload")  # Our internal UUID
            status = payload.get("status", "").lower()
            
            if status == "paid":
                payment_status = PaymentStatus.COMPLETED
            elif status == "expired":
                payment_status = PaymentStatus.EXPIRED
            else:
                payment_status = PaymentStatus.PENDING
            
            logger.info(f"CryptoBot webhook: invoice {invoice_id} -> {status}")
            
            return WebhookResult(
                success=True,
                payment_uuid=payment_uuid,
                status=payment_status,
                provider_payment_id=str(invoice_id)
            )
            
        except Exception as e:
            logger.error(f"CryptoBot webhook error: {e}")
            return WebhookResult(
                success=False,
                error=str(e)
            )
    
    def _verify_signature(self, data: dict, signature: str) -> bool:
        """
        Verify webhook signature.
        
        CryptoBot uses HMAC-SHA-256 with token hash as key.
        """
        try:
            import json
            
            # Create secret key from token
            secret = hashlib.sha256(self.api_token.encode()).digest()
            
            # Create check string
            check_string = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            
            # Calculate HMAC
            expected = hmac.new(
                secret, 
                check_string.encode(), 
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected, signature)
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    async def get_invoice(self, invoice_id: str) -> Optional[CryptoBotInvoice]:
        """
        Get invoice details.
        
        Args:
            invoice_id: CryptoBot invoice ID
            
        Returns:
            CryptoBotInvoice or None
        """
        try:
            result = await self._request("GET", "getInvoices", {
                "invoice_ids": invoice_id
            })
            
            invoices = result.get("items", [])
            if not invoices:
                return None
            
            inv = invoices[0]
            return CryptoBotInvoice(
                invoice_id=inv.get("invoice_id"),
                hash=inv.get("hash"),
                currency_type=inv.get("currency_type"),
                asset=inv.get("asset"),
                fiat=inv.get("fiat"),
                amount=inv.get("amount"),
                pay_url=inv.get("pay_url") or inv.get("bot_invoice_url"),
                status=inv.get("status"),
                created_at=datetime.fromisoformat(inv.get("created_at").replace("Z", "+00:00")),
                paid_at=datetime.fromisoformat(inv["paid_at"].replace("Z", "+00:00")) if inv.get("paid_at") else None,
                paid_amount=inv.get("paid_amount"),
                paid_asset=inv.get("paid_asset")
            )
            
        except Exception as e:
            logger.error(f"CryptoBot get_invoice error: {e}")
            return None


# Create default instance (will be configured later)
cryptobot_provider = CryptoBotProvider()
