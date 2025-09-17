import pytest
from aicconnector import stage

def test_stage_module_import():
    assert hasattr(stage, "Stage") or hasattr(stage, "run_stage")

# Add more tests for stage functions/classes if needed
