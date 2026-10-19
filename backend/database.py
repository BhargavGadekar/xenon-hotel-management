import sqlite3
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "xenon_hotel.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT UNIQUE NOT NULL,
        room_type TEXT NOT NULL DEFAULT 'Executive Suite',
        wing TEXT NOT NULL DEFAULT 'Wing I · Imperial Pavilion',
        capacity INTEGER NOT NULL DEFAULT 2,
        base_rate INTEGER NOT NULL DEFAULT 25000,
        status TEXT NOT NULL DEFAULT 'vacant' CHECK (status IN ('vacant', 'occupied', 'cleaning', 'maintenance')),
        amenities TEXT NOT NULL DEFAULT '[]',
        active INTEGER NOT NULL DEFAULT 1,
        created_at INTEGER NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stays (
        id TEXT PRIMARY KEY,
        room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
        guest_name TEXT NOT NULL,
        guest_phone TEXT NOT NULL DEFAULT '',
        guest_email TEXT NOT NULL DEFAULT '',
        vip_tier TEXT NOT NULL DEFAULT 'Gold VIP',
        id_proof_type TEXT NOT NULL DEFAULT 'Passport',
        id_proof_number TEXT NOT NULL DEFAULT '',
        adults INTEGER NOT NULL DEFAULT 1,
        children INTEGER NOT NULL DEFAULT 0,
        stay_nights INTEGER NOT NULL DEFAULT 1,
        check_in_at INTEGER NOT NULL,
        expected_check_out_at INTEGER NOT NULL,
        actual_check_out_at INTEGER,
        nightly_rate INTEGER NOT NULL,
        advance_paid INTEGER NOT NULL DEFAULT 0,
        folio_charges INTEGER NOT NULL DEFAULT 0,
        discount INTEGER NOT NULL DEFAULT 0,
        damage_charges INTEGER NOT NULL DEFAULT 0,
        total_billed INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'checked_in' CHECK (status IN ('checked_in', 'checked_out', 'cancelled')),
        notes TEXT NOT NULL DEFAULT '',
        created_at INTEGER NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS folio_charges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stay_id TEXT NOT NULL REFERENCES stays(id) ON DELETE CASCADE,
        charge_type TEXT NOT NULL DEFAULT 'room_service',
        description TEXT NOT NULL,
        amount INTEGER NOT NULL,
        created_at INTEGER NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        price INTEGER NOT NULL,
        icon TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed initial data if rooms table is empty
    cur.execute("SELECT COUNT(*) as count FROM rooms")
    count = cur.fetchone()["count"]
    if count == 0:
        seed_starter_data(conn)

    conn.close()

def seed_starter_data(conn: sqlite3.Connection):
    cur = conn.cursor()
    now_ms = int(time.time() * 1000)
    day_ms = 86400 * 1000

    starter_rooms = [
        ("Suite 101", "Presidential Oceanfront Villa", "Wing I · Imperial Pavilion", 4, 85000, "occupied",
         '["Private Plunge Pool", "24/7 Dedicated Butler", "Panoramic Ocean View", "Walk-in Dressing Room"]'),
        ("Suite 102", "Royal Enclave Grand Chamber", "Wing I · Imperial Pavilion", 2, 45000, "vacant",
         '["King Silk Canopy Bed", "Private Balcony Veranda", "Jacuzzi Spa Bath", "Fine Espresso Bar"]'),
        ("Suite 201", "Horizon Penthouse Residence", "Wing II · Royal Enclave", 3, 65000, "occupied",
         '["Private Rooftop Solarium", "Limestone Fireplace", "Wine & Champagne Cellar", "Deep Soaking Marble Tub"]'),
        ("Suite 202", "Executive Atelier Suite", "Wing II · Royal Enclave", 2, 32000, "cleaning",
         '["Bespoke Executive Desk", "Botanical Terrace", "Rainfall Hydrotherapy Shower", "Turn-Down Aromatherapy"]'),
        ("Suite 301", "Grand Heritage Pavilion", "Wing III · Atelier Wing", 2, 28000, "vacant",
         '["Vintage Teak Furnishings", "Clawfoot Copper Tub", "Courtyard Garden Access", "Bespoke Tea Bar"]'),
        ("Suite 302", "Solarium Garden Villa", "Wing IV · Garden Villas", 4, 55000, "vacant",
         '["Secluded Courtyard", "Open-Air Garden Rainshower", "Private Sun Deck", "In-Villa Dining Lounge"]'),
        ("Suite 303", "Deluxe Azure Lagoon Chamber", "Wing III · Atelier Wing", 2, 24000, "maintenance",
         '["Direct Lagoon Step-In", "Double Vanity Marble", "Smart Ambience Controls", "Linen Bedding"]'),
        ("Suite 401", "Ambassadorial Royal Estate", "Wing I · Imperial Pavilion", 6, 120000, "vacant",
         '["Dual Master Wings", "Private Helipad Priority", "Executive Conference Lounge", "Private Sommelier Service"]')
    ]

    for r in starter_rooms:
        cur.execute("""
            INSERT INTO rooms (room_number, room_type, wing, capacity, base_rate, status, amenities, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (r[0], r[1], r[2], r[3], r[4], r[5], r[6], now_ms))

    # Room 101 occupied stay: Lord Sterling Hawthorne
    cur.execute("SELECT id FROM rooms WHERE room_number = 'Suite 101'")
    r101_id = cur.fetchone()["id"]
    checkin_101 = now_ms - (2 * day_ms + 14400000) # 2 days and 4 hours ago
    expected_101 = checkin_101 + (4 * day_ms)
    stay_101_id = "XEN-STAY-8821"

    cur.execute("""
        INSERT INTO stays (id, room_id, guest_name, guest_phone, guest_email, vip_tier, id_proof_type, id_proof_number,
                           adults, children, stay_nights, check_in_at, expected_check_out_at, nightly_rate,
                           advance_paid, folio_charges, status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        stay_101_id, r101_id, "Lord Sterling Hawthorne", "+44 7911 123456", "sterling@hawthorne-holdings.co.uk",
        "Black Diamond VIP", "Passport", "GBR-99201488", 2, 0, 4,
        checkin_101, expected_101, 85000, 50000, 48500, "checked_in",
        "Prefers 1996 Dom Pérignon chilled at 8°C. Butler service notified for evening private terrace dining.", checkin_101
    ))

    # Folio charges for 101
    cur.execute("""
        INSERT INTO folio_charges (stay_id, charge_type, description, amount, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (stay_101_id, "room_service", "Dom Pérignon Vintage 2012 (Bottle) & Caviar Service", 32000, checkin_101 + 3600000))

    cur.execute("""
        INSERT INTO folio_charges (stay_id, charge_type, description, amount, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (stay_101_id, "spa_wellness", "Imperial Warm Stone Hydrotherapy & Aromatherapy (Couple)", 16500, checkin_101 + 86400000))

    # Room 201 occupied stay: Madame Vivienne Chen
    cur.execute("SELECT id FROM rooms WHERE room_number = 'Suite 201'")
    r201_id = cur.fetchone()["id"]
    checkin_201 = now_ms - (1 * day_ms + 7200000)
    expected_201 = checkin_201 + (3 * day_ms)
    stay_201_id = "XEN-STAY-9042"

    cur.execute("""
        INSERT INTO stays (id, room_id, guest_name, guest_phone, guest_email, vip_tier, id_proof_type, id_proof_number,
                           adults, children, stay_nights, check_in_at, expected_check_out_at, nightly_rate,
                           advance_paid, folio_charges, status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        stay_201_id, r201_id, "Madame Vivienne Chen", "+1 (212) 555-0199", "v.chen@atelier-art.com",
        "Gold VIP", "Passport", "USA-58201994", 1, 0, 3,
        checkin_201, expected_201, 65000, 30000, 14500, "checked_in",
        "Allergies: Pistachio. Requested high-floor silence and silk pillow replacements.", checkin_201
    ))

    cur.execute("""
        INSERT INTO folio_charges (stay_id, charge_type, description, amount, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (stay_201_id, "fine_dining", "Gourmet White Truffle Risotto & Saint-Émilion Grand Cru", 14500, checkin_201 + 18000000))

    # Past completed stay for history demonstration
    past_stay_id = "XEN-STAY-7104"
    cur.execute("SELECT id FROM rooms WHERE room_number = 'Suite 102'")
    r102_id = cur.fetchone()["id"]
    past_in = now_ms - (6 * day_ms)
    past_out = now_ms - (3 * day_ms)
    cur.execute("""
        INSERT INTO stays (id, room_id, guest_name, guest_phone, guest_email, vip_tier, id_proof_type, id_proof_number,
                           adults, children, stay_nights, check_in_at, expected_check_out_at, actual_check_out_at,
                           nightly_rate, advance_paid, folio_charges, discount, damage_charges, total_billed,
                           status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        past_stay_id, r102_id, "Baroness Alexandra von Berg", "+41 22 739 1100", "alexandra@vonberg.ch",
        "Black Diamond VIP", "Passport", "CHE-4481023", 2, 0, 3,
        past_in, past_out, past_out, 45000, 50000, 22000, 5000, 0, 152000,
        "checked_out", "Flawless stay. Commended butler staff and concierge.", past_in
    ))

    cur.execute("""
        INSERT INTO folio_charges (stay_id, charge_type, description, amount, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (past_stay_id, "room_service", "Caviar Tasting & Rare Vintage Port Wine", 22000, past_in + 86400000))

    # Seed luxury catalog
    catalog_items = [
        ("Dom Pérignon Vintage 2012", "Dining & Wine", "Cellar-aged vintage French champagne served in crystal flutes with berries", 28000, "🍾"),
        ("Beluga Caviar Tasting Service", "Dining & Wine", "50g Royal Beluga served with warm brioche blinis and cultured butter", 18500, "🥂"),
        ("White Truffle Risotto en Suite", "Dining & Wine", "Acquerello carnaroli rice with shaved Alba white truffles & 36-month Parmigiano", 5500, "🍽️"),
        ("Kobe Wagyu A5 Striploin Course", "Dining & Wine", "Grade A5 Hyogo Prefecture beef seared over Binchotan coals with wasabi demi-glace", 14000, "🥩"),
        ("Imperial Warm Stone Body Ritual", "Spa & Wellness", "90-minute restorative heated volcanic basalt stones and organic damask rose oil", 8500, "✨"),
        ("Dead Sea Mineral Hydro-Facial", "Spa & Wellness", "Deep cellular rejuvenation with pure hyaluronic serum & marine botanicals", 6500, "💆"),
        ("Maybach S680 Airport Transfer", "Concierge & Transport", "Chauffeured private round-trip airport or helipad escort with refreshments", 9500, "🚗"),
        ("Private Riva Yacht Sunset Charter", "Concierge & Transport", "2-hour coastal sunset voyage with private skipper & sommelier pairing", 35000, "🛥️"),
        ("Italian Silk Express Valet Laundry", "Valet & Laundry", "Delicate hand laundering, pressing, and fragrant cedar wardrobe return within 4 hours", 3200, "👔"),
        ("Artisanal Midnight Cellar Minibar", "Suite Amenities", "Replenished single-malt scotches, craft pralines, and mineral waters", 4800, "🥃"),
        ("Bespoke In-Suite Floral Curation", "Suite Amenities", "Freshly cut Ecuadorian white garden roses and orchid arrangement", 3800, "🌹"),
    ]

    for item in catalog_items:
        cur.execute("""
            INSERT INTO catalog (name, category, description, price, icon)
            VALUES (?, ?, ?, ?, ?)
        """, item)

    conn.commit()

def calculate_nights(check_in_ms: int, check_out_ms: Optional[int] = None) -> int:
    target_ms = check_out_ms if check_out_ms else int(time.time() * 1000)
    diff_ms = max(0, target_ms - check_in_ms)
    days = int((diff_ms / (86400 * 1000)) + 0.999) # Ceil to at least 1 day
    return max(1, days)
