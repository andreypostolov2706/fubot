"""
Payment Provider Manager

Manages payment providers and routes payments to appropriate provider.
"""
from typing import Dict, Optional, List
from loguru import logger

from core.config import config
from .base import BasePaymentProvider
from .cryptobot import CryptoBotProvider


class ProviderManager:
    """
    Manages payment providers.
    
    Handles provider initialization, configuration, and routing.
    """
    
    def __init__(self):
        self._providers: Dict[str, BasePaymentProvider] = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize all configured providers"""
        if self._initialized:
            return
        
        # Initialize CryptoBot
        if config.CRYPTOBOT_API_TOKEN:
            cryptobot = CryptoBotProvider({
                "api_token": config.CRYPTOBOT_API_TOKEN,
                "testnet": config.CRYPTOBOT_TESTNET
            })
            is_valid, error = cryptobot.validate_config()
            if is_valid:
                self._providers["cryptobot"] = cryptobot
                logger.info("CryptoBot provider initialized")
            else:
                logger.warning(f"CryptoBot config invalid: {error}")
        
        # TODO: Add other providers here
        # if config.YOOKASSA_SHOP_ID:
        #     yookassa = YooKassaProvider({...})
        #     self._providers["yookassa"] = yookassa
        
        self._initialized = True
        logger.info(f"Provider manager initialized with {len(self._providers)} providers")
    
    def get_provider(self, provider_id: str) -> Optional[BasePaymentProvider]:
        """
        Get provider by ID.
        
        Args:
            provider_id: Provider ID (cryptobot, yookassa, etc.)
            
        Returns:
            Provider instance or None
        """
        if not self._initialized:
            self.initialize()
        
        return self._providers.get(provider_id)
    
    def get_available_providers(self) -> List[BasePaymentProvider]:
        """
        Get list of available (configured) providers.
        
        Returns:
            List of provider instances
        """
        if not self._initialized:
            self.initialize()
        
        return list(self._providers.values())
    
    def get_provider_ids(self) -> List[str]:
        """
        Get list of available provider IDs.
        
        Returns:
            List of provider IDs
        """
        if not self._initialized:
            self.initialize()
        
        return list(self._providers.keys())
    
    def is_provider_available(self, provider_id: str) -> bool:
        """Check if provider is available"""
        return self.get_provider(provider_id) is not None
    
    def register_provider(self, provider: BasePaymentProvider):
        """
        Register a provider manually.
        
        Args:
            provider: Provider instance
        """
        is_valid, error = provider.validate_config()
        if not is_valid:
            raise ValueError(f"Invalid provider config: {error}")
        
        self._providers[provider.id] = provider
        logger.info(f"Provider {provider.id} registered")


# Global instance
provider_manager = ProviderManager()
