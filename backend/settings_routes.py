"""
Settings API Routes for MT5_UI

Provides endpoints for managing:
- MT5 Accounts
- API Integrations
- Appearance Settings
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.storage.storage_factory import get_storage
from backend.services.encryption_service import get_encryption_service
from backend.mt5_client import MT5Client

router = APIRouter(prefix="/api/settings", tags=["settings"])

# ==================== MODELS ====================

class AccountCreate(BaseModel):
    """Model for creating a new MT5 account."""
    name: str = Field(..., min_length=1, max_length=100, description="Account name")
    login: int = Field(..., gt=0, description="MT5 login number")
    password: str = Field(..., min_length=1, description="MT5 password")
    server: str = Field(..., min_length=1, max_length=100, description="MT5 server")


class AccountUpdate(BaseModel):
    """Model for updating an existing MT5 account."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    login: Optional[int] = Field(None, gt=0)
    password: Optional[str] = Field(None, min_length=1)
    server: Optional[str] = Field(None, min_length=1, max_length=100)


class AccountResponse(BaseModel):
    """Model for account response (password masked)."""
    id: str
    name: str
    login: int
    server: str
    is_active: bool
    status: str = "disconnected"  # connected, disconnected, error
    created_at: str
    updated_at: Optional[str] = None


class AccountTestResponse(BaseModel):
    """Model for account connection test response."""
    success: bool
    connected: bool
    error: Optional[str] = None
    account_info: Optional[Dict[str, Any]] = None


class APIIntegrationCreate(BaseModel):
    """Model for creating a new API integration."""
    name: str = Field(..., min_length=1, max_length=100, description="Integration name")
    type: str = Field(..., description="Integration type: economic_calendar, news, custom")
    api_key: str = Field(..., min_length=1, description="API key")
    base_url: Optional[str] = Field(None, description="Base URL for API")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


