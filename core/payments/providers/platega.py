"""
Platega Payment Provider

Integration with Platega.io for SBP (СБП) payments.
API Docs: https://docs.platega.io/
"""
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


# Platega API endpoint
PLATEGA_API_URL = "https://app.platega.io"


@dataclass
class PlategalTransaction:
    """Platega transaction data"""
    transaction_id: str
    payment_method: str
    redirect_url: str
    status: str
    amount: Decimal
    currency: str
    expires_in: str
    usdt_rate: Optional[float] = None


class PlategalProvider(BasePaymentProvider):
    """
    Platega payment provider.
    
    Supports payments via SBP (СБП QR).
    
    Config:
        merchant_id: Platega Merchant ID
        api_key: Platega API Key
    """
    
    # Payment methods
    PAYMENT_METHOD_SBP = 2  # СБП QR
    
    @property
    def id(self) -> str:
        return "platega"
    
    @property
    def name(self) -> str:
        return "СБП (Platega)"
    
    @property
    def currencies(self) -> List[str]:
        return ["RUB"]
    
    @property
    def icon(self) -> str:
        return "🏦"
    
    @property
    def api_url(self) -> str:
        return PLATEGA_API_URL
    
    @property
    def merchant_id(self) -> str:
        """Get Merchant ID from config"""
        return self.config.get("merchant_id", "")
    
    @property
    def api_key(self) -> str:
        """Get API Key from config"""
        return self.config.get("api_key", "")
    
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate Platega config"""
        if not self.merchant_id:
            return False, "Merchant ID is required"
        if not self.api_key:
            return False, "API Key is required"
        return True, None
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: dict = None
    ) -> dict:
        """
        Make API request to Platega.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response JSON
        """
        url = f"{self.api_url}/{endpoint}"
        headers = {
            "X-MerchantId": self.merchant_id,
            "X-Secret": self.api_key,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=headers, params=data) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"Platega API error: {response.status} - {text}")
                        raise Exception(f"Platega API error: {response.status}")
                    result = await response.json()
            else:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"Platega API error: {response.status} - {text}")
                        raise Exception(f"Platega API error: {response.status}")
                    result = await response.json()
        
        return result
    
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
        Create Platega payment (SBP QR).
        
        Args:
            amount: Amount in RUB
            currency: Currency (RUB)
            user_id: Internal user ID
            payment_uuid: Internal payment UUID
            description: Payment description
            
        Returns:
            ProviderPaymentResult with redirect URL
        """
        try:
            # Validate currency
            if currency not in self.currencies:
                return ProviderPaymentResult(
                    success=False,
                    error=f"Unsupported currency: {currency}. Supported: {', '.join(self.currencies)}"
                )
            
            # Prepare payment data
            payment_data = {
                "paymentMethod": self.PAYMENT_METHOD_SBP,
                "paymentDetails": {
                    "amount": int(amount),  # Amount in RUB (integer)
                    "currency": "RUB"
                },
                "description": description or f"Пополнение баланса #{payment_uuid[:8]}",
                "return": kwargs.get("return_url", "https://t.me"),
                "failedUrl": kwargs.get("failed_url", "https://t.me"),
                "payload": f"{payment_uuid}:{user_id}"  # Our internal data
            }
            
            # Create payment
            result = await self._request("POST", "transaction/process", payment_data)
            
            transaction_id = result.get("transactionId")
            redirect_url = result.get("redirect")
            
            logger.info(f"Platega payment created: {transaction_id} for {amount} RUB")
            
            return ProviderPaymentResult(
                success=True,
                payment_url=redirect_url,
                provider_payment_id=transaction_id,
                raw_response=result
            )
            
        except Exception as e:
            logger.error(f"Platega create_payment error: {e}")
            return ProviderPaymentResult(
                success=False,
                error=str(e)
            )
    
    async def check_payment(
        self,
        provider_payment_id: str
    ) -> PaymentStatus:
        """
        Check payment status.
        
        Args:
            provider_payment_id: Platega transaction ID
            
        Returns:
            Payment status
        """
        try:
            logger.debug(f"Checking Platega payment status: {provider_payment_id}")
            
            result = await self._request("GET", f"transaction/status/{provider_payment_id}")
            
            status = result.get("status", "").upper()
            
            logger.info(f"Platega payment {provider_payment_id} status: {status}")
            
            status_map = {
                "PENDING": PaymentStatus.PENDING,
                "CONFIRMED": PaymentStatus.COMPLETED,
                "COMPLETED": PaymentStatus.COMPLETED,
                "PAID": PaymentStatus.COMPLETED,
                "EXPIRED": PaymentStatus.EXPIRED,
                "FAILED": PaymentStatus.FAILED,
                "CANCELLED": PaymentStatus.FAILED,
            }
            
            return status_map.get(status, PaymentStatus.PENDING)
            
        except Exception as e:
            logger.error(f"Platega check_payment error: {e}")
            return PaymentStatus.PENDING
    
    async def handle_webhook(
        self,
        data: dict,
        headers: dict = None
    ) -> WebhookResult:
        """
        Handle Platega webhook.
        
        Platega sends webhooks when payment status changes.
        Headers contain X-MerchantId and X-Secret for verification.
        
        Args:
            data: Webhook payload
            headers: HTTP headers
            
        Returns:
            WebhookResult
        """
        try:
            # Verify merchant ID
            if headers:
                merchant_id = headers.get("X-MerchantId", "")
                if merchant_id and merchant_id != self.merchant_id:
                    return WebhookResult(
                        success=False,
                        error="Invalid merchant ID"
                    )
            
            # Parse webhook data
            transaction_id = data.get("id")
            amount = data.get("amount")
            currency = data.get("currency", "RUB")
            status = data.get("status", "").upper()
            
            # Extract our payload (payment_uuid:user_id)
            # Note: Platega doesn't return payload in webhook, 
            # we need to look it up by transaction_id
            
            if status == "CONFIRMED" or status == "COMPLETED" or status == "PAID":
                payment_status = PaymentStatus.COMPLETED
            elif status == "EXPIRED":
                payment_status = PaymentStatus.EXPIRED
            elif status == "FAILED" or status == "CANCELLED":
                payment_status = PaymentStatus.FAILED
            else:
                payment_status = PaymentStatus.PENDING
            
            logger.info(f"Platega webhook: transaction {transaction_id} -> {status}")
            
            return WebhookResult(
                success=True,
                payment_uuid=None,  # Will be looked up by provider_payment_id
                status=payment_status,
                provider_payment_id=transaction_id,
                amount=Decimal(str(amount)) if amount else None,
                currency=currency
            )
            
        except Exception as e:
            logger.error(f"Platega webhook error: {e}")
            return WebhookResult(
                success=False,
                error=str(e)
            )
    
    async def get_rates(self, payment_method: int = None) -> dict:
        """
        Get current exchange rates.
        
        Args:
            payment_method: Payment method ID (optional)
            
        Returns:
            Rates dictionary
        """
        try:
            endpoint = "rates"
            if payment_method:
                endpoint = f"rates/{payment_method}"
            
            result = await self._request("GET", endpoint)
            return result
            
        except Exception as e:
            logger.error(f"Platega get_rates error: {e}")
            return {}


# Create default instance (will be configured later)
platega_provider = PlategalProvider()
