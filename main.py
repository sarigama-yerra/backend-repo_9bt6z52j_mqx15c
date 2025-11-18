import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Order, Task, Attachment, Invoice

app = FastAPI(title="Maso Project API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Maso Project Backend Running"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Ensure env flags are included
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Utility to safely turn string id into ObjectId

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


# ========== Orders ==========

@app.post("/api/orders")
async def create_order(order: Order):
    oid = create_document("order", order)
    return {"id": oid}


@app.get("/api/orders")
async def list_orders(limit: int = 50):
    docs = get_documents("order", limit=limit)
    # Convert ObjectId for JSON
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# ========== Tasks ==========

@app.post("/api/tasks")
async def create_task(task: Task):
    oid = create_document("task", task)
    return {"id": oid}


@app.get("/api/tasks")
async def list_tasks(order_id: Optional[str] = None, status: Optional[str] = None, limit: int = 100):
    filter_dict = {}
    if order_id:
        filter_dict["order_id"] = order_id
    if status:
        filter_dict["status"] = status
    docs = get_documents("task", filter_dict, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


@app.patch("/api/tasks/{task_id}/status")
async def update_task_status(task_id: str, payload: StatusUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    _id = to_object_id(task_id)
    update = {"$set": {"status": payload.status, "updated_at": __import__('datetime').datetime.utcnow()}}
    if payload.notes:
        update["$set"]["notes"] = payload.notes
    result = db["task"].update_one({"_id": _id}, update)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


# ========== Attachments ==========

@app.post("/api/attachments")
async def create_attachment(attachment: Attachment):
    oid = create_document("attachment", attachment)
    return {"id": oid}


@app.get("/api/attachments")
async def list_attachments(order_id: Optional[str] = None, limit: int = 50):
    filter_dict = {"order_id": order_id} if order_id else {}
    docs = get_documents("attachment", filter_dict, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# ========== Invoices ==========

@app.post("/api/invoices")
async def create_invoice(invoice: Invoice):
    # Compute totals if needed
    subtotal = sum(i.quantity * i.unit_price for i in invoice.items)
    total = subtotal * (1 + invoice.tax_rate)
    payload = invoice.model_dump()
    payload["subtotal"] = round(subtotal, 2)
    payload["total"] = round(total, 2)
    oid = create_document("invoice", payload)
    return {"id": oid, "subtotal": payload["subtotal"], "total": payload["total"]}


@app.get("/api/invoices")
async def list_invoices(order_id: Optional[str] = None, limit: int = 50):
    filter_dict = {"order_id": order_id} if order_id else {}
    docs = get_documents("invoice", filter_dict, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
