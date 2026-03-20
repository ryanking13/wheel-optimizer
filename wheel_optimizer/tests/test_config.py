from wheel_optimizer.config import OptimizerConfig


def test_defaults():
    config = OptimizerConfig()
    assert config.disable_all is False
    assert config.remove_docstrings is False


def test_explicit_values():
    config = OptimizerConfig(disable_all=True, remove_docstrings=True)
    assert config.disable_all is True
    assert config.remove_docstrings is True


def test_frozen():
    config = OptimizerConfig()
    try:
        config.disable_all = True  # type: ignore[misc]
        raise AssertionError("Expected FrozenInstanceError")
    except AttributeError:
        pass
