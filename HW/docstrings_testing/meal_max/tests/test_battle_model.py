import pytest

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal


@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

# @pytest.fixture
# def mock_update_play_count(mocker):
#     """Mock the update_play_count function for testing purposes."""
#     return mocker.patch("music_collection.models.playlist_model.update_play_count")

"""Fixtures providing sample meals for the tests."""
@pytest.fixture
def sample_meal1():
    return Meal(1, 'Meal 1', 'Cuisine 1', 1.99, 'LOW')

@pytest.fixture
def sample_meal2():
    return Meal(2, 'Meal 2', 'Cuisine 2', 9.99, 'HIGH')

@pytest.fixture
def sample_combatants(sample_meal1, sample_meal2):
    return [sample_meal1, sample_meal2]

##################################################
# battle Test Cases
##################################################

def test_battle(battle_model, sample_combatants):
    """Test battle function."""
    battle_model.combatants.extend(sample_combatants)
    winner = battle_model.battle()
    assert len(battle_model.combatants) == 1
    assert winner == 'Meal 1' or winner == 'Meal 2'

def test_battle_empty_combatants_list(battle_model):
    """Test error when calling battle on an empty list."""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

##################################################
# clear_combatants Test Cases
##################################################

def test_clear_combatants(battle_model, sample_combatants):
    """Test clear_combatants function."""
    battle_model.combatants.extend(sample_combatants)
    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0

##################################################
# get_battle_score Test Cases
##################################################

def test_get_battle_score(battle_model, sample_meal1):
    """Test get_battle_score function."""
    score = battle_model.get_battle_score(sample_meal1)
    assert score == 14.91

##################################################
# get_combatants Test Cases
##################################################

def test_get_combatants(battle_model, sample_combatants):
    """Test get_combatants function."""
    battle_model.combatants.extend(sample_combatants)
    combatants = battle_model.get_combatants()
    assert combatants == sample_combatants

##################################################
# prep_combatant Test Cases
##################################################

def test_prep_combatant(battle_model, sample_meal1):
    """Test adding a meal to the combatants list."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == 'Meal 1'

def test_add_meal_to_full_combatants_list(battle_model, sample_combatants, sample_meal1):
    """Test error when adding a meal to a full combatants list."""
    battle_model.combatants.extend(sample_combatants)
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal1)
