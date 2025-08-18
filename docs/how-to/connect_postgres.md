# Connect to a Postgres database

Assumes `DATABASE_URL` is set and migrations are handled by persistence docs.

```python
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

from hacs_persistence import HACSConnectionFactory

adapter = HACSConnectionFactory.get_adapter(auto_migrate=False)
print("DB adapter:", type(adapter).__name__)
```

```
DB adapter: PostgreSQLAdapter
```
