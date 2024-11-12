from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    delete_meal,
    get_meal_by_id,
    get_meal_by_name,
    update_meal_stats,
    get_leaderboard
)

######################################################
#
#    Fixtures and Utilities
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Add and delete
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the database."""
    create_meal(meal="Pasta", cuisine="Italian", price=12.99, difficulty="MED")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "SQL query did not match the expected structure."
    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Pasta", "Italian", 12.99, "MED")
    assert actual_arguments == expected_arguments, f"Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with duplicate name, which should raise an error."""
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")
    with pytest.raises(ValueError, match="Meal with name 'Pasta' already exists"):
        create_meal(meal="Pasta", cuisine="Italian", price=12.99, difficulty="MED")

def test_create_meal_invalid_price():
    """Test error when creating a meal with invalid price."""
    with pytest.raises(ValueError, match="Invalid price: -5.99. Price must be a positive number."):
        create_meal(meal="Pizza", cuisine="Italian", price=-5.99, difficulty="LOW")

def test_create_meal_invalid_difficulty():
    """Test error when creating a meal with invalid difficulty."""
    with pytest.raises(ValueError, match="Invalid difficulty level: UNKNOWN. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Pizza", cuisine="Italian", price=15.99, difficulty="UNKNOWN")

def test_delete_meal(mock_cursor):
    """Test soft deleting a meal by meal ID."""
    mock_cursor.fetchone.return_value = [False]
    delete_meal(1)

    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_select_sql == expected_select_sql, "The SELECT query did not match."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match."

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_update_args = mock_cursor.execute.call_args_list[1][0][1]

    expected_select_args = (1,)
    expected_update_args = (1,)
    assert actual_select_args == expected_select_args, f"Expected {expected_select_args}, got {actual_select_args}."
    assert actual_update_args == expected_update_args, f"Expected {expected_update_args}, got {actual_update_args}."

def test_delete_meal_bad_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""
    mock_cursor.fetchone.return_value = None
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete an already deleted meal."""
    mock_cursor.fetchone.return_value = [True]
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        delete_meal(1)
    

def test_clear_meals(mock_cursor, mocker):
    """Test clearing all meals in the database."""
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="SQL create statement"))

    clear_meals()
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')
    mock_cursor.executescript.assert_called_once()

######################################################
#
#    Retrieve and update meals
#
######################################################

def test_get_meal_by_id(mock_cursor):
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 12.99, "MED", False)
    result = get_meal_by_id(1)
    expected_result = Meal(1, "Pasta", "Italian", 12.99, "MED")
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query

    actual_arguments = mock_cursor.execute.call_args[0][1]
    assert actual_arguments == (1,), f"Expected (1,), got {actual_arguments}"

def test_get_meal_by_invalid_id(mock_cursor):
    mock_cursor.fetchone.return_value = None
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_deleted_id(mock_cursor):
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 12.99, "MED", True)
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)

def test_get_meal_by_name(mock_cursor):
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 12.99, "MED", False)
    result = get_meal_by_name("Pasta")
    expected_result = Meal(1, "Pasta", "Italian", 12.99, "MED")
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query

def test_get_meal_by_invalid_name(mock_cursor):
    mock_cursor.fetchone.return_value = None
    with pytest.raises(ValueError, match="Meal with name Pizza not found"):
        get_meal_by_name("Pizza")

def test_get_meal_by_deleted_name(mock_cursor):
    mock_cursor.fetchone.return_value = (1, "Pasta", "Italian", 12.99, "MED", True)
    with pytest.raises(ValueError, match="Meal with name Pasta has been deleted"):
        get_meal_by_name("Pasta")

def test_update_meal_stats(mock_cursor):
    mock_cursor.fetchone.return_value = [False]
    update_meal_stats(1, "win")

    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])
    assert actual_query == expected_query

    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]
    assert actual_arguments == (1,), f"Expected (1,), got {actual_arguments}"

def test_update_meal_stats_invalid_id(mock_cursor):
    mock_cursor.fetchone.return_value = None
    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        update_meal_stats(999, "win")

def test_update_meal_stats_invalid_stat(mock_cursor):
    mock_cursor.fetchone.return_value = [False]
    with pytest.raises(ValueError, match="Invalid result: invalid_stat. Expected 'win' or 'loss'."):
        update_meal_stats(1, "invalid_stat")

def test_update_meal_stats_deleted(mock_cursor):
    mock_cursor.fetchone.return_value = [True]
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, "win")
    
def test_get_leaderboard_sorted_by_wins(mock_cursor):
    """Test getting leaderboard sorted by wins."""
    # Simulate leaderboard entries sorted by wins
    mock_cursor.fetchall.return_value = [
        (1, "Pasta", "Italian", 12.99, "MED", 10, 8, 80.0),
        (2, "Pizza", "Italian", 15.99, "HIGH", 8, 5, 62.5),
        (3, "Burger", "American", 10.99, "LOW", 12, 4, 33.3)
    ]

    result = get_leaderboard(sort_by="wins")

    expected_result = [
        {"id": 1, "meal": "Pasta", "cuisine": "Italian", "price": 12.99, "difficulty": "MED", "battles": 10, "wins": 8, "win_pct": 8000.0},
        {"id": 2, "meal": "Pizza", "cuisine": "Italian", "price": 15.99, "difficulty": "HIGH", "battles": 8, "wins": 5, "win_pct": 6250},
        {"id": 3, "meal": "Burger", "cuisine": "American", "price": 10.99, "difficulty": "LOW", "battles": 12, "wins": 4, "win_pct": 3330}
    ]
    
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_sorted_by_win_pct(mock_cursor):
    """Test getting leaderboard sorted by win percentage."""
    # Simulate leaderboard entries sorted by win percentage
    mock_cursor.fetchall.return_value = [
        (1, "Burger", "American", 10.99, "LOW", 12, 9, 75.0),
        (2, "Pizza", "Italian", 15.99, "HIGH", 8, 5, 62.5),
        (3, "Pasta", "Italian", 12.99, "MED", 10, 6, 60.0)
    ]

    result = get_leaderboard(sort_by="win_pct")

    expected_result = [
        {"id": 1, "meal": "Burger", "cuisine": "American", "price": 10.99, "difficulty": "LOW", "battles": 12, "wins": 9, "win_pct": 7500},
        {"id": 2, "meal": "Pizza", "cuisine": "Italian", "price": 15.99, "difficulty": "HIGH", "battles": 8, "wins": 5, "win_pct": 6250},
        {"id": 3, "meal": "Pasta", "cuisine": "Italian", "price": 12.99, "difficulty": "MED", "battles": 10, "wins": 6, "win_pct": 6000}
    ]
    
    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0 ORDER BY win_pct DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_invalid_sort_by(mock_cursor):
    """Test getting leaderboard with an invalid sort_by parameter."""
    with pytest.raises(ValueError, match="Invalid sort_by parameter"):
        get_leaderboard(sort_by="invalid_param")

    mock_cursor.execute.assert_not_called()
