import sqlite3
import json
from pathlib import Path
import tempfile
import pytest

from mtgengine.card_definition import CardDefinition
from mtgengine.card_repository import CardRepository


@pytest.fixture
def temp_db():
    """Create a temporary database with test data."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db") as f:
        db_path = f.name
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE cards (
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
    
    cursor.execute("""
        CREATE TABLE rulings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            oracle_id TEXT NOT NULL REFERENCES cards(oracle_id),
            published_at TEXT NOT NULL,
            comment TEXT NOT NULL,
            UNIQUE(oracle_id, published_at, comment)
        )
    """)
    
    # Insert test data
    test_cards = [
        {
            "oracle_id": "test-001",
            "name": "Lightning Bolt",
            "mana_cost": "{R}",
            "type_line": "Instant",
            "oracle_text": "Lightning Bolt deals 3 damage to any target.",
            "colors": json.dumps(["R"]),
            "color_identity": json.dumps(["R"]),
            "keywords": json.dumps([]),
            "power": None,
            "toughness": None,
            "loyalty": None,
            "layout": "normal"
        },
        {
            "oracle_id": "test-002",
            "name": "Serra Angel",
            "mana_cost": "{3}{W}{W}",
            "type_line": "Creature — Angel",
            "oracle_text": "Flying, vigilance",
            "colors": json.dumps(["W"]),
            "color_identity": json.dumps(["W"]),
            "keywords": json.dumps(["Flying", "Vigilance"]),
            "power": "4",
            "toughness": "4",
            "loyalty": None,
            "layout": "normal"
        },
        {
            "oracle_id": "test-003",
            "name": "Black Lotus",
            "mana_cost": "{0}",
            "type_line": "Artifact",
            "oracle_text": "{T}, Sacrifice Black Lotus: Add three mana of any one color.",
            "colors": json.dumps([]),
            "color_identity": json.dumps([]),
            "keywords": json.dumps([]),
            "power": None,
            "toughness": None,
            "loyalty": None,
            "layout": "normal"
        },
        {
            "oracle_id": "test-004",
            "name": "Tarmogoyf",
            "mana_cost": "{1}{G}",
            "type_line": "Creature — Lhurgoyf",
            "oracle_text": "Tarmogoyf's power is equal to the number of card types among cards in all graveyards and its toughness is equal to that number plus 1.",
            "colors": json.dumps(["G"]),
            "color_identity": json.dumps(["G"]),
            "keywords": json.dumps([]),
            "power": "*",
            "toughness": "1+*",
            "loyalty": None,
            "layout": "normal"
        },
        {
            "oracle_id": "test-005",
            "name": "Jace, the Mind Sculptor",
            "mana_cost": "{2}{U}{U}",
            "type_line": "Legendary Planeswalker — Jace",
            "oracle_text": "+2: Look at the top card of target player's library.\n0: Draw three cards, then put two cards from your hand on top of your library.\n-1: Return target creature to its owner's hand.\n-12: Exile all cards from target player's library, then that player shuffles their hand into their library.",
            "colors": json.dumps(["U"]),
            "color_identity": json.dumps(["U"]),
            "keywords": json.dumps([]),
            "power": None,
            "toughness": None,
            "loyalty": 3,
            "layout": "normal"
        }
    ]
    
    for card in test_cards:
        cursor.execute("""
            INSERT INTO cards
                (oracle_id, name, mana_cost, type_line, oracle_text,
                 colors, color_identity, keywords, power, toughness, loyalty, layout)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            card["oracle_id"],
            card["name"],
            card["mana_cost"],
            card["type_line"],
            card["oracle_text"],
            card["colors"],
            card["color_identity"],
            card["keywords"],
            card["power"],
            card["toughness"],
            card["loyalty"],
            card["layout"]
        ))
    
    # Insert test rulings
    cursor.execute("""
        INSERT INTO rulings (oracle_id, published_at, comment)
        VALUES (?, ?, ?)
    """, ("test-001", "2004-10-04", "You can target yourself with Lightning Bolt."))
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


def test_card_definition_creation():
    """Test that CardDefinition can be created with proper types."""
    card = CardDefinition(
        oracle_id="test-id",
        name="Test Card",
        mana_cost="{2}{U}",
        type_line="Instant",
        oracle_text="Do something.",
        colors=["U"],
        color_identity=["U"],
        keywords=["Flash"],
        power=None,
        toughness=None,
        loyalty=None,
        layout="normal"
    )
    
    assert card.oracle_id == "test-id"
    assert card.name == "Test Card"
    assert card.mana_cost == "{2}{U}"
    assert card.colors == ["U"]
    assert card.keywords == ["Flash"]


def test_card_definition_with_nullable_fields():
    """Test CardDefinition with nullable fields."""
    card = CardDefinition(
        oracle_id="test-id",
        name="Land Card",
        mana_cost=None,
        type_line="Land",
        oracle_text=None,
        colors=[],
        color_identity=[],
        keywords=[],
        power=None,
        toughness=None,
        loyalty=None,
        layout="normal"
    )
    
    assert card.mana_cost is None
    assert card.oracle_text is None
    assert card.power is None


