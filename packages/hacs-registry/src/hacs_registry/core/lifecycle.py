"""
Lifecycle Management Following SOLID Principles

This module provides lifecycle management for registry components,
following healthcare-specific requirements and SOLID principles.

SOLID Compliance:
- S: Single Responsibility - each class manages one aspect of lifecycle
- O: Open/Closed - extensible for new lifecycle patterns
- L: Liskov Substitution - all lifecycle managers are interchangeable
- I: Interface Segregation - focused lifecycle interfaces
- D: Dependency Inversion - depends on abstractions

Healthcare Lifecycle Patterns:
    📋 Resource Lifecycle - Draft → Review → Published → Deprecated → Retired
    🤖 Agent Lifecycle - Created → Configured → Testing → Production → Retired
    🔐 Permission Lifecycle - Requested → Approved → Active → Suspended → Revoked
    📊 Audit Lifecycle - Created → Reviewed → Archived
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field

from .base import Entity, EntityId, DomainEvent, EventPublisher
from .events import RegistryEvent

logger = logging.getLogger(__name__)


class LifecycleState(str, Enum):
    """Standard lifecycle states across all registry components."""
    
    # Creation states
    DRAFT = "draft"
    PENDING = "pending"
    
    # Review states  
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    
    # Active states
    ACTIVE = "active"
    PUBLISHED = "published"
    DEPLOYED = "deployed"
    
    # Transition states
    UPDATING = "updating"
    TESTING = "testing"
    STAGING = "staging"
    
    # End states
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"
    RETIRED = "retired"
    ARCHIVED = "archived"
    
    # Error states
    FAILED = "failed"
    ERROR = "error"


class LifecycleAction(str, Enum):
    """Actions that can trigger lifecycle transitions."""
    
    CREATE = "create"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    DEPLOY = "deploy"
    UPDATE = "update"
    TEST = "test"
    PROMOTE = "promote"
    DEPRECATE = "deprecate"
    SUSPEND = "suspend"
    RETIRE = "retire"
    ARCHIVE = "archive"
    RESTORE = "restore"
    FAIL = "fail"


@dataclass
class LifecycleTransition:
    """
    Represents a lifecycle state transition.
    
    SOLID Compliance:
    - S: Single responsibility - represents one state change
    - L: Liskov substitution - all transitions behave consistently
    """
    
    from_state: LifecycleState
    to_state: LifecycleState
    action: LifecycleAction
    actor_id: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the transition."""
        if self.from_state == self.to_state:
            raise ValueError("Cannot transition to the same state")


@dataclass
class LifecycleRule:
    """
    Defines rules for lifecycle transitions.
    
    SOLID Compliance:
    - S: Single responsibility - encapsulates one transition rule
    - O: Open/closed - new rules can be added without modification
    """
    
    name: str
    description: str
    from_states: Set[LifecycleState]
    to_state: LifecycleState
    action: LifecycleAction
    required_permissions: List[str] = field(default_factory=list)
    conditions: List[Callable[[Entity], bool]] = field(default_factory=list)
    auto_transition: bool = False
    timeout_hours: Optional[int] = None
    
    def can_transition(self, entity: Entity, current_state: LifecycleState) -> bool:
        """Check if transition is allowed for the given entity."""
        if current_state not in self.from_states:
            return False
        
        # Check all conditions
        for condition in self.conditions:
            if not condition(entity):
                return False
        
        return True
    
    def is_expired(self, transition_time: datetime) -> bool:
        """Check if this transition has expired (for timeout rules)."""
        if not self.timeout_hours:
            return False
        
        expiry_time = transition_time + timedelta(hours=self.timeout_hours)
        return datetime.now(timezone.utc) > expiry_time


class LifecycleStateChangedEvent(RegistryEvent):
    """Event fired when entity lifecycle state changes."""
    
    def __init__(self, entity_id: EntityId, transition: LifecycleTransition, **kwargs):
        super().__init__(entity_id, **kwargs)
        self.transition = transition
        self.entity_type = kwargs.get('entity_type', 'unknown')
    
    @property
    def event_type(self) -> str:
        return "lifecycle.state.changed"