class APIIntegrationUpdate(BaseModel):
    """Model for updating an existing API integration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = None
    api_key: Optional[str] = Field(None, min_length=1)
    base_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class APIIntegrationResponse(BaseModel):
    """Model for API integration response (API key masked)."""
    id: str
    name: str
    type: str
    base_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: str = "inactive"  # active, inactive, error
    last_tested: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    api_key_masked: str = "****"


class APIIntegrationTestResponse(BaseModel):
    """Model for API integration test response."""
    success: bool
    connected: bool
    error: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


class AppearanceSettings(BaseModel):
    """Model for appearance settings."""
    density: str = Field(default="normal", description="UI density: compact, normal, comfortable")
    theme: str = Field(default="dark", description="Theme: dark, light")
    font_size: int = Field(default=14, ge=12, le=18, description="Font size in pixels")
    accent_color: str = Field(default="#3b82f6", description="Accent color (hex)")
    show_animations: bool = Field(default=True, description="Show animations")


# ==================== DEPENDENCIES ====================

def get_mt5_client() -> MT5Client:
    """Get MT5 client instance."""
    return MT5Client()


# ==================== HELPER FUNCTIONS ====================

def _mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """
    Mask API key for display.

    Args:
        api_key: API key to mask
        visible_chars: Number of characters to show at the end

    Returns:
        Masked API key (e.g., "****abcd")
    """
    if not api_key or len(api_key) <= visible_chars:
        return "****"
    return "****" + api_key[-visible_chars:]


def _mask_account_password(account: Dict[str, Any]) -> AccountResponse:
    """
    Convert account dict to response model with masked password.
    
    Args:
        account: Account dictionary from storage
        
    Returns:
        AccountResponse with password removed
    """
    # Remove password from response
    account_copy = account.copy()
    account_copy.pop("password", None)
    account_copy.pop("password_encrypted", None)
    
    # Determine status (will be enhanced with actual MT5 connection check)
    status = "disconnected"
    if account.get("is_active"):
        status = "connected"  # Simplified for now
    
    return AccountResponse(
        id=account_copy.get("id", ""),
        name=account_copy.get("name", ""),
        login=account_copy.get("login", 0),
        server=account_copy.get("server", ""),
        is_active=account_copy.get("is_active", False),
        status=status,
        created_at=account_copy.get("created_at", datetime.utcnow().isoformat()),
        updated_at=account_copy.get("updated_at")
    )


def _mask_integration_api_key(integration: Dict[str, Any]) -> APIIntegrationResponse:
    """
    Convert integration dict to response model with masked API key.

    Args:
        integration: Integration dictionary from storage

    Returns:
        APIIntegrationResponse with API key masked
    """
    # Remove API key from response
    integration_copy = integration.copy()
    api_key = integration_copy.pop("api_key", "")
    integration_copy.pop("api_key_encrypted", None)

    return APIIntegrationResponse(
        id=integration_copy.get("id", ""),
        name=integration_copy.get("name", ""),
        type=integration_copy.get("type", "custom"),
        base_url=integration_copy.get("base_url"),
        config=integration_copy.get("config"),
        status=integration_copy.get("status", "inactive"),
        last_tested=integration_copy.get("last_tested"),
        created_at=integration_copy.get("created_at", datetime.utcnow().isoformat()),
        updated_at=integration_copy.get("updated_at"),
        api_key_masked=_mask_api_key(api_key) if api_key else "****"
    )


async def _test_api_integration(integration_type: str, api_key: str, base_url: Optional[str] = None) -> APIIntegrationTestResponse:
    """
    Test API integration connection.

    Args:
        integration_type: Type of integration (economic_calendar, news, custom)
        api_key: API key
        base_url: Base URL for API

    Returns:
        APIIntegrationTestResponse with connection status
    """
    try:
        import requests

        # Test based on integration type
        if integration_type == "economic_calendar":
            # Test Econdb API
            url = base_url or "https://www.econdb.com/api"
            response = requests.get(
                f"{url}/series",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )

            if response.status_code == 200:
                return APIIntegrationTestResponse(
                    success=True,
                    connected=True,
                    response_data={"status": "connected", "api": "econdb"}
                )
            else:
                return APIIntegrationTestResponse(
                    success=False,
                    connected=False,
                    error=f"API returned status {response.status_code}"
                )

        elif integration_type == "news":
            # Test NewsAPI or Finnhub
            if base_url and "newsapi" in base_url.lower():
                # NewsAPI
                url = base_url or "https://newsapi.org/v2"
                response = requests.get(
                    f"{url}/top-headlines",
                    params={"apiKey": api_key, "category": "business"},
                    timeout=10
                )
            else:
                # Finnhub
                url = base_url or "https://finnhub.io/api/v1"
                response = requests.get(
                    f"{url}/news",
                    params={"token": api_key, "category": "forex"},
                    timeout=10
                )

            if response.status_code == 200:
                return APIIntegrationTestResponse(
                    success=True,
                    connected=True,
                    response_data={"status": "connected", "articles_count": len(response.json())}
                )
            else:
                return APIIntegrationTestResponse(
                    success=False,
                    connected=False,
                    error=f"API returned status {response.status_code}"
                )

        else:
            # Custom integration - just test if URL is reachable
            if not base_url:
                return APIIntegrationTestResponse(
                    success=False,
                    connected=False,
                    error="Base URL required for custom integrations"
                )

            response = requests.get(
                base_url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )

            if response.status_code < 400:
                return APIIntegrationTestResponse(
                    success=True,
                    connected=True,
                    response_data={"status": "connected", "status_code": response.status_code}
                )
            else:
                return APIIntegrationTestResponse(
                    success=False,
                    connected=False,
                    error=f"API returned status {response.status_code}"
                )

    except requests.exceptions.Timeout:
        return APIIntegrationTestResponse(
            success=False,
            connected=False,
            error="Connection timeout"
        )
    except requests.exceptions.ConnectionError:
        return APIIntegrationTestResponse(
            success=False,
            connected=False,
            error="Connection failed"
        )
    except Exception as e:
        return APIIntegrationTestResponse(
            success=False,
            connected=False,
            error=f"Test failed: {str(e)}"
        )


async def _test_mt5_connection(login: int, password: str, server: str) -> AccountTestResponse:
    """
    Test MT5 connection with provided credentials.
    
    Args:
        login: MT5 login number
        password: MT5 password
        server: MT5 server
        
    Returns:
        AccountTestResponse with connection status
    """
    try:
        import MetaTrader5 as mt5
        
        # Initialize MT5
        if not mt5.initialize():
            return AccountTestResponse(
                success=False,
                connected=False,
                error="Failed to initialize MT5 terminal"
            )
        
        # Try to login
        authorized = mt5.login(login=login, password=password, server=server)
        
        if not authorized:
            error_code = mt5.last_error()
            mt5.shutdown()
            return AccountTestResponse(
                success=False,
                connected=False,
                error=f"Login failed: {error_code}"
            )
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            mt5.shutdown()
            return AccountTestResponse(
                success=False,
                connected=False,
                error="Failed to get account info"
            )
        
        # Convert account info to dict
        info_dict = {
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin": account_info.margin,
            "margin_free": account_info.margin_free,
            "margin_level": account_info.margin_level,
            "leverage": account_info.leverage,
            "currency": account_info.currency,
            "name": account_info.name,
            "server": account_info.server,
            "login": account_info.login
        }
        
        mt5.shutdown()
        
        return AccountTestResponse(
            success=True,
            connected=True,
            account_info=info_dict
        )
        
    except Exception as e:
        return AccountTestResponse(
            success=False,
            connected=False,
            error=f"Connection test failed: {str(e)}"
        )


# ==================== ACCOUNT ENDPOINTS ====================

@router.get("/accounts", response_model=Dict[str, Any])
async def get_accounts():
    """
    Get all MT5 accounts.
    
    Returns:
        Dictionary with accounts list and active account ID
    """
    storage = get_storage()
    
    try:
        accounts = await storage.get_accounts()
        active_account = await storage.get_active_account()
        
        # Mask passwords in response
        masked_accounts = [_mask_account_password(acc) for acc in accounts]
        
        return {
            "accounts": masked_accounts,
            "active_account_id": active_account["id"] if active_account else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get accounts: {str(e)}")


@router.post("/accounts", response_model=AccountResponse)
async def create_account(account: AccountCreate):
    """
    Create a new MT5 account.
    
    Args:
        account: Account creation data
        
    Returns:
        Created account (password masked)
    """
    storage = get_storage()
    
    try:
        # Create account (password will be encrypted by storage layer)
        new_account = await storage.add_account({
            "name": account.name,
            "login": account.login,
            "password": account.password,
            "server": account.server
        })
        
        return _mask_account_password(new_account)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(account_id: str, updates: AccountUpdate):
    """
    Update an existing MT5 account.
    
    Args:
        account_id: Account ID
        updates: Fields to update
        
    Returns:
        Updated account (password masked)
    """
    storage = get_storage()
    
    try:
        # Build updates dict (only include provided fields)
        update_dict = {}
        if updates.name is not None:
            update_dict["name"] = updates.name
        if updates.login is not None:
            update_dict["login"] = updates.login
        if updates.password is not None:
            update_dict["password"] = updates.password
        if updates.server is not None:
            update_dict["server"] = updates.server
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_account = await storage.update_account(account_id, update_dict)
        
        if not updated_account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return _mask_account_password(updated_account)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update account: {str(e)}")


@router.delete("/accounts/{account_id}")
async def delete_account(account_id: str):
    """
    Delete an MT5 account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Success status
    """
    storage = get_storage()
    
    try:
        success = await storage.remove_account(account_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return {"success": True, "message": "Account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")


@router.post("/accounts/{account_id}/activate")
async def activate_account(account_id: str):
    """
    Set an account as active (deactivates all others).
    
    Args:
        account_id: Account ID to activate
        
    Returns:
        Success status and updated account
    """
    storage = get_storage()
    
    try:
        success = await storage.set_active_account(account_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Get the activated account
        account = await storage.get_account(account_id)
        
        return {
            "success": True,
            "message": "Account activated successfully",
            "account": _mask_account_password(account)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate account: {str(e)}")


@router.post("/accounts/{account_id}/test", response_model=AccountTestResponse)
async def test_account_connection(account_id: str):
    """
    Test MT5 connection for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        Connection test results
    """
    storage = get_storage()
    
    try:
        # Get account with decrypted password
        account = await storage.get_account(account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Test connection
        result = await _test_mt5_connection(
            login=account["login"],
            password=account["password"],
            server=account["server"]
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test connection: {str(e)}")


# ==================== API INTEGRATION ENDPOINTS ====================

@router.get("/integrations", response_model=Dict[str, Any])
async def get_integrations():
    """
    Get all API integrations.

    Returns:
        Dictionary with integrations list
    """
    storage = get_storage()

    try:
        integrations = await storage.get_api_integrations()

        # Mask API keys in response
        masked_integrations = [_mask_integration_api_key(integ) for integ in integrations]

        return {
            "integrations": masked_integrations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get integrations: {str(e)}")


@router.post("/integrations", response_model=APIIntegrationResponse)
async def create_integration(integration: APIIntegrationCreate):
    """
    Create a new API integration.

    Args:
        integration: Integration creation data

    Returns:
        Created integration (API key masked)
    """
    storage = get_storage()

    try:
        # Validate integration type
        valid_types = ["economic_calendar", "news", "custom"]
        if integration.type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid integration type. Must be one of: {', '.join(valid_types)}"
            )

        # Create integration (API key will be encrypted by storage layer)
        new_integration = await storage.add_api_integration({
            "name": integration.name,
            "type": integration.type,
            "api_key": integration.api_key,
            "base_url": integration.base_url,
            "config": integration.config
        })

        return _mask_integration_api_key(new_integration)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create integration: {str(e)}")


@router.put("/integrations/{integration_id}", response_model=APIIntegrationResponse)
async def update_integration(integration_id: str, updates: APIIntegrationUpdate):
    """
    Update an existing API integration.

    Args:
        integration_id: Integration ID
        updates: Fields to update

    Returns:
        Updated integration (API key masked)
    """
    storage = get_storage()

    try:
        # Build updates dict (only include provided fields)
        update_dict = {}
        if updates.name is not None:
            update_dict["name"] = updates.name
        if updates.type is not None:
            # Validate type
            valid_types = ["economic_calendar", "news", "custom"]
            if updates.type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid integration type. Must be one of: {', '.join(valid_types)}"
                )
            update_dict["type"] = updates.type
        if updates.api_key is not None:
            update_dict["api_key"] = updates.api_key
        if updates.base_url is not None:
            update_dict["base_url"] = updates.base_url
        if updates.config is not None:
            update_dict["config"] = updates.config

        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated_integration = await storage.update_api_integration(integration_id, update_dict)

        if not updated_integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        return _mask_integration_api_key(updated_integration)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update integration: {str(e)}")


@router.delete("/integrations/{integration_id}")
async def delete_integration(integration_id: str):
    """
    Delete an API integration.

    Args:
        integration_id: Integration ID

    Returns:
        Success status
    """
    storage = get_storage()

    try:
        success = await storage.remove_api_integration(integration_id)

        if not success:
            raise HTTPException(status_code=404, detail="Integration not found")

        return {"success": True, "message": "Integration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete integration: {str(e)}")


@router.post("/integrations/{integration_id}/test", response_model=APIIntegrationTestResponse)
async def test_integration_connection(integration_id: str):
    """
    Test API integration connection.

    Args:
        integration_id: Integration ID

    Returns:
        Connection test results
    """
    storage = get_storage()

    try:
        # Get integration with decrypted API key
        integration = await storage.get_api_integration(integration_id)

        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")

        # Test connection
        result = await _test_api_integration(
            integration_type=integration["type"],
            api_key=integration["api_key"],
            base_url=integration.get("base_url")
        )

        # Update last_tested timestamp if successful
        if result.connected:
            await storage.update_api_integration(integration_id, {
                "last_tested": datetime.utcnow().isoformat(),
                "status": "active"
            })
        else:
            await storage.update_api_integration(integration_id, {
                "status": "error"
            })

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test integration: {str(e)}")


# ==================== APPEARANCE ENDPOINTS ====================

@router.get("/appearance", response_model=AppearanceSettings)
async def get_appearance_settings():
    """
    Get appearance settings.

    Returns:
        Current appearance settings
    """
    storage = get_storage()

    try:
        settings = await storage.get_appearance_settings()

        return AppearanceSettings(
            density=settings.get("density", "normal"),
            theme=settings.get("theme", "dark"),
            font_size=settings.get("font_size", 14),
            accent_color=settings.get("accent_color", "#3b82f6"),
            show_animations=settings.get("show_animations", True)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get appearance settings: {str(e)}")


@router.put("/appearance", response_model=AppearanceSettings)
async def update_appearance_settings(settings: AppearanceSettings):
    """
    Update appearance settings.

    Args:
        settings: New appearance settings

    Returns:
        Updated appearance settings
    """
    storage = get_storage()

    try:
        # Validate density
        valid_densities = ["compact", "normal", "comfortable"]
        if settings.density not in valid_densities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid density. Must be one of: {', '.join(valid_densities)}"
            )

        # Validate theme
        valid_themes = ["dark", "light"]
        if settings.theme not in valid_themes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid theme. Must be one of: {', '.join(valid_themes)}"
            )

        # Update settings
        updated_settings = await storage.update_appearance_settings({
            "density": settings.density,
            "theme": settings.theme,
            "font_size": settings.font_size,
            "accent_color": settings.accent_color,
            "show_animations": settings.show_animations
        })

        return AppearanceSettings(
            density=updated_settings.get("density", "normal"),
            theme=updated_settings.get("theme", "dark"),
            font_size=updated_settings.get("font_size", 14),
            accent_color=updated_settings.get("accent_color", "#3b82f6"),
            show_animations=updated_settings.get("show_animations", True)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update appearance settings: {str(e)}")

