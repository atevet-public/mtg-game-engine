#!/usr/bin/env python3
"""
Import Scryfall card and ruling data into a SQLite database.

Downloads the latest Oracle Cards and Rulings bulk data from Scryfall,
filters to gameplay-relevant fields, and populates a local SQLite database.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from urllib.request import urlopen


def get_bulk_data_info():
    """Fetch the bulk data manifest from Scryfall."""
    print("Fetching bulk data info from Scryfall...")
    url = "https://api.scryfall.com/bulk-data"
    
    with urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
    
    oracle_cards_info = None
    rulings_info = None
    
    for item in data["data"]:
        if item["type"] == "oracle_cards":
            oracle_cards_info = item
        elif item["type"] == "rulings":
            rulings_info = item
    
    if not oracle_cards_info:
        raise ValueError("Could not find oracle_cards bulk data")
    if not rulings_info:
        raise ValueError("Could not find rulings bulk data")
    
    return oracle_cards_info, rulings_info


def download_json_data(url, description):
    """Download and parse JSON from a URL."""
    print(f"Downloading {description}...")
    print(f"  URL: {url}")
    
    with urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
    
    print(f"  Downloaded {len(data)} items")
    return data


def create_database(db_path):
    """Create the SQLite database with the required schema."""
    print(f"Creating database at {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create cards table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            oracle_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mana_cost TEXT,
            type_line TEXT NOT NULL,
            oracle_text TEXT,
            colors TEXT,
            color_identity TEXT,
            keywords TEXT,
            power TEXT,
            toughness TEXT,
            loyalty INTEGER,
            layout TEXT
        )
    """)
    
    # Create rulings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rulings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oracle_id TEXT NOT NULL REFERENCES cards(oracle_id),
            published_at TEXT NOT NULL,
            comment TEXT NOT NULL
        )
    """)
    
    conn.commit()
    return conn


def filter_and_insert_cards(conn, cards_data):
    """Filter cards to gameplay-relevant fields and insert into database."""
    print("Inserting cards into database...")
    
    cursor = conn.cursor()
    inserted = 0
    skipped = 0
    
    for card in cards_data:
        # Skip cards without oracle_id (shouldn't happen, but be safe)
        if "oracle_id" not in card:
            skipped += 1
            continue
        
        # Extract relevant fields
        oracle_id = card["oracle_id"]
        name = card.get("name", "")
        mana_cost = card.get("mana_cost")
        type_line = card.get("type_line", "")
        oracle_text = card.get("oracle_text")
        colors = json.dumps(card.get("colors", []))
        color_identity = json.dumps(card.get("color_identity", []))
        keywords = json.dumps(card.get("keywords", []))
        power = card.get("power")
        toughness = card.get("toughness")
        loyalty = card.get("loyalty")
        layout = card.get("layout", "normal")
        
        # Convert loyalty to integer if present
        if loyalty is not None:
            try:
                loyalty = int(loyalty)
            except (ValueError, TypeError):
                loyalty = None
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO cards 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                oracle_id,
                name,
                mana_cost,
                type_line,
                oracle_text,
                colors,
                color_identity,
                keywords,
                power,
                toughness,
                loyalty,
                layout
            ))
            inserted += 1
            
            if inserted % 1000 == 0:
                print(f"  Inserted {inserted} cards...")
                conn.commit()
        
        except sqlite3.Error as e:
            print(f"  Error inserting card {name} ({oracle_id}): {e}")
            skipped += 1
    
    conn.commit()
    print(f"Finished inserting cards: {inserted} inserted, {skipped} skipped")
    return inserted, skipped


def insert_rulings(conn, rulings_data):
    """Insert rulings into database."""
    print("Inserting rulings into database...")
    
    cursor = conn.cursor()
    inserted = 0
    skipped = 0
    
    for ruling in rulings_data:
        oracle_id = ruling.get("oracle_id")
        published_at = ruling.get("published_at")
        comment = ruling.get("comment")
        
        if not oracle_id or not published_at or not comment:
            skipped += 1
            continue
        
        try:
            cursor.execute("""
                INSERT INTO rulings (oracle_id, published_at, comment)
                VALUES (?, ?, ?)
            """, (oracle_id, published_at, comment))
            inserted += 1
            
            if inserted % 5000 == 0:
                print(f"  Inserted {inserted} rulings...")
                conn.commit()
        
        except sqlite3.Error as e:
            print(f"  Error inserting ruling for {oracle_id}: {e}")
            skipped += 1
    
    conn.commit()
    print(f"Finished inserting rulings: {inserted} inserted, {skipped} skipped")
    return inserted, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Import Scryfall card data into SQLite database"
    )
    parser.add_argument(
        "--db",
        default="cards.db",
        help="Path to SQLite database file (default: cards.db)"
    )
    args = parser.parse_args()
    
    db_path = Path(args.db)
    
    try:
        # Get bulk data URLs
        oracle_cards_info, rulings_info = get_bulk_data_info()
        
        # Download data
        cards_data = download_json_data(
            oracle_cards_info["download_uri"],
            "Oracle Cards"
        )
        rulings_data = download_json_data(
            rulings_info["download_uri"],
            "Rulings"
        )
        
        # Create database
        conn = create_database(db_path)
        
        # Insert data
        cards_inserted, cards_skipped = filter_and_insert_cards(conn, cards_data)
        rulings_inserted, rulings_skipped = insert_rulings(conn, rulings_data)
        
        conn.close()
        
        print("\n" + "="*60)
        print("Import complete!")
        print(f"Database: {db_path.absolute()}")
        print(f"Cards: {cards_inserted} inserted, {cards_skipped} skipped")
        print(f"Rulings: {rulings_inserted} inserted, {rulings_skipped} skipped")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
