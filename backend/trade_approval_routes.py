"""
Trade Approval API Routes for Phase 5: Trade Ideas Workflow

Provides endpoints to approve, reject, and modify AI-generated trade ideas.
Updates trade idea JSON files with approval status and manual overrides.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trade-approval", tags=["trade-approval"])

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"
TRADE_IDEAS_DIR = DATA_DIR / "trade_ideas"


# ==================== REQUEST/RESPONSE MODELS ====================

class TradeIdeaDetail(BaseModel):
    """Detailed trade idea with approval fields."""
    id: str
    timestamp: str
    symbol: str
    timeframe: str
    confidence: int
    action: str
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    volume: Optional[float] = None
    rr_ratio: Optional[float] = None
    status: str  # "pending_approval", "approved", "rejected", "executed", "cancelled"
    source: Optional[str] = None
    notes: Optional[str] = None
    emnr_flags: Optional[Dict[str, bool]] = None
    indicators: Optional[Dict[str, Any]] = None
    execution_plan: Optional[Dict[str, Any]] = None
    
    # Approval fields
    approval_status: Optional[str] = None  # "pending", "approved", "rejected"
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Manual overrides
    manual_overrides: Optional[Dict[str, Any]] = None


class ApprovalRequest(BaseModel):
    """Request to approve a trade idea."""
    trade_idea_id: str = Field(..., description="Trade idea ID to approve")
    approved_by: str = Field(default="user", description="Username of approver")
    manual_overrides: Optional[Dict[str, Any]] = Field(None, description="Manual parameter overrides")


class RejectionRequest(BaseModel):
    """Request to reject a trade idea."""
    trade_idea_id: str = Field(..., description="Trade idea ID to reject")
    rejected_by: str = Field(default="user", description="Username of rejector")
    rejection_reason: str = Field(..., description="Reason for rejection")


class ModifyRequest(BaseModel):
    """Request to modify trade idea parameters."""
    trade_idea_id: str = Field(..., description="Trade idea ID to modify")
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    volume: Optional[float] = None
    notes: Optional[str] = None


class TradeIdeasListResponse(BaseModel):
    """Response containing list of trade ideas."""
    items: List[TradeIdeaDetail]
    total: int
    pending_count: int
    approved_count: int
    rejected_count: int


class ApprovalResponse(BaseModel):
    """Response after approval/rejection action."""
    success: bool
    message: str
    trade_idea: TradeIdeaDetail


# ==================== HELPER FUNCTIONS ====================

def _get_trade_idea_path(trade_idea_id: str) -> Optional[Path]:
    """Find the file path for a trade idea by ID."""
    if not TRADE_IDEAS_DIR.exists():
        return None
    
    for file_path in TRADE_IDEAS_DIR.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if data.get('id') == trade_idea_id:
                    return file_path
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            continue
    
    return None


def _load_trade_idea(trade_idea_id: str) -> Optional[Dict[str, Any]]:
    """Load a trade idea by ID."""
    file_path = _get_trade_idea_path(trade_idea_id)
    if not file_path:
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading trade idea {trade_idea_id}: {e}")
        return None


def _save_trade_idea(trade_idea_id: str, data: Dict[str, Any]) -> bool:
    """Save a trade idea to file."""
    file_path = _get_trade_idea_path(trade_idea_id)
    if not file_path:
        logger.error(f"Trade idea file not found: {trade_idea_id}")
        return False
    
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved trade idea {trade_idea_id} to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving trade idea {trade_idea_id}: {e}")
        return False


def _load_all_trade_ideas() -> List[Dict[str, Any]]:
    """Load all trade ideas from files."""
    trade_ideas = []
    
    if not TRADE_IDEAS_DIR.exists():
        logger.warning(f"Trade ideas directory not found: {TRADE_IDEAS_DIR}")
        return trade_ideas
    
    for file_path in TRADE_IDEAS_DIR.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                trade_ideas.append(data)
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            continue
    
    return trade_ideas


# ==================== API ENDPOINTS ====================

@router.get("/", response_model=TradeIdeasListResponse)
async def get_trade_ideas(
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    approval_status: Optional[str] = None
):
    """
    Get all trade ideas with optional filtering.
    
    Query Parameters:
    - status: Filter by status (pending_approval, approved, rejected, executed, cancelled)
    - symbol: Filter by symbol (e.g., EURUSD)
    - approval_status: Filter by approval status (pending, approved, rejected)
    """
    try:
        trade_ideas = _load_all_trade_ideas()
        
        # Apply filters
        if status:
            trade_ideas = [ti for ti in trade_ideas if ti.get('status') == status]
        
        if symbol:
            trade_ideas = [ti for ti in trade_ideas if ti.get('symbol') == symbol.upper()]
        
        if approval_status:
            trade_ideas = [ti for ti in trade_ideas if ti.get('approval_status') == approval_status]
        
        # Count by approval status
        pending_count = sum(1 for ti in trade_ideas if ti.get('approval_status') in [None, 'pending'])
        approved_count = sum(1 for ti in trade_ideas if ti.get('approval_status') == 'approved')
        rejected_count = sum(1 for ti in trade_ideas if ti.get('approval_status') == 'rejected')
        
        # Convert to response model
        items = [TradeIdeaDetail(**ti) for ti in trade_ideas]
        
        return TradeIdeasListResponse(
            items=items,
            total=len(items),
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count
        )
    
    except Exception as e:
        logger.error(f"Error getting trade ideas: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving trade ideas: {str(e)}")


@router.get("/{trade_idea_id}", response_model=TradeIdeaDetail)
async def get_trade_idea(trade_idea_id: str):
    """Get a specific trade idea by ID."""
    trade_idea = _load_trade_idea(trade_idea_id)
    
    if not trade_idea:
        raise HTTPException(status_code=404, detail=f"Trade idea not found: {trade_idea_id}")
    
    return TradeIdeaDetail(**trade_idea)


@router.post("/approve", response_model=ApprovalResponse)
async def approve_trade_idea(request: ApprovalRequest = Body(...)):
    """
    Approve a trade idea.
    
    Updates the trade idea file with:
    - approval_status: "approved"
    - approved_by: username
    - approved_at: timestamp
    - manual_overrides: any parameter overrides
    - status: "approved" (if not already executed)
    """
    try:
        # Load trade idea
        trade_idea = _load_trade_idea(request.trade_idea_id)
        if not trade_idea:
            raise HTTPException(status_code=404, detail=f"Trade idea not found: {request.trade_idea_id}")
        
        # Update approval fields
        trade_idea['approval_status'] = 'approved'
        trade_idea['approved_by'] = request.approved_by
        trade_idea['approved_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Apply manual overrides if provided
        if request.manual_overrides:
            trade_idea['manual_overrides'] = request.manual_overrides
            
            # Apply overrides to main fields
            for key, value in request.manual_overrides.items():
                if key in ['entry_price', 'stop_loss', 'take_profit', 'volume']:
                    trade_idea[key] = value
        
        # Update status if still pending
        if trade_idea.get('status') == 'pending_approval':
            trade_idea['status'] = 'approved'
        
        # Save updated trade idea
        if not _save_trade_idea(request.trade_idea_id, trade_idea):
            raise HTTPException(status_code=500, detail="Failed to save trade idea")
        
        logger.info(f"Trade idea {request.trade_idea_id} approved by {request.approved_by}")
        
        return ApprovalResponse(
            success=True,
            message=f"Trade idea {request.trade_idea_id} approved successfully",
            trade_idea=TradeIdeaDetail(**trade_idea)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving trade idea: {e}")
        raise HTTPException(status_code=500, detail=f"Error approving trade idea: {str(e)}")


@router.post("/reject", response_model=ApprovalResponse)
async def reject_trade_idea(request: RejectionRequest = Body(...)):
    """
    Reject a trade idea.
    
    Updates the trade idea file with:
    - approval_status: "rejected"
    - rejected_by: username
    - rejected_at: timestamp
    - rejection_reason: reason for rejection
    - status: "rejected"
    """
    try:
        # Load trade idea
        trade_idea = _load_trade_idea(request.trade_idea_id)
        if not trade_idea:
            raise HTTPException(status_code=404, detail=f"Trade idea not found: {request.trade_idea_id}")
        
        # Update rejection fields
        trade_idea['approval_status'] = 'rejected'
        trade_idea['rejected_by'] = request.rejected_by
        trade_idea['rejected_at'] = datetime.utcnow().isoformat() + 'Z'
        trade_idea['rejection_reason'] = request.rejection_reason
        trade_idea['status'] = 'rejected'
        
        # Save updated trade idea
        if not _save_trade_idea(request.trade_idea_id, trade_idea):
            raise HTTPException(status_code=500, detail="Failed to save trade idea")
        
        logger.info(f"Trade idea {request.trade_idea_id} rejected by {request.rejected_by}: {request.rejection_reason}")
        
        return ApprovalResponse(
            success=True,
            message=f"Trade idea {request.trade_idea_id} rejected",
            trade_idea=TradeIdeaDetail(**trade_idea)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting trade idea: {e}")
        raise HTTPException(status_code=500, detail=f"Error rejecting trade idea: {str(e)}")


@router.patch("/modify", response_model=ApprovalResponse)
async def modify_trade_idea(request: ModifyRequest = Body(...)):
    """
    Modify trade idea parameters (manual override).

    Allows manual adjustment of:
    - entry_price
    - stop_loss
    - take_profit
    - volume
    - notes

    Updates are stored in manual_overrides field and applied to main fields.
    """
    try:
        # Load trade idea
        trade_idea = _load_trade_idea(request.trade_idea_id)
        if not trade_idea:
            raise HTTPException(status_code=404, detail=f"Trade idea not found: {request.trade_idea_id}")

        # Initialize manual_overrides if not exists
        if 'manual_overrides' not in trade_idea:
            trade_idea['manual_overrides'] = {}

        # Track what was modified
        modifications = {}

        # Apply modifications
        if request.entry_price is not None:
            trade_idea['entry_price'] = request.entry_price
            modifications['entry_price'] = request.entry_price

        if request.stop_loss is not None:
            trade_idea['stop_loss'] = request.stop_loss
            modifications['stop_loss'] = request.stop_loss

        if request.take_profit is not None:
            trade_idea['take_profit'] = request.take_profit
            modifications['take_profit'] = request.take_profit

        if request.volume is not None:
            trade_idea['volume'] = request.volume
            modifications['volume'] = request.volume

        if request.notes is not None:
            trade_idea['notes'] = request.notes
            modifications['notes'] = request.notes

        # Update manual_overrides
        trade_idea['manual_overrides'].update(modifications)
        trade_idea['manual_overrides']['modified_at'] = datetime.utcnow().isoformat() + 'Z'

        # Recalculate R:R ratio if prices were modified
        if 'entry_price' in modifications or 'stop_loss' in modifications or 'take_profit' in modifications:
            entry = trade_idea.get('entry_price')
            sl = trade_idea.get('stop_loss')
            tp = trade_idea.get('take_profit')

            if entry and sl and tp:
                risk = abs(entry - sl)
                reward = abs(tp - entry)
                if risk > 0:
                    trade_idea['rr_ratio'] = round(reward / risk, 2)

        # Save updated trade idea
        if not _save_trade_idea(request.trade_idea_id, trade_idea):
            raise HTTPException(status_code=500, detail="Failed to save trade idea")

        logger.info(f"Trade idea {request.trade_idea_id} modified: {modifications}")

        return ApprovalResponse(
            success=True,
            message=f"Trade idea {request.trade_idea_id} modified successfully",
            trade_idea=TradeIdeaDetail(**trade_idea)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error modifying trade idea: {e}")
        raise HTTPException(status_code=500, detail=f"Error modifying trade idea: {str(e)}")


@router.delete("/{trade_idea_id}")
async def cancel_trade_idea(trade_idea_id: str):
    """
    Cancel a trade idea (mark as cancelled, don't delete file).

    Updates status to "cancelled" but keeps the file for audit trail.
    """
    try:
        # Load trade idea
        trade_idea = _load_trade_idea(trade_idea_id)
        if not trade_idea:
            raise HTTPException(status_code=404, detail=f"Trade idea not found: {trade_idea_id}")

        # Update status
        trade_idea['status'] = 'cancelled'
        trade_idea['cancelled_at'] = datetime.utcnow().isoformat() + 'Z'

        # Save updated trade idea
        if not _save_trade_idea(trade_idea_id, trade_idea):
            raise HTTPException(status_code=500, detail="Failed to save trade idea")

        logger.info(f"Trade idea {trade_idea_id} cancelled")

        return {
            "success": True,
            "message": f"Trade idea {trade_idea_id} cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling trade idea: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling trade idea: {str(e)}")

