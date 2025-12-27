from src.domain.rokda import reward_rokda


def test_reward_rokda_positive_value():
    result = reward_rokda(10)
    assert result > 10
    assert isinstance(result, float)


def test_reward_rokda_zero():
    result = reward_rokda(0)
    assert result > 0
    assert isinstance(result, float)


def test_reward_rokda_negative_value():
    result = reward_rokda(-5)
    assert result > 0
    assert isinstance(result, float)


def test_reward_rokda_none():
    result = reward_rokda(None)
    assert result > 0
    assert isinstance(result, float)


def test_reward_rokda_large_value():
    result = reward_rokda(1000)
    assert result >= 1000
    assert isinstance(result, float)
