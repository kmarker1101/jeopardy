import pytest
from unittest.mock import Mock, patch
from rich.console import Console
from rich.prompt import Prompt
import requests
from jeopardy_game import JeopardyGame

@pytest.fixture
def game():
    return JeopardyGame()

@pytest.fixture
def mock_console():
    with patch('rich.console.Console') as mock:
        yield mock

@pytest.fixture
def mock_requests():
    with patch('requests.post') as mock:
        yield mock

def test_game_initialization(game):
    """Test that game initializes with correct default values"""
    assert isinstance(game.console, Console)
    assert "Science" in game.categories
    assert 100 in game.points
    assert game.score == 0
    assert isinstance(game.board, dict)

def test_generate_question_success(game, mock_requests):
    """Test successful question generation"""
    mock_response = Mock()
    mock_response.json.return_value = {
        'response': 'What is the capital of France?\nParis'
    }
    mock_requests.return_value = mock_response

    result = game.generate_question("Geography", 100)
    assert isinstance(result, dict)
    assert "question" in result
    assert "answer" in result
    assert result["answer"] == "paris"

def test_generate_question_error(game, mock_requests):
    """Test question generation with API error"""
    mock_requests.side_effect = requests.exceptions.RequestException()

    result = game.generate_question("Geography", 100)
    assert isinstance(result, dict)
    assert "question" in result
    assert "answer" in result
    assert result["answer"] == "backup"

def test_answer_validation(game):
    """Test different answer matching scenarios"""
    test_cases = [
        # Exact matches
        ("paris", "paris", True),
        ("mount everest", "mount everest", True),

        # Different cases
        ("Paris", "paris", True),
        ("MOUNT EVEREST", "mount everest", True),

        # With/without articles
        ("the eiffel tower", "eiffel tower", True),
        ("a red planet", "red planet", True),

        # Similar answers
        ("mt everest", "mount everest", True),
        ("george washington", "president washington", False),

        # Wrong answers
        ("completely wrong", "correct answer", False),
        ("mars", "venus", False),
        ("pacific ocean", "atlantic ocean", False),

        # Partial matches that should fail
        ("new", "new york city", False),
        ("cat", "category", False),

        # With extra spaces
        ("  paris  ", "paris", True),
        ("mount   everest", "mount everest", True),

        # Almost correct
        ("mount everst", "mount everest", True),
        ("mount everust", "mount everest", True),
    ]

    for player_answer, correct_answer, expected in test_cases:
        result = game.check_answer(player_answer, correct_answer)
        assert result == expected, \
            f"Failed for player_answer='{player_answer}', " \
            f"correct_answer='{correct_answer}', " \
            f"expected={expected}, got={result}"


@pytest.mark.parametrize("points,expected", [
    (100, True),
    (200, True),
    (300, True),
    (400, True),
    (500, True),
    (600, False)
])
def test_valid_points(points, expected):
    """Test that only valid point values are accepted"""
    game = JeopardyGame()
    assert (points in game.points) == expected

def test_score_update(game):
    """Test score updates correctly"""
    initial_score = game.score

    # Simulate correct answer
    game.score += 100
    assert game.score == initial_score + 100

    # Simulate wrong answer
    game.score -= 200
    assert game.score == initial_score - 100

def test_board_initialization(game):
    """Test board structure after initialization"""
    game.board = {}  # Clear any existing board

    # Mock the generate_question method to avoid API calls
    with patch.object(game, 'generate_question') as mock_generate:
        mock_generate.return_value = {
            "question": "Test question",
            "answer": "Test answer"
        }

        game.initialize_board()

        # Check board structure
        assert len(game.board) == len(game.categories)
        for category in game.categories:
            assert category in game.board
            assert len(game.board[category]) == len(game.points)
            for points in game.points:
                assert points in game.board[category]
                assert "question" in game.board[category][points]
                assert "answer" in game.board[category][points]
                assert "answered" in game.board[category][points]
                assert game.board[category][points]["answered"] == False

if __name__ == "__main__":
    pytest.main([__file__])
