"""
Database Schemas for Maso Project

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name (e.g., Order -> "order").

These schemas are read by the Flames database viewer and can also be used for
request validation in the API.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class Machine(BaseModel):
    """Machines available on the shop floor"""
    name: str = Field(..., description="Machine name or number")
    group: Optional[str] = Field(None, description="Group/line this machine belongs to")
    type: Optional[str] = Field(None, description="Machine type (e.g., Laser, Press Brake, Punch)")
    status: Literal["idle", "running", "maintenance", "offline"] = Field(
        "idle", description="Current machine status"
    )


class OrderItem(BaseModel):
    sku: str = Field(..., description="Part number or SKU")
    description: Optional[str] = Field(None, description="Part description")
    quantity: int = Field(..., ge=1, description="Quantity required")
    unit_price: float = Field(0, ge=0, description="Unit price for invoicing")


class Order(BaseModel):
    """Production order raised by managers"""
    customer: str = Field(..., description="Customer name")
    po_number: Optional[str] = Field(None, description="Customer purchase order number")
    items: List[OrderItem] = Field(default_factory=list, description="List of items in the order")
    priority: Literal["low", "normal", "high", "urgent"] = Field("normal")
    due_date: Optional[datetime] = Field(None, description="Requested delivery date")
    notes: Optional[str] = Field(None, description="Additional instructions")
    status: Literal["draft", "scheduled", "in_progress", "completed", "invoiced", "cancelled"] = Field(
        "draft", description="Overall order status"
    )


class Task(BaseModel):
    """Executable task linked to an order and optionally a machine"""
    order_id: str = Field(..., description="Linked order id")
    name: str = Field(..., description="Task name, e.g., Laser Cut, Bend, Weld")
    machine_id: Optional[str] = Field(None, description="Assigned machine id")
    group: Optional[str] = Field(None, description="Assigned machine group/line")
    assignee: Optional[str] = Field(None, description="Employee name or id")
    status: Literal["queued", "assigned", "in_progress", "paused", "done", "rejected"] = Field(
        "queued", description="Task progress state"
    )
    estimated_minutes: Optional[int] = Field(None, ge=0)
    actual_minutes: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class Attachment(BaseModel):
    """Attachment metadata for drawings, DXF, PDFs. We store URL/filename only."""
    order_id: str = Field(..., description="Linked order id")
    filename: str = Field(..., description="Original filename")
    url: Optional[str] = Field(None, description="Public URL if uploaded to external storage")
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = Field(None, ge=0)


class InvoiceItem(BaseModel):
    description: str
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)


class Invoice(BaseModel):
    order_id: str = Field(..., description="Order id this invoice is for")
    items: List[InvoiceItem] = Field(default_factory=list)
    subtotal: float = Field(0, ge=0)
    tax_rate: float = Field(0.0, ge=0, le=1.0, description="Fraction, e.g., 0.18 for 18%")
    total: float = Field(0, ge=0)
    notes: Optional[str] = None
