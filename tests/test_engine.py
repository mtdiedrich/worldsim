"""Tests for engine module."""

from worldsim.engine import new_run, step, get_summary_state
from worldsim.config import RUN_SEED, N_TICKS


def test_new_run_initialization():
    """Test creating a new run."""
    run_state = new_run()
    
    assert run_state["tick"] == 0
    assert run_state["status"] == "idle"
    assert "world" in run_state
    assert "memory" in run_state
    assert len(run_state["memory"]) == 2  # Two cultures


def test_new_run_with_custom_params():
    """Test creating a run with custom parameters."""
    run_state = new_run(run_seed=123, n_ticks=5)
    
    assert run_state["run_seed"] == 123
    assert run_state["n_ticks"] == 5


def test_step_increments_tick():
    """Test that step increments the tick."""
    run_state = new_run()
    
    assert run_state["tick"] == 0
    
    step(run_state)
    
    assert run_state["tick"] == 1


def test_step_changes_status():
    """Test that step changes status from idle to running."""
    run_state = new_run(n_ticks=2)
    
    assert run_state["status"] == "idle"
    
    step(run_state)
    
    assert run_state["status"] == "running"


def test_step_completes_run():
    """Test that step completes the run when n_ticks is reached."""
    run_state = new_run(n_ticks=1)
    
    step(run_state)
    
    assert run_state["tick"] == 1
    assert run_state["status"] == "complete"


def test_multiple_steps():
    """Test running multiple steps."""
    run_state = new_run(n_ticks=3)
    
    for i in range(3):
        step(run_state)
        assert run_state["tick"] == i + 1
    
    assert run_state["status"] == "complete"


def test_step_produces_events():
    """Test that steps produce events."""
    run_state = new_run(n_ticks=1)
    
    step(run_state)
    
    # Should have some events
    assert len(run_state["world"]["event_log"]) >= 0


def test_get_summary_state():
    """Test getting summary state."""
    run_state = new_run()
    step(run_state)
    
    summary = get_summary_state(run_state)
    
    assert "tick" in summary
    assert "status" in summary
    assert "cultures" in summary
    assert "regions" in summary
    assert "event_count" in summary
    
    assert summary["tick"] == 1


def test_summary_state_cultures():
    """Test summary state contains culture info."""
    run_state = new_run()
    step(run_state)
    
    summary = get_summary_state(run_state)
    
    assert "saltborn" in summary["cultures"]
    assert "ashfolk" in summary["cultures"]
    
    for culture_id, culture in summary["cultures"].items():
        assert "name" in culture
        assert "population" in culture
        assert "resources" in culture
        assert "tech_count" in culture
        assert "relations" in culture


def test_step_does_not_exceed_ticks():
    """Test that step stops at n_ticks."""
    run_state = new_run(n_ticks=2)
    
    step(run_state)
    step(run_state)
    step(run_state)
    
    # Should not exceed 2 ticks
    assert run_state["tick"] == 2
    assert run_state["status"] == "complete"
