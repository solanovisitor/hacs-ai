# ADR-003: Protocol-First Design Pattern

## Status
**Accepted** - Implemented across all HACS packages

## Context
HACS needs to support multiple AI frameworks (LangChain, LangGraph, OpenAI, Anthropic), healthcare standards (FHIR), and integration patterns (MCP, REST APIs) while maintaining clean abstractions and testability. Traditional inheritance hierarchies become rigid and difficult to extend as the system grows.

## Decision
We will adopt a **Protocol-First Design Pattern** using Python's `typing.Protocol` to define interfaces before implementations, enabling flexible composition and runtime type checking.

## Architecture Overview

### Core Design Principles

#### 1. Define Protocols Before Implementations
```python
# Define the interface first
@runtime_checkable
class PersistenceProvider(Protocol):
    async def create_resource(self, resource: BaseResource) -> str: ...
    async def get_resource(self, resource_type: str, resource_id: str) -> Optional[BaseResource]: ...
    async def update_resource(self, resource: BaseResource) -> bool: ...
    async def delete_resource(self, resource_type: str, resource_id: str) -> bool: ...

# Implement later
class PostgreSQLAdapter(PersistenceProvider):
    async def create_resource(self, resource: BaseResource) -> str:
        # Actual implementation
        pass
```

#### 2. Compositional Interface Design
```python
# Small, focused protocols
@runtime_checkable
class Identifiable(Protocol):
    @property
    def id(self) -> str: ...

@runtime_checkable
class Timestamped(Protocol):
    @property
    def created_at(self) -> datetime: ...
    @property
    def updated_at(self) -> datetime: ...

@runtime_checkable
class Versioned(Protocol):
    @property
    def version(self) -> str: ...

# Compose larger interfaces
@runtime_checkable
class ClinicalEntity(Identifiable, Timestamped, Versioned, Protocol):
    def validate_clinical_data(self) -> bool: ...
```

#### 3. Runtime Type Checking
```python
def process_clinical_entity(entity: Any) -> bool:
    if isinstance(entity, ClinicalEntity):
        return entity.validate_clinical_data()
    raise TypeError(f"Expected ClinicalEntity, got {type(entity)}")
```

## Key Protocol Categories

### 1. Infrastructure Protocols
Core system abstractions that enable dependency injection and testing.

```python
@runtime_checkable
class LLMProvider(Protocol):
    def generate_response(self, prompt: str, **kwargs) -> str: ...
    def generate_structured_response(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]: ...

@runtime_checkable
class VectorStore(Protocol):
    async def add_vectors(self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]) -> None: ...
    async def similarity_search(self, query_vector: List[float], k: int = 10) -> List[Dict[str, Any]]: ...

@runtime_checkable
class AgentFramework(Protocol):
    def create_agent(self, config: Dict[str, Any]) -> Any: ...
    def run_agent(self, agent: Any, input_data: Dict[str, Any]) -> Dict[str, Any]: ...
```

### 2. Healthcare Domain Protocols
Healthcare-specific abstractions for clinical workflows and FHIR compliance.

```python
@runtime_checkable
class ClinicalResource(Protocol):
    def to_fhir(self) -> Dict[str, Any]: ...
    def from_fhir(self, fhir_data: Dict[str, Any]) -> None: ...
    def validate_clinical_data(self) -> bool: ...

@runtime_checkable
class ClinicalReasoning(Protocol):
    def analyze_clinical_data(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]: ...

@runtime_checkable
class WorkflowEngine(Protocol):
    async def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]: ...
    def validate_workflow(self, workflow_definition: Dict[str, Any]) -> bool: ...
```

### 3. Tool and Registry Protocols
Abstractions for tool registration and discovery.

```python
@runtime_checkable
class ToolRegistry(Protocol):
    def register_tool(self, func: Callable, metadata: ToolMetadata) -> None: ...
    def get_tool(self, name: str) -> Optional[Callable]: ...
    def list_tools(self, category: Optional[str] = None) -> List[str]: ...

@runtime_checkable
class ToolDecorator(Protocol):
    def __call__(self, func: F) -> F: ...
```

### 4. Memory and Context Protocols
AI memory management and context handling.

```python
@runtime_checkable
class MemoryStore(Protocol):
    async def store_memory(self, memory: MemoryBlock) -> str: ...
    async def retrieve_memories(self, query: str, limit: int = 10) -> List[MemoryBlock]: ...
    async def consolidate_memories(self, memory_ids: List[str]) -> MemoryBlock: ...

@runtime_checkable
class ActorCapability(Protocol):
    def can_perform_action(self, action: str, resource: str) -> bool: ...
    def get_permissions(self) -> List[str]: ...
```

## Implementation Patterns

### 1. Adapter Pattern with Protocols
```python
class LangChainAdapter:
    """Adapts LangChain components to HACS protocols."""
    
    def __init__(self, langchain_llm):
        self._llm = langchain_llm
        
    def generate_response(self, prompt: str, **kwargs) -> str:
        return self._llm.invoke(prompt)
    
    def generate_structured_response(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        structured_llm = self._llm.with_structured_output(schema)
        return structured_llm.invoke(prompt)

# Verify protocol compliance at runtime
assert isinstance(LangChainAdapter(llm), LLMProvider)
```

