"""Tests for the State Machine module."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from core.state_machine import (
    SystemState,
    StateTransition,
    StateMachine,
    StateChangeEvent,
    InvalidStateTransitionError
)


class TestSystemState:
    """Tests for SystemState enum."""
    
    def test_system_state_values(self):
        """Test that all expected system states exist."""
        expected_states = {
            "IDLE", "INITIALIZING", "RUNNING", "PAUSED", 
            "ERROR", "MAINTENANCE", "SHUTDOWN"
        }
        
        actual_states = {state.name for state in SystemState}
        assert actual_states == expected_states
    
    def test_system_state_string_values(self):
        """Test system state string values."""
        assert SystemState.IDLE.value == "idle"
        assert SystemState.RUNNING.value == "running"
        assert SystemState.ERROR.value == "error"


class TestStateTransition:
    """Tests for StateTransition class."""
    
    def test_transition_creation(self):
        """Test state transition creation."""
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start",
            condition=lambda: True
        )
        
        assert transition.from_state == SystemState.IDLE
        assert transition.to_state == SystemState.RUNNING
        assert transition.trigger == "start"
        assert transition.condition() == True
    
    def test_transition_without_condition(self):
        """Test state transition without condition."""
        transition = StateTransition(
            from_state=SystemState.RUNNING,
            to_state=SystemState.PAUSED,
            trigger="pause"
        )
        
        assert transition.condition is None
    
    def test_transition_is_valid(self):
        """Test transition validity check."""
        # Transition with condition that returns True
        valid_transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start",
            condition=lambda: True
        )
        
        assert valid_transition.is_valid()
        
        # Transition with condition that returns False
        invalid_transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start",
            condition=lambda: False
        )
        
        assert not invalid_transition.is_valid()
        
        # Transition without condition (always valid)
        no_condition_transition = StateTransition(
            from_state=SystemState.RUNNING,
            to_state=SystemState.PAUSED,
            trigger="pause"
        )
        
        assert no_condition_transition.is_valid()


class TestStateChangeEvent:
    """Tests for StateChangeEvent class."""
    
    def test_event_creation(self):
        """Test state change event creation."""
        event = StateChangeEvent(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start",
            metadata={"user": "test_user"}
        )
        
        assert event.from_state == SystemState.IDLE
        assert event.to_state == SystemState.RUNNING
        assert event.trigger == "start"
        assert event.metadata == {"user": "test_user"}
        assert isinstance(event.timestamp, datetime)
    
    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        event = StateChangeEvent(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start",
            metadata={"user": "test_user"}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["from_state"] == "idle"
        assert event_dict["to_state"] == "running"
        assert event_dict["trigger"] == "start"
        assert event_dict["metadata"] == {"user": "test_user"}
        assert "timestamp" in event_dict


class TestStateMachine:
    """Tests for StateMachine class."""
    
    @pytest.fixture
    def state_machine(self):
        """Create state machine instance for testing."""
        return StateMachine(initial_state=SystemState.IDLE)
    
    def test_state_machine_initialization(self, state_machine):
        """Test state machine initialization."""
        assert state_machine.current_state == SystemState.IDLE
        assert len(state_machine.transitions) == 0
        assert len(state_machine.event_history) == 0
        assert len(state_machine.listeners) == 0
    
    def test_add_transition(self, state_machine):
        """Test adding a state transition."""
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start"
        )
        
        state_machine.add_transition(transition)
        
        assert len(state_machine.transitions) == 1
        assert state_machine.transitions[0] == transition
    
    def test_add_multiple_transitions(self, state_machine):
        """Test adding multiple transitions."""
        transitions = [
            StateTransition(SystemState.IDLE, SystemState.RUNNING, "start"),
            StateTransition(SystemState.RUNNING, SystemState.PAUSED, "pause"),
            StateTransition(SystemState.PAUSED, SystemState.RUNNING, "resume"),
            StateTransition(SystemState.RUNNING, SystemState.IDLE, "stop")
        ]
        
        for transition in transitions:
            state_machine.add_transition(transition)
        
        assert len(state_machine.transitions) == 4
    
    def test_trigger_valid_transition(self, state_machine):
        """Test triggering a valid state transition."""
        # Add transition
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start"
        )
        state_machine.add_transition(transition)
        
        # Trigger transition
        result = state_machine.trigger("start")
        
        assert result == True
        assert state_machine.current_state == SystemState.RUNNING
        assert len(state_machine.event_history) == 1
        
        event = state_machine.event_history[0]
        assert event.from_state == SystemState.IDLE
        assert event.to_state == SystemState.RUNNING
        assert event.trigger == "start"
    
    def test_trigger_invalid_transition(self, state_machine):
        """Test triggering an invalid state transition."""
        # Add transition from IDLE to RUNNING
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start"
        )
        state_machine.add_transition(transition)
        
        # Try to trigger "pause" from IDLE (no such transition)
        with pytest.raises(InvalidStateTransitionError):
            state_machine.trigger("pause")
        
        # State should remain unchanged
        assert state_machine.current_state == SystemState.IDLE
        assert len(state_machine.event_history) == 0
    
    def test_trigger_with_failed_condition(self, state_machine):
        """Test triggering transition with failed condition."""
        # Add transition with condition that returns False
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start",
            condition=lambda: False
        )
        state_machine.add_transition(transition)
        
        # Trigger should fail due to condition
        with pytest.raises(InvalidStateTransitionError):
            state_machine.trigger("start")
        
        assert state_machine.current_state == SystemState.IDLE
    
    def test_trigger_with_metadata(self, state_machine):
        """Test triggering transition with metadata."""
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start"
        )
        state_machine.add_transition(transition)
        
        metadata = {"user": "test_user", "reason": "manual_start"}
        result = state_machine.trigger("start", metadata=metadata)
        
        assert result == True
        assert state_machine.current_state == SystemState.RUNNING
        
        event = state_machine.event_history[0]
        assert event.metadata == metadata
    
    def test_can_trigger(self, state_machine):
        """Test checking if a trigger is valid."""
        # Add transitions
        transitions = [
            StateTransition(SystemState.IDLE, SystemState.RUNNING, "start"),
            StateTransition(SystemState.RUNNING, SystemState.PAUSED, "pause"),
            StateTransition(SystemState.IDLE, SystemState.MAINTENANCE, "maintenance", 
                          condition=lambda: False)  # Condition that fails
        ]
        
        for transition in transitions:
            state_machine.add_transition(transition)
        
        # From IDLE state
        assert state_machine.can_trigger("start") == True
        assert state_machine.can_trigger("pause") == False  # Not valid from IDLE
        assert state_machine.can_trigger("maintenance") == False  # Condition fails
        assert state_machine.can_trigger("nonexistent") == False
    
    def test_get_valid_triggers(self, state_machine):
        """Test getting valid triggers for current state."""
        # Add transitions
        transitions = [
            StateTransition(SystemState.IDLE, SystemState.RUNNING, "start"),
            StateTransition(SystemState.IDLE, SystemState.MAINTENANCE, "maintenance"),
            StateTransition(SystemState.RUNNING, SystemState.PAUSED, "pause"),
            StateTransition(SystemState.IDLE, SystemState.ERROR, "error", 
                          condition=lambda: False)  # This should be excluded
        ]
        
        for transition in transitions:
            state_machine.add_transition(transition)
        
        valid_triggers = state_machine.get_valid_triggers()
        
        assert "start" in valid_triggers
        assert "maintenance" in valid_triggers
        assert "pause" not in valid_triggers  # Not valid from IDLE
        assert "error" not in valid_triggers  # Condition fails
    
    def test_add_listener(self, state_machine):
        """Test adding state change listener."""
        events_received = []
        
        def listener(event):
            events_received.append(event)
        
        state_machine.add_listener(listener)
        
        # Add transition and trigger it
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start"
        )
        state_machine.add_transition(transition)
        state_machine.trigger("start")
        
        # Listener should have been called
        assert len(events_received) == 1
        assert events_received[0].from_state == SystemState.IDLE
        assert events_received[0].to_state == SystemState.RUNNING
    
    def test_remove_listener(self, state_machine):
        """Test removing state change listener."""
        events_received = []
        
        def listener(event):
            events_received.append(event)
        
        state_machine.add_listener(listener)
        state_machine.remove_listener(listener)
        
        # Add transition and trigger it
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start"
        )
        state_machine.add_transition(transition)
        state_machine.trigger("start")
        
        # Listener should not have been called
        assert len(events_received) == 0
    
    def test_get_state_history(self, state_machine):
        """Test getting state change history."""
        # Add transitions
        transitions = [
            StateTransition(SystemState.IDLE, SystemState.RUNNING, "start"),
            StateTransition(SystemState.RUNNING, SystemState.PAUSED, "pause"),
            StateTransition(SystemState.PAUSED, SystemState.RUNNING, "resume")
        ]
        
        for transition in transitions:
            state_machine.add_transition(transition)
        
        # Trigger multiple transitions
        state_machine.trigger("start")
        state_machine.trigger("pause")
        state_machine.trigger("resume")
        
        history = state_machine.get_state_history()
        
        assert len(history) == 3
        assert history[0]["from_state"] == "idle"
        assert history[0]["to_state"] == "running"
        assert history[1]["from_state"] == "running"
        assert history[1]["to_state"] == "paused"
        assert history[2]["from_state"] == "paused"
        assert history[2]["to_state"] == "running"
    
    def test_get_state_history_with_limit(self, state_machine):
        """Test getting limited state change history."""
        # Add transition
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start"
        )
        state_machine.add_transition(transition)
        
        # Trigger multiple times (this would normally not be possible,
        # but we'll manually add events for testing)
        for i in range(5):
            event = StateChangeEvent(
                from_state=SystemState.IDLE,
                to_state=SystemState.RUNNING,
                trigger="start"
            )
            state_machine.event_history.append(event)
        
        # Get limited history
        history = state_machine.get_state_history(limit=3)
        
        assert len(history) == 3
    
    def test_get_current_state_info(self, state_machine):
        """Test getting current state information."""
        info = state_machine.get_current_state_info()
        
        assert info["current_state"] == "idle"
        assert "state_duration" in info
        assert "valid_triggers" in info
        assert isinstance(info["state_duration"], float)
    
    def test_reset_state_machine(self, state_machine):
        """Test resetting state machine."""
        # Add transition and trigger it
        transition = StateTransition(
            from_state=SystemState.IDLE,
            to_state=SystemState.RUNNING,
            trigger="start"
        )
        state_machine.add_transition(transition)
        state_machine.trigger("start")
        
        # Verify state changed
        assert state_machine.current_state == SystemState.RUNNING
        assert len(state_machine.event_history) == 1
        
        # Reset to initial state
        state_machine.reset()
        
        assert state_machine.current_state == SystemState.IDLE
        assert len(state_machine.event_history) == 0
    
    def test_complex_state_flow(self, state_machine):
        """Test a complex state flow scenario."""
        # Setup complete state machine
        transitions = [
            StateTransition(SystemState.IDLE, SystemState.INITIALIZING, "initialize"),
            StateTransition(SystemState.INITIALIZING, SystemState.RUNNING, "start"),
            StateTransition(SystemState.INITIALIZING, SystemState.ERROR, "error"),
            StateTransition(SystemState.RUNNING, SystemState.PAUSED, "pause"),
            StateTransition(SystemState.PAUSED, SystemState.RUNNING, "resume"),
            StateTransition(SystemState.RUNNING, SystemState.IDLE, "stop"),
            StateTransition(SystemState.PAUSED, SystemState.IDLE, "stop"),
            StateTransition(SystemState.ERROR, SystemState.IDLE, "reset"),
            StateTransition(SystemState.RUNNING, SystemState.MAINTENANCE, "maintenance"),
            StateTransition(SystemState.MAINTENANCE, SystemState.IDLE, "complete")
        ]
        
        for transition in transitions:
            state_machine.add_transition(transition)
        
        # Test normal flow: IDLE -> INITIALIZING -> RUNNING -> PAUSED -> RUNNING -> IDLE
        assert state_machine.current_state == SystemState.IDLE
        
        state_machine.trigger("initialize")
        assert state_machine.current_state == SystemState.INITIALIZING
        
        state_machine.trigger("start")
        assert state_machine.current_state == SystemState.RUNNING
        
        state_machine.trigger("pause")
        assert state_machine.current_state == SystemState.PAUSED
        
        state_machine.trigger("resume")
        assert state_machine.current_state == SystemState.RUNNING
        
        state_machine.trigger("stop")
        assert state_machine.current_state == SystemState.IDLE
        
        # Verify history
        assert len(state_machine.event_history) == 5


if __name__ == "__main__":
    pytest.main([__file__])