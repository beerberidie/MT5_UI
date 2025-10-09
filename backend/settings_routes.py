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


# ==================== DEPENDENCIES ====================

def get_mt5_client() -> MT5Client:
    """Get MT5 client instance."""
    return MT5Client()


# ==================== HELPER FUNCTIONS ====================

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