### 2. Dependency Injection with Protocols
```python
def execute_clinical_analysis(
    data: Dict[str, Any],
    reasoning_engine: ClinicalReasoning,  # Protocol, not concrete class
    persistence: PersistenceProvider,     # Protocol, not concrete class
    actor: ActorCapability               # Protocol, not concrete class
) -> Dict[str, Any]:
    
    if not actor.can_perform_action("analyze", "clinical_data"):
        raise PermissionError("Insufficient permissions")
    
    analysis = reasoning_engine.analyze_clinical_data(data)
    
    # Store results
    result_id = await persistence.create_resource(
        create_analysis_resource(analysis)
    )
    
    return {"analysis": analysis, "result_id": result_id}
```

### 3. Protocol Validation
```python
def validate_clinical_resource(resource: Any) -> bool:
    """Validate that a resource implements the ClinicalResource protocol."""
    if not isinstance(resource, ClinicalResource):
        return False
    
    try:
        # Test protocol methods
        fhir_data = resource.to_fhir()
        is_valid = resource.validate_clinical_data()
        return isinstance(fhir_data, dict) and isinstance(is_valid, bool)
    except (AttributeError, TypeError):
        return False
```

## Framework Integration Examples

### 1. LangChain Integration
```python
class HACSLangChainTool:
    """Convert HACS tools to LangChain tools using protocols."""
    
    def __init__(self, hacs_tool: Callable, registry: ToolRegistry):
        self.hacs_tool = hacs_tool
        self.registry = registry
    
    def _run(self, **kwargs) -> str:
        return self.hacs_tool(**kwargs)
    
    async def _arun(self, **kwargs) -> str:
        if asyncio.iscoroutinefunction(self.hacs_tool):
            return await self.hacs_tool(**kwargs)
        return self.hacs_tool(**kwargs)
```

### 2. MCP Integration
```python
class MCPToolAdapter:
    """Adapt HACS tools to MCP protocol using tool protocols."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    async def use_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.registry.get_tool(name)
        if not tool:
            raise ValueError(f"Tool {name} not found")
        
        if asyncio.iscoroutinefunction(tool):
            result = await tool(**arguments)
        else:
            result = tool(**arguments)
        
        return {"result": result}
```

## Benefits of Protocol-First Design

### 1. Flexible Composition
- Mix and match implementations
- Runtime polymorphism
- Easy testing with mock objects

### 2. Framework Independence
- Tools work across multiple AI frameworks
- Easy migration between implementations
- Vendor lock-in prevention

### 3. Enhanced Testing
```python
class MockLLMProvider:
    """Mock implementation for testing."""
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        return f"Mock response to: {prompt}"
    
    def generate_structured_response(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        return {"mock": "structured_response"}

# Use in tests
mock_llm = MockLLMProvider()
assert isinstance(mock_llm, LLMProvider)  # Validates protocol compliance
```

### 4. Clear API Contracts
- Explicit interface definitions
- Self-documenting code
- IDE support and type checking

## Protocol Design Guidelines

### 1. Keep Protocols Small and Focused
```python
# Good: Small, focused protocol
@runtime_checkable
class Identifiable(Protocol):
    @property
    def id(self) -> str: ...

# Avoid: Large, monolithic protocol
class EverythingProtocol(Protocol):
    def method1(self): ...
    def method2(self): ...
    # ... 20 more methods
```

### 2. Use Composition Over Complex Inheritance
```python
# Good: Compositional design
class ClinicalEntity(Identifiable, Timestamped, ClinicalResource, Protocol):
    pass

# Avoid: Deep inheritance hierarchies
class ComplexClinicalEntity(BaseClinicalEntity, TimestampMixin, ...):
    pass
```

### 3. Provide Default Implementations Where Appropriate
```python
@runtime_checkable
class Validatable(Protocol):
    def validate(self) -> bool: ...
    
    def is_valid(self) -> bool:
        """Default implementation using validate()."""
        try:
            return self.validate()
        except Exception:
            return False
```

## Migration Strategy

### Phase 1: Core Protocols ✅
- Infrastructure protocols (LLMProvider, VectorStore, PersistenceProvider)
- Basic healthcare protocols (ClinicalResource, Identifiable)
- Tool registry protocols

### Phase 2: Advanced Protocols ✅
- Clinical reasoning protocols
- Memory management protocols
- Actor capability protocols

### Phase 3: Framework Integration ✅
- LangChain adapter protocols
- MCP integration protocols
- OpenAI/Anthropic adapter protocols

## Performance Considerations

### 1. Protocol Checking Overhead
- `isinstance()` checks have minimal overhead
- Protocol methods use standard Python call mechanisms
- No significant performance impact in practice

### 2. Memory Usage
- Protocols don't add memory overhead
- Same memory usage as regular Python objects
- Duck typing benefits without costs

## Consequences

### Positive
- **Flexibility**: Easy to swap implementations
- **Testability**: Mock objects naturally implement protocols
- **Framework Independence**: Not tied to specific AI frameworks
- **Type Safety**: Runtime and static type checking
- **Documentation**: Protocols serve as API documentation

### Negative
- **Learning Curve**: Developers need to understand protocols
- **Verbosity**: More interface definitions upfront
- **Runtime Checking**: Additional isinstance() calls

## Related Decisions
- [ADR-001: SOLID Principles Compliance](ADR-001-SOLID-principles-compliance.md)
- [ADR-004: Dependency Injection Container](ADR-004-dependency-injection.md)

## References
- [PEP 544 – Protocols](https://peps.python.org/pep-0544/)
- [Python typing.Protocol documentation](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [Structural Subtyping](https://mypy.readthedocs.io/en/stable/protocols.html)

---
**Date**: 2025-08-04  
**Author**: HACS Architecture Team  
**Reviewers**: Technical Architecture Board