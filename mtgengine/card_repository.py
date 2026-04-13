"""SQLite-backed read-only repository for CardDefinition lookups."""

import sqlite3
import json
from pathlib import Path
from typing import Self

from mtgengine.card_definition import CardDefinition


class CardRepository:
    def __init__(self, db_path: str | Path):
        """Initialize repository with a SQLite database path."""
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def get_by_oracle_id(self, oracle_id: str) -> CardDefinition | None:
        """Retrieve a card by its unique oracle ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cards WHERE oracle_id = ?", (oracle_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_card_definition(row)

    def get_by_name(self, name: str) -> CardDefinition | None:
        """Retrieve a card by its exact name (case-insensitive)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM cards WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_card_definition(row)

    def search(self, query: str) -> list[CardDefinition]:
        """Search cards by name or oracle text (case-insensitive)."""
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        search_pattern = f"%{escaped}%"
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM cards
            WHERE LOWER(name) LIKE LOWER(?) ESCAPE '\\'
               OR LOWER(oracle_text) LIKE LOWER(?) ESCAPE '\\'
            """,
            (search_pattern, search_pattern),
        )
        return [self._row_to_card_definition(row) for row in cursor.fetchall()]

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def _row_to_card_definition(self, row: sqlite3.Row) -> CardDefinition:
        return CardDefinition(
            oracle_id=row["oracle_id"],
            name=row["name"],
            mana_cost=row["mana_cost"],
            type_line=row["type_line"],
            oracle_text=row["oracle_text"],
            colors=json.loads(row["colors"]) if row["colors"] else [],
            color_identity=json.loads(row["color_identity"]) if row["color_identity"] else [],
            keywords=json.loads(row["keywords"]) if row["keywords"] else [],
            power=row["power"],
            toughness=row["toughness"],
            loyalty=row["loyalty"],
            layout=row["layout"]
        )