def test_card_definition_with_star_power_toughness():
    """Test CardDefinition can handle * in power/toughness."""
    card = CardDefinition(
        oracle_id="test-id",
        name="Variable Creature",
        mana_cost="{1}{G}",
        type_line="Creature — Test",
        oracle_text="Power and toughness vary.",
        colors=["G"],
        color_identity=["G"],
        keywords=[],
        power="*",
        toughness="1+*",
        loyalty=None,
        layout="normal"
    )
    
    assert card.power == "*"
    assert card.toughness == "1+*"


def test_repository_init(temp_db):
    """Test that CardRepository can be initialized."""
    repo = CardRepository(temp_db)
    assert repo is not None
    repo.close()


def test_repository_context_manager(temp_db):
    """Test that CardRepository works as a context manager."""
    with CardRepository(temp_db) as repo:
        assert repo is not None


def test_get_by_oracle_id(temp_db):
    """Test retrieving a card by oracle_id."""
    with CardRepository(temp_db) as repo:
        card = repo.get_by_oracle_id("test-001")
        
        assert card is not None
        assert card.oracle_id == "test-001"
        assert card.name == "Lightning Bolt"
        assert card.mana_cost == "{R}"
        assert card.type_line == "Instant"
        assert card.colors == ["R"]
        assert card.keywords == []


def test_get_by_oracle_id_not_found(temp_db):
    """Test that get_by_oracle_id returns None for non-existent cards."""
    with CardRepository(temp_db) as repo:
        card = repo.get_by_oracle_id("non-existent")
        assert card is None


def test_get_by_name(temp_db):
    """Test retrieving a card by exact name."""
    with CardRepository(temp_db) as repo:
        card = repo.get_by_name("Serra Angel")
        
        assert card is not None
        assert card.oracle_id == "test-002"
        assert card.name == "Serra Angel"
        assert card.power == "4"
        assert card.toughness == "4"
        assert card.keywords == ["Flying", "Vigilance"]


def test_get_by_name_case_insensitive(temp_db):
    """Test that get_by_name is case-insensitive."""
    with CardRepository(temp_db) as repo:
        card = repo.get_by_name("lightning bolt")
        assert card is not None
        assert card.name == "Lightning Bolt"


def test_get_by_name_not_found(temp_db):
    """Test that get_by_name returns None for non-existent cards."""
    with CardRepository(temp_db) as repo:
        card = repo.get_by_name("Non-Existent Card")
        assert card is None


def test_get_creature_with_power_toughness(temp_db):
    """Test retrieving a creature with power/toughness."""
    with CardRepository(temp_db) as repo:
        card = repo.get_by_name("Serra Angel")
        
        assert card.power == "4"
        assert card.toughness == "4"


def test_get_creature_with_star_power_toughness(temp_db):
    """Test retrieving a creature with * power/toughness."""
    with CardRepository(temp_db) as repo:
        card = repo.get_by_name("Tarmogoyf")
        
        assert card.power == "*"
        assert card.toughness == "1+*"


def test_get_planeswalker_with_loyalty(temp_db):
    """Test retrieving a planeswalker with loyalty."""
    with CardRepository(temp_db) as repo:
        card = repo.get_by_name("Jace, the Mind Sculptor")
        
        assert card.loyalty == 3
        assert "Planeswalker" in card.type_line


def test_search_by_name(temp_db):
    """Test searching for cards by name."""
    with CardRepository(temp_db) as repo:
        results = repo.search("Angel")
        
        assert len(results) == 1
        assert results[0].name == "Serra Angel"


def test_search_by_oracle_text(temp_db):
    """Test searching for cards by oracle text."""
    with CardRepository(temp_db) as repo:
        results = repo.search("damage")
        
        assert len(results) == 1
        assert results[0].name == "Lightning Bolt"


def test_search_case_insensitive(temp_db):
    """Test that search is case-insensitive."""
    with CardRepository(temp_db) as repo:
        results = repo.search("ANGEL")
        
        assert len(results) == 1
        assert results[0].name == "Serra Angel"


def test_search_multiple_results(temp_db):
    """Test search returning multiple results."""
    with CardRepository(temp_db) as repo:
        # All test cards have 'a' in name or text
        results = repo.search("a")
        
        assert len(results) >= 2


def test_search_no_results(temp_db):
    """Test search with no matching results."""
    with CardRepository(temp_db) as repo:
        results = repo.search("ZZZZZZZZZ")
        
        assert len(results) == 0
        assert results == []


def test_search_empty_query(temp_db):
    """Test search with empty query returns all cards."""
    with CardRepository(temp_db) as repo:
        results = repo.search("")
        
        assert len(results) == 5  # All test cards


def test_search_wildcard_not_treated_as_sql(temp_db):
    """Test that SQL wildcards in search query are treated as literals."""
    with CardRepository(temp_db) as repo:
        # '_' should match literally (underscore character), not as SQL wildcard
        results = repo.search("_")
        
        # None of our test cards have underscore in name or text
        assert len(results) == 0
        
        # '%' should also be treated literally
        results_percent = repo.search("%")
        assert len(results_percent) == 0


def test_repository_with_path_object(temp_db):
    """Test that repository accepts Path objects."""
    path_obj = Path(temp_db)
    with CardRepository(path_obj) as repo:
        card = repo.get_by_name("Lightning Bolt")
        assert card is not None
