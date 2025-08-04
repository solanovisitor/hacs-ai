# HACS Infrastructure

Infrastructure components for HACS (Healthcare Agent Communication Standard) providing dependency injection, configuration management, service discovery, and monitoring capabilities.

## Features

- **Dependency Injection Container**: Type-safe DI with singleton, transient, and scoped lifetimes
- **Configuration Management**: Environment-based configuration with validation
- **Service Registry & Discovery**: Service registration, health monitoring, and load balancing
- **Event System**: Pub/sub event bus with filtering and async handling
- **Lifecycle Management**: Graceful startup and shutdown orchestration
- **Monitoring**: Health checks, metrics collection, and performance monitoring

## Installation

```bash
pip install hacs-infrastructure
```

## Quick Start

```python
from hacs_infrastructure import Container, Injectable, get_config

# Dependency Injection
@Injectable
class DatabaseService:
    def __init__(self):
        self.connection = "database_connection"

@Injectable  
class UserService:
    def __init__(self, db: DatabaseService):
        self.db = db

container = Container()
container.register(DatabaseService)
container.register(UserService)

user_service = container.get(UserService)

# Configuration
config = get_config()
print(f"Environment: {config.environment}")
print(f"Debug mode: {config.debug}")
```

## License

MIT License - see LICENSE file for details.