"""
Service Registry - Manages installed services
"""
from typing import Dict, Optional, List
from pathlib import Path
import importlib
import sys

from loguru import logger

from core.config import config
from core.database import get_db
from .base_service import BaseService
from .core_api import CoreAPI


class ServiceRegistry:
    """Service registry singleton"""
    
    _instance = None
    _services: Dict[str, BaseService] = {}
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def init(self):
        """Initialize registry and load services"""
        if self._initialized:
            return
        
        await self._load_services_from_db()
        self._initialized = True
        logger.info(f"Service registry initialized with {len(self._services)} services")
    
    async def _load_services_from_db(self):
        """Load active services from database"""
        from core.database.models import Service
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Service).where(Service.status == "active")
            )
            services = result.scalars().all()
            
            for service_record in services:
                try:
                    await self._load_service(service_record)
                except Exception as e:
                    logger.error(f"Failed to load service {service_record.id}: {e}")
                    # Update service status to error
                    service_record.status = "error"
                    service_record.last_error = str(e)
                    service_record.error_count = (service_record.error_count or 0) + 1
                    await session.commit()
    
    async def _load_service(self, service_record):
        """Load single service"""
        service_id = service_record.id
        install_path = service_record.install_path
        
        if not install_path:
            install_path = str(config.SERVICES_DIR / service_id)
        
        # Add to path if needed
        if install_path not in sys.path:
            sys.path.insert(0, str(Path(install_path).parent))
        
        # Import service module
        try:
            module_name = f"services.{service_id}.service"
            if module_name in sys.modules:
                # Reload if already loaded
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
        except ImportError as e:
            logger.error(f"Cannot import service {service_id}: {e}")
            raise
        
        # Find service class
        service_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, BaseService) and 
                attr is not BaseService):
                service_class = attr
                break
        
        if not service_class:
            raise ValueError(f"No BaseService subclass found in {module_name}")
        
        # Create instance
        core_api = CoreAPI(service_id)
        service_instance = service_class(core_api)
        
        self._services[service_id] = service_instance
        logger.info(f"Service loaded: {service_id} v{service_instance.info.version}")
    
    def get(self, service_id: str) -> Optional[BaseService]:
        """Get service by ID"""
        return self._services.get(service_id)
    
    def get_all(self) -> List[BaseService]:
        """Get all loaded services"""
        return list(self._services.values())
    
    def get_active(self) -> List[BaseService]:
        """Get all active services"""
        return [s for s in self._services.values()]
    
    async def register(self, service: BaseService) -> bool:
        """
        Register new service.
        
        Args:
            service: Service instance
        
        Returns:
            True if successful
        """
        from core.database.models import Service
        
        service_id = service.info.id
        
        if service_id in self._services:
            logger.warning(f"Service {service_id} already registered")
            return False
        
        async with get_db() as session:
            # Check if exists in DB
            from sqlalchemy import select
            result = await session.execute(
                select(Service).where(Service.id == service_id)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.warning(f"Service {service_id} already in database")
                return False
            
            # Create record
            service_record = Service(
                id=service_id,
                name=service.info.name,
                description=service.info.description,
                version=service.info.version,
                author=service.info.author,
                icon=service.info.icon,
                status="active",
                features=service.features,
                permissions=service.permissions
            )
            session.add(service_record)
        
        # Install service
        try:
            success = await service.install()
            if not success:
                raise Exception("Service install() returned False")
        except Exception as e:
            logger.error(f"Failed to install service {service_id}: {e}")
            # Remove from DB
            async with get_db() as session:
                from sqlalchemy import delete
                await session.execute(
                    delete(Service).where(Service.id == service_id)
                )
            return False
        
        self._services[service_id] = service
        logger.info(f"Service registered: {service_id}")
        return True
    
    async def unregister(self, service_id: str) -> bool:
        """
        Unregister service.
        
        Args:
            service_id: Service ID
        
        Returns:
            True if successful
        """
        from core.database.models import Service
        
        service = self._services.get(service_id)
        if not service:
            logger.warning(f"Service {service_id} not found")
            return False
        
        # Uninstall service
        try:
            success = await service.uninstall()
            if not success:
                raise Exception("Service uninstall() returned False")
        except Exception as e:
            logger.error(f"Failed to uninstall service {service_id}: {e}")
            return False
        
        # Remove from DB
        async with get_db() as session:
            from sqlalchemy import delete
            await session.execute(
                delete(Service).where(Service.id == service_id)
            )
        
        del self._services[service_id]
        logger.info(f"Service unregistered: {service_id}")
        return True
    
    async def enable(self, service_id: str) -> bool:
        """Enable service"""
        from core.database.models import Service
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Service).where(Service.id == service_id)
            )
            service_record = result.scalar_one_or_none()
            
            if not service_record:
                return False
            
            service_record.status = "active"
            
            # Load if not loaded
            if service_id not in self._services:
                await self._load_service(service_record)
        
        return True
    
    async def disable(self, service_id: str) -> bool:
        """Disable service"""
        from core.database.models import Service
        
        async with get_db() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Service).where(Service.id == service_id)
            )
            service_record = result.scalar_one_or_none()
            
            if not service_record:
                return False
            
            service_record.status = "disabled"
        
        # Remove from loaded
        if service_id in self._services:
            del self._services[service_id]
        
        return True


# Global instance
service_registry = ServiceRegistry()
