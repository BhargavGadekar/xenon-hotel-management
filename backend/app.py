import os
import sys
import time
import random
import json
from pathlib import Path
from typing import Optional, List

# Ensure backend directory is in sys.path regardless of execution directory (Windows / Mac / Linux)
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import get_connection, init_db, calculate_nights

# Initialize database schema and seeds
init_db()

app = FastAPI(
    title="Xenon Hotel & Residences - Lodging Management API",
    description="Luxury Typography Lodging and Stays Operating System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Pydantic Models -----------------

class RoomCreate(BaseModel):
    room_number: str
    room_type: str = "Executive Atelier Suite"
    wing: str = "Wing I · Imperial Pavilion"
    capacity: int = 2
    base_rate: int = 35000
    amenities: List[str] = Field(default_factory=list)

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    room_type: Optional[str] = None
    wing: Optional[str] = None
    capacity: Optional[int] = None
    base_rate: Optional[int] = None
    status: Optional[str] = None
    amenities: Optional[List[str]] = None

class StatusUpdate(BaseModel):
    status: str

class CheckInRequest(BaseModel):
    room_id: int
    guest_name: str
    guest_phone: str = ""
    guest_email: str = ""
    vip_tier: str = "Gold VIP"
    id_proof_type: str = "Passport"
    id_proof_number: str = ""
    adults: int = 1
    children: int = 0
    stay_nights: int = 1
    nightly_rate: Optional[int] = None
    advance_paid: int = 0
    notes: str = ""

class CheckOutRequest(BaseModel):
    stay_id: str
    damage_charges: int = 0
    discount: int = 0
    notes: str = ""

class FolioChargeRequest(BaseModel):
    stay_id: Optional[str] = None
    room_id: Optional[int] = None
    charge_type: str = "room_service"
    description: str
    amount: int

# ----------------- API Endpoints -----------------

@app.get("/api/overview")
def get_overview():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rooms WHERE active = 1")
    rooms = [dict(r) for r in cur.fetchall()]

    total_rooms = len(rooms)
    occupied = len([r for r in rooms if r["status"] == "occupied"])
    vacant = len([r for r in rooms if r["status"] == "vacant"])
    cleaning = len([r for r in rooms if r["status"] == "cleaning"])
    maintenance = len([r for r in rooms if r["status"] == "maintenance"])
    occupancy_rate = round((occupied / total_rooms * 100), 1) if total_rooms > 0 else 0

    cur.execute("SELECT * FROM stays WHERE status = 'checked_in'")
    active_stays = [dict(s) for s in cur.fetchall()]
    active_guests_count = sum(s["adults"] + s["children"] for s in active_stays)

    # Calculate real-time live revenue for active stays
    now_ms = int(time.time() * 1000)
    live_folio_revenue = 0
    for s in active_stays:
        nights = calculate_nights(s["check_in_at"], now_ms)
        stay_charge = nights * s["nightly_rate"]
        live_folio_revenue += (stay_charge + s["folio_charges"])

    cur.execute("SELECT SUM(total_billed) as settled_revenue FROM stays WHERE status = 'checked_out'")
    settled_rev_row = cur.fetchone()
    settled_revenue = settled_rev_row["settled_revenue"] or 0

    conn.close()

    return {
        "hotel_name": "Xenon Grand Hotel & Residences",
        "tagline": "Private Suites, Villas & Sanctuaries",
        "currency": "₹",
        "total_rooms": total_rooms,
        "occupied": occupied,
        "vacant": vacant,
        "cleaning": cleaning,
        "maintenance": maintenance,
        "occupancy_rate": occupancy_rate,
        "active_stays_count": len(active_stays),
        "active_guests_count": active_guests_count,
        "live_folio_revenue": live_folio_revenue,
        "settled_revenue": settled_revenue,
        "total_revenue": live_folio_revenue + settled_revenue
    }

@app.get("/api/rooms")
def get_rooms():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rooms WHERE active = 1 ORDER BY wing ASC, room_number ASC")
    raw_rooms = [dict(r) for r in cur.fetchall()]

    # Fetch active stays
    cur.execute("SELECT * FROM stays WHERE status = 'checked_in'")
    active_stays = [dict(s) for s in cur.fetchall()]
    stay_map = {s["room_id"]: s for s in active_stays}

    # Fetch folio charges for all active stays
    stay_ids = [s["id"] for s in active_stays]
    folio_map = {}
    if stay_ids:
        placeholders = ",".join(["?"] * len(stay_ids))
        cur.execute(f"SELECT * FROM folio_charges WHERE stay_id IN ({placeholders}) ORDER BY created_at DESC", stay_ids)
        for ch in cur.fetchall():
            c_dict = dict(ch)
            folio_map.setdefault(c_dict["stay_id"], []).append(c_dict)

    now_ms = int(time.time() * 1000)
    enriched_rooms = []

    for room in raw_rooms:
        try:
            room["amenities"] = json.loads(room["amenities"])
        except Exception:
            room["amenities"] = []

        active_stay = stay_map.get(room["id"])
        if active_stay:
            nights = calculate_nights(active_stay["check_in_at"], now_ms)
            stay_charge = nights * active_stay["nightly_rate"]
            folio_items = folio_map.get(active_stay["id"], [])
            folio_sum = sum(item["amount"] for item in folio_items)
            gross_total = stay_charge + folio_sum
            net_due = max(0, gross_total - active_stay["advance_paid"])

            active_stay_enriched = {
                **active_stay,
                "nights_elapsed": nights,
                "room_stay_charges": stay_charge,
                "folio_charges_list": folio_items,
                "folio_sum": folio_sum,
                "calculated_gross_total": gross_total,
                "calculated_due": net_due,
            }
            room["active_stay"] = active_stay_enriched
        else:
            room["active_stay"] = None

        enriched_rooms.append(room)

    conn.close()
    return {"rooms": enriched_rooms}

@app.post("/api/rooms", status_code=201)
def create_room(payload: RoomCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM rooms WHERE room_number = ?", (payload.room_number.strip(),))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Suite / Room number already exists.")

    now_ms = int(time.time() * 1000)
    cur.execute("""
        INSERT INTO rooms (room_number, room_type, wing, capacity, base_rate, status, amenities, active, created_at)
        VALUES (?, ?, ?, ?, ?, 'vacant', ?, 1, ?)
    """, (
        payload.room_number.strip(),
        payload.room_type.strip(),
        payload.wing.strip(),
        payload.capacity,
        payload.base_rate,
        json.dumps(payload.amenities),
        now_ms
    ))
    new_id = cur.lastrowid
    conn.commit()

    cur.execute("SELECT * FROM rooms WHERE id = ?", (new_id,))
    room = dict(cur.fetchone())
    room["amenities"] = payload.amenities
    room["active_stay"] = None

    conn.close()
    return {"ok": True, "room": room}

@app.patch("/api/rooms/{room_id}/status")
def update_room_status(room_id: int, payload: StatusUpdate):
    if payload.status not in ["vacant", "cleaning", "maintenance", "occupied"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rooms WHERE id = ? AND active = 1", (room_id,))
    room = cur.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="Suite not found")

    if room["status"] == "occupied" and payload.status != "occupied":
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot alter status of occupied suite. Perform check-out first.")

    cur.execute("UPDATE rooms SET status = ? WHERE id = ?", (payload.status, room_id))
    conn.commit()
    conn.close()

    return {"ok": True, "room_id": room_id, "status": payload.status}

@app.patch("/api/rooms/{room_id}")
def update_room(room_id: int, payload: RoomUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rooms WHERE id = ? AND active = 1", (room_id,))
    room = cur.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="Suite not found")

    updates = []
    values = []

    if payload.room_number is not None:
        updates.append("room_number = ?")
        values.append(payload.room_number.strip())
    if payload.room_type is not None:
        updates.append("room_type = ?")
        values.append(payload.room_type.strip())
    if payload.wing is not None:
        updates.append("wing = ?")
        values.append(payload.wing.strip())
    if payload.capacity is not None:
        updates.append("capacity = ?")
        values.append(payload.capacity)
    if payload.base_rate is not None:
        updates.append("base_rate = ?")
        values.append(payload.base_rate)
    if payload.status is not None and payload.status in ["vacant", "cleaning", "maintenance"]:
        updates.append("status = ?")
        values.append(payload.status)
    if payload.amenities is not None:
        updates.append("amenities = ?")
        values.append(json.dumps(payload.amenities))

    if updates:
        values.append(room_id)
        cur.execute(f"UPDATE rooms SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

    conn.close()
    return {"ok": True, "message": "Suite specifications updated"}

@app.delete("/api/rooms/{room_id}")
def delete_room(room_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    room = cur.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="Suite not found")

    if room["status"] == "occupied":
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot decommission suite with an in-house guest.")

    cur.execute("UPDATE rooms SET active = 0 WHERE id = ?", (room_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "message": f"Suite {room['room_number']} archived"}

@app.post("/api/checkin", status_code=201)
def check_in_guest(payload: CheckInRequest):
    if not payload.guest_name.strip():
        raise HTTPException(status_code=400, detail="Guest name is mandatory")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM rooms WHERE id = ? AND active = 1", (payload.room_id,))
    room = cur.fetchone()
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="Suite not found")

    if room["status"] == "occupied":
        conn.close()
        raise HTTPException(status_code=409, detail=f"Suite {room['room_number']} is currently occupied.")

    now_ms = int(time.time() * 1000)
    nights = max(1, payload.stay_nights)
    expected_out_ms = now_ms + (nights * 86400 * 1000)
    rate = payload.nightly_rate if payload.nightly_rate is not None else room["base_rate"]
    stay_id = f"XEN-STAY-{random.randint(10000, 99999)}"

    cur.execute("""
        INSERT INTO stays (
            id, room_id, guest_name, guest_phone, guest_email, vip_tier,
            id_proof_type, id_proof_number, adults, children, stay_nights,
            check_in_at, expected_check_out_at, nightly_rate, advance_paid,
            folio_charges, status, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'checked_in', ?, ?)
    """, (
        stay_id, room["id"], payload.guest_name.strip(), payload.guest_phone.strip(),
        payload.guest_email.strip(), payload.vip_tier, payload.id_proof_type,
        payload.id_proof_number.strip(), max(1, payload.adults), max(0, payload.children),
        nights, now_ms, expected_out_ms, rate, max(0, payload.advance_paid),
        payload.notes.strip(), now_ms
    ))

    # Mark room occupied
    cur.execute("UPDATE rooms SET status = 'occupied' WHERE id = ?", (room["id"],))
    conn.commit()
    conn.close()

    return {
        "ok": True,
        "stay_id": stay_id,
        "room_number": room["room_number"],
        "guest_name": payload.guest_name,
        "vip_tier": payload.vip_tier,
        "message": f"Welcome {payload.guest_name} to {room['room_number']}."
    }

@app.post("/api/checkout")
def check_out_guest(payload: CheckOutRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM stays WHERE id = ?", (payload.stay_id,))
    stay = cur.fetchone()
    if not stay:
        conn.close()
        raise HTTPException(status_code=404, detail="Stay record not found")

    if stay["status"] != "checked_in":
        conn.close()
        raise HTTPException(status_code=400, detail="Stay has already been settled and checked out.")

    cur.execute("SELECT * FROM rooms WHERE id = ?", (stay["room_id"],))
    room = cur.fetchone()

    now_ms = int(time.time() * 1000)
    nights = calculate_nights(stay["check_in_at"], now_ms)
    room_charges = nights * stay["nightly_rate"]

    # Record damage charge if any
    if payload.damage_charges > 0:
        cur.execute("""
            INSERT INTO folio_charges (stay_id, charge_type, description, amount, created_at)
            VALUES (?, 'other', 'Sanctuary Restoration & Property Assessment', ?, ?)
        """, (stay["id"], payload.damage_charges, now_ms))

    # Fetch all folio charges
    cur.execute("SELECT * FROM folio_charges WHERE stay_id = ?", (stay["id"],))
    folio_items = [dict(ch) for ch in cur.fetchall()]
    total_folio_charges = sum(item["amount"] for item in folio_items)

    discount = max(0, payload.discount)
    gross_total = room_charges + total_folio_charges - discount
    net_due = max(0, gross_total - stay["advance_paid"])

    combined_notes = stay["notes"]
    if payload.notes.strip():
        combined_notes = f"{combined_notes}\nCheckout Note: {payload.notes.strip()}".strip()

    # Update stay record
    cur.execute("""
        UPDATE stays SET
            status = 'checked_out',
            actual_check_out_at = ?,
            folio_charges = ?,
            discount = ?,
            damage_charges = ?,
            total_billed = ?,
            notes = ?
        WHERE id = ?
    """, (now_ms, total_folio_charges, discount, payload.damage_charges, gross_total, combined_notes, stay["id"]))

    # Transition room to housekeeping / cleaning
    if room:
        cur.execute("UPDATE rooms SET status = 'cleaning' WHERE id = ?", (room["id"],))

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "summary": {
            "stay_id": stay["id"],
            "room_number": room["room_number"] if room else "N/A",
            "room_type": room["room_type"] if room else "Sanctuary Suite",
            "guest_name": stay["guest_name"],
            "vip_tier": stay["vip_tier"],
            "check_in_at": stay["check_in_at"],
            "check_out_at": now_ms,
            "nights": nights,
            "nightly_rate": stay["nightly_rate"],
            "room_charges": room_charges,
            "folio_charges": total_folio_charges,
            "folio_items": folio_items,
            "discount": discount,
            "damage_charges": payload.damage_charges,
            "advance_paid": stay["advance_paid"],
            "gross_total": gross_total,
            "net_due": net_due,
        }
    }

@app.post("/api/folio/charge", status_code=201)
def add_folio_charge(payload: FolioChargeRequest):
    conn = get_connection()
    cur = conn.cursor()

    target_stay_id = payload.stay_id
    if not target_stay_id and payload.room_id:
        cur.execute("SELECT id FROM stays WHERE room_id = ? AND status = 'checked_in'", (payload.room_id,))
        stay = cur.fetchone()
        if stay:
            target_stay_id = stay["id"]

    if not target_stay_id:
        conn.close()
        raise HTTPException(status_code=404, detail="No active in-house guest found for this suite.")

    cur.execute("SELECT * FROM stays WHERE id = ?", (target_stay_id,))
    stay = cur.fetchone()
    if not stay or stay["status"] != "checked_in":
        conn.close()
        raise HTTPException(status_code=400, detail="Guest is no longer checked in.")

    now_ms = int(time.time() * 1000)
    cur.execute("""
        INSERT INTO folio_charges (stay_id, charge_type, description, amount, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (target_stay_id, payload.charge_type, payload.description.strip(), payload.amount, now_ms))

    charge_id = cur.lastrowid

    # Update stays cached folio_charges
    cur.execute("UPDATE stays SET folio_charges = folio_charges + ? WHERE id = ?", (payload.amount, target_stay_id))
    conn.commit()

    cur.execute("SELECT * FROM folio_charges WHERE id = ?", (charge_id,))
    charge = dict(cur.fetchone())
    conn.close()

    return {"ok": True, "charge": charge}

@app.get("/api/folio/{stay_id}")
def get_folio(stay_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.*, r.room_number, r.room_type, r.wing
        FROM stays s
        JOIN rooms r ON s.room_id = r.id
        WHERE s.id = ?
    """, (stay_id,))
    stay = cur.fetchone()
    if not stay:
        conn.close()
        raise HTTPException(status_code=404, detail="Stay record not found")

    cur.execute("SELECT * FROM folio_charges WHERE stay_id = ? ORDER BY created_at ASC", (stay_id,))
    folio_items = [dict(ch) for ch in cur.fetchall()]

    stay_dict = dict(stay)
    now_ms = int(time.time() * 1000)
    out_ms = stay_dict["actual_check_out_at"] or now_ms
    nights = calculate_nights(stay_dict["check_in_at"], out_ms)
    room_charges = nights * stay_dict["nightly_rate"]
    folio_sum = sum(item["amount"] for item in folio_items)
    gross_total = room_charges + folio_sum - stay_dict["discount"]
    net_due = max(0, gross_total - stay_dict["advance_paid"])

    conn.close()

    return {
        "stay": stay_dict,
        "nights": nights,
        "room_charges": room_charges,
        "folio_items": folio_items,
        "folio_sum": folio_sum,
        "gross_total": gross_total,
        "net_due": net_due
    }

@app.get("/api/history")
def get_history(search: Optional[str] = None):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT s.*, r.room_number, r.room_type, r.wing
        FROM stays s
        JOIN rooms r ON s.room_id = r.id
    """
    params = []
    if search:
        query += " WHERE s.guest_name LIKE ? OR s.id LIKE ? OR r.room_number LIKE ?"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])

    query += " ORDER BY s.created_at DESC LIMIT 100"

    cur.execute(query, params)
    history = [dict(row) for row in cur.fetchall()]

    conn.close()
    return {"history": history}

@app.get("/api/catalog")
def get_catalog():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM catalog ORDER BY category ASC, price DESC")
    items = [dict(row) for row in cur.fetchall()]
    conn.close()
    return {"catalog": items}

@app.post("/api/reset-demo")
def reset_demo():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS folio_charges")
    cur.execute("DROP TABLE IF EXISTS stays")
    cur.execute("DROP TABLE IF EXISTS rooms")
    cur.execute("DROP TABLE IF EXISTS catalog")
    conn.commit()
    conn.close()

    init_db()
    return {"ok": True, "message": "Demo data refreshed to luxury estate state."}

# ----------------- Static Frontend Mount (OS-Agnostic) -----------------

STATIC_DIR = str((BACKEND_DIR.parent / "static").resolve())
app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    print(f"Xenon Hotel Management Server running on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)

