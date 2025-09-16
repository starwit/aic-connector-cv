import pytest

def test_rediswriter_import():
    try:
        from aicconnector.aicconnector import AicConnector
    except ImportError as e:
        pytest.fail(f"Failed to import AicConnector: {e}")

    assert AicConnector is not None, "AicConnector should be imported successfully"