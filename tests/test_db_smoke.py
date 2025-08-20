import os
import pytest

pytestmark = pytest.mark.db


def test_can_create_postgres_adapter_when_configured():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL not set; skipping DB smoke test")

    try:
        from hacs_persistence.adapter import create_postgres_adapter
    except Exception as e:
        pytest.skip(f"hacs_persistence not available: {e}")

    async def _run():
        adapter = await create_postgres_adapter(database_url=db_url)
        assert adapter is not None
        assert hasattr(adapter, "save")

    import asyncio

    asyncio.run(_run())