class LifecycleManager(ABC):
    """
    Abstract base class for lifecycle management.
    
    SOLID Compliance:
    - S: Single responsibility - manages entity lifecycle
    - O: Open/closed - extensible for specific entity types
    - L: Liskov substitution - all managers are interchangeable
    - I: Interface segregation - focused lifecycle interface
    """
    
    def __init__(self, event_publisher: Optional[EventPublisher] = None):
        self.event_publisher = event_publisher
        self.logger = logging.getLogger(self.__class__.__name__)
        self._rules: Dict[LifecycleAction, List[LifecycleRule]] = {}
        self._state_history: Dict[EntityId, List[LifecycleTransition]] = {}
        self._current_states: Dict[EntityId, LifecycleState] = {}
        
        # Initialize with default rules
        self._initialize_rules()
    
    @abstractmethod
    def _initialize_rules(self):
        """Initialize lifecycle rules for this manager type."""
        pass
    
    @property
    @abstractmethod
    def entity_type(self) -> str:
        """Type of entity this manager handles."""
        pass
    
    def add_rule(self, rule: LifecycleRule):
        """Add a lifecycle rule."""
        if rule.action not in self._rules:
            self._rules[rule.action] = []
        self._rules[rule.action].append(rule)
        self.logger.debug(f"Added lifecycle rule: {rule.name}")
    
    def get_current_state(self, entity_id: EntityId) -> Optional[LifecycleState]:
        """Get the current state of an entity."""
        return self._current_states.get(entity_id)
    
    def get_state_history(self, entity_id: EntityId) -> List[LifecycleTransition]:
        """Get the state transition history for an entity."""
        return self._state_history.get(entity_id, []).copy()
    
    async def initialize_entity(self, entity: Entity, initial_state: LifecycleState = LifecycleState.DRAFT):
        """Initialize lifecycle tracking for an entity."""
        self._current_states[entity.id] = initial_state
        self._state_history[entity.id] = []
        
        self.logger.info(f"Initialized {self.entity_type} {entity.id} in state {initial_state}")
    
    async def can_transition(self, entity: Entity, action: LifecycleAction, actor_id: Optional[str] = None) -> bool:
        """Check if an entity can perform the given action."""
        current_state = self.get_current_state(entity.id)
        if not current_state:
            return False
        
        rules = self._rules.get(action, [])
        for rule in rules:
            if rule.can_transition(entity, current_state):
                # TODO: Check permissions if actor_id provided
                return True
        
        return False
    
    async def transition(
        self, 
        entity: Entity, 
        action: LifecycleAction, 
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Attempt to transition an entity's lifecycle state."""
        
        current_state = self.get_current_state(entity.id)
        if not current_state:
            raise ValueError(f"Entity {entity.id} not initialized in lifecycle manager")
        
        # Find applicable rule
        applicable_rule = None
        rules = self._rules.get(action, [])
        
        for rule in rules:
            if rule.can_transition(entity, current_state):
                applicable_rule = rule
                break
        
        if not applicable_rule:
            self.logger.warning(f"No rule allows {action} from {current_state} for {entity.id}")
            return False
        
        # Create transition
        transition = LifecycleTransition(
            from_state=current_state,
            to_state=applicable_rule.to_state,
            action=action,
            actor_id=actor_id,
            reason=reason,
            metadata=metadata or {}
        )
        
        # Update state
        self._current_states[entity.id] = applicable_rule.to_state
        if entity.id not in self._state_history:
            self._state_history[entity.id] = []
        self._state_history[entity.id].append(transition)
        
        # Update entity timestamp
        entity.update_timestamp()
        
        # Publish event
        if self.event_publisher:
            event = LifecycleStateChangedEvent(
                entity.id, 
                transition,
                entity_type=self.entity_type,
                actor_id=actor_id
            )
            await self.event_publisher.publish(event)
        
        self.logger.info(f"{self.entity_type} {entity.id} transitioned: {current_state} → {applicable_rule.to_state}")
        return True
    
    async def get_available_actions(self, entity: Entity) -> List[LifecycleAction]:
        """Get list of actions available for an entity in its current state."""
        current_state = self.get_current_state(entity.id)
        if not current_state:
            return []
        
        available_actions = []
        for action, rules in self._rules.items():
            for rule in rules:
                if rule.can_transition(entity, current_state):
                    available_actions.append(action)
                    break
        
        return available_actions
    
    async def check_expired_transitions(self) -> List[EntityId]:
        """Check for entities with expired lifecycle transitions."""
        expired_entities = []
        
        for entity_id, transitions in self._state_history.items():
            if not transitions:
                continue
            
            last_transition = transitions[-1]
            current_state = self._current_states.get(entity_id)
            
            # Find rules with timeouts for current state
            for rules in self._rules.values():
                for rule in rules:
                    if (rule.to_state == current_state and 
                        rule.is_expired(last_transition.timestamp)):
                        expired_entities.append(entity_id)
                        break
        
        return expired_entities


class ResourceLifecycleManager(LifecycleManager):
    """
    Lifecycle manager for healthcare resources.
    
    SOLID Compliance:
    - S: Single responsibility - manages resource lifecycle specifically
    """
    
    @property
    def entity_type(self) -> str:
        return "Resource"
    
    def _initialize_rules(self):
        """Initialize healthcare resource lifecycle rules."""
        
        # Draft → Review
        self.add_rule(LifecycleRule(
            name="submit_for_review",
            description="Submit draft resource for review",
            from_states={LifecycleState.DRAFT},
            to_state=LifecycleState.REVIEW,
            action=LifecycleAction.SUBMIT
        ))
        
        # Review → Approved/Rejected
        self.add_rule(LifecycleRule(
            name="approve_resource",
            description="Approve resource after review",
            from_states={LifecycleState.REVIEW},
            to_state=LifecycleState.APPROVED,
            action=LifecycleAction.APPROVE,
            required_permissions=["resource.approve"]
        ))
        
        self.add_rule(LifecycleRule(
            name="reject_resource",
            description="Reject resource after review",
            from_states={LifecycleState.REVIEW},
            to_state=LifecycleState.REJECTED,
            action=LifecycleAction.REJECT,
            required_permissions=["resource.approve"]
        ))
        
        # Approved → Published
        self.add_rule(LifecycleRule(
            name="publish_resource",
            description="Publish approved resource",
            from_states={LifecycleState.APPROVED},
            to_state=LifecycleState.PUBLISHED,
            action=LifecycleAction.PUBLISH,
            required_permissions=["resource.publish"]
        ))
        
        # Published → Deprecated
        self.add_rule(LifecycleRule(
            name="deprecate_resource",
            description="Deprecate published resource",
            from_states={LifecycleState.PUBLISHED},
            to_state=LifecycleState.DEPRECATED,
            action=LifecycleAction.DEPRECATE,
            required_permissions=["resource.deprecate"]
        ))
        
        # Deprecated → Retired
        self.add_rule(LifecycleRule(
            name="retire_resource",
            description="Retire deprecated resource",
            from_states={LifecycleState.DEPRECATED},
            to_state=LifecycleState.RETIRED,
            action=LifecycleAction.RETIRE,
            required_permissions=["resource.retire"],
            timeout_hours=24 * 30  # 30 days grace period
        ))
        
        # Emergency transitions
        self.add_rule(LifecycleRule(
            name="emergency_suspend",
            description="Emergency suspension of resource",
            from_states={LifecycleState.PUBLISHED, LifecycleState.DEPRECATED},
            to_state=LifecycleState.SUSPENDED,
            action=LifecycleAction.SUSPEND,
            required_permissions=["resource.emergency"]
        ))


class AgentLifecycleManager(LifecycleManager):
    """
    Lifecycle manager for AI agents.
    
    SOLID Compliance:
    - S: Single responsibility - manages agent lifecycle specifically
    """
    
    @property
    def entity_type(self) -> str:
        return "Agent"
    
    def _initialize_rules(self):
        """Initialize AI agent lifecycle rules."""
        
        # Draft → Testing
        self.add_rule(LifecycleRule(
            name="start_testing",
            description="Start agent testing phase",
            from_states={LifecycleState.DRAFT},
            to_state=LifecycleState.TESTING,
            action=LifecycleAction.TEST
        ))
        
        # Testing → Staging
        self.add_rule(LifecycleRule(
            name="promote_to_staging",
            description="Promote agent to staging environment",
            from_states={LifecycleState.TESTING},
            to_state=LifecycleState.STAGING,
            action=LifecycleAction.PROMOTE,
            required_permissions=["agent.promote"]
        ))
        
        # Staging → Production
        self.add_rule(LifecycleRule(
            name="deploy_to_production",
            description="Deploy agent to production",
            from_states={LifecycleState.STAGING},
            to_state=LifecycleState.DEPLOYED,
            action=LifecycleAction.DEPLOY,
            required_permissions=["agent.deploy"]
        ))
        
        # Production → Retired
        self.add_rule(LifecycleRule(
            name="retire_agent",
            description="Retire production agent",
            from_states={LifecycleState.DEPLOYED},
            to_state=LifecycleState.RETIRED,
            action=LifecycleAction.RETIRE,
            required_permissions=["agent.retire"]
        ))
        
        # Emergency suspension
        self.add_rule(LifecycleRule(
            name="emergency_suspend_agent",
            description="Emergency suspension of agent",
            from_states={LifecycleState.DEPLOYED, LifecycleState.STAGING},
            to_state=LifecycleState.SUSPENDED,
            action=LifecycleAction.SUSPEND,
            required_permissions=["agent.emergency"]
        ))


class IAMLifecycleManager(LifecycleManager):
    """
    Lifecycle manager for IAM permissions and actors.
    
    SOLID Compliance:
    - S: Single responsibility - manages IAM lifecycle specifically
    """
    
    @property
    def entity_type(self) -> str:
        return "IAM"
    
    def _initialize_rules(self):
        """Initialize IAM lifecycle rules."""
        
        # Pending → Active
        self.add_rule(LifecycleRule(
            name="activate_permission",
            description="Activate pending permission",
            from_states={LifecycleState.PENDING},
            to_state=LifecycleState.ACTIVE,
            action=LifecycleAction.APPROVE,
            required_permissions=["iam.approve"]
        ))
        
        # Active → Suspended
        self.add_rule(LifecycleRule(
            name="suspend_permission",
            description="Suspend active permission",
            from_states={LifecycleState.ACTIVE},
            to_state=LifecycleState.SUSPENDED,
            action=LifecycleAction.SUSPEND,
            required_permissions=["iam.suspend"]
        ))
        
        # Suspended → Active (restore)
        self.add_rule(LifecycleRule(
            name="restore_permission",
            description="Restore suspended permission",
            from_states={LifecycleState.SUSPENDED},
            to_state=LifecycleState.ACTIVE,
            action=LifecycleAction.RESTORE,
            required_permissions=["iam.restore"]
        ))
        
        # Any → Retired (revoke)
        self.add_rule(LifecycleRule(
            name="revoke_permission",
            description="Revoke permission permanently",
            from_states={LifecycleState.ACTIVE, LifecycleState.SUSPENDED, LifecycleState.PENDING},
            to_state=LifecycleState.RETIRED,
            action=LifecycleAction.RETIRE,
            required_permissions=["iam.revoke"]
        ))


# Factory for creating lifecycle managers

class LifecycleManagerFactory:
    """
    Factory for creating lifecycle managers.
    
    SOLID Compliance:
    - S: Single responsibility - creates lifecycle managers
    - O: Open/closed - new manager types can be added
    - D: Dependency inversion - depends on abstractions
    """
    
    _managers = {
        "Resource": ResourceLifecycleManager,
        "Agent": AgentLifecycleManager,
        "IAM": IAMLifecycleManager,
    }
    
    @classmethod
    def create(cls, entity_type: str, event_publisher: Optional[EventPublisher] = None) -> LifecycleManager:
        """Create a lifecycle manager for the given entity type."""
        if entity_type not in cls._managers:
            raise ValueError(f"No lifecycle manager for entity type: {entity_type}")
        
        manager_class = cls._managers[entity_type]
        return manager_class(event_publisher)
    
    @classmethod
    def register_manager(cls, entity_type: str, manager_class: type):
        """Register a new lifecycle manager type."""
        cls._managers[entity_type] = manager_class
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported entity types."""
        return list(cls._managers.keys())