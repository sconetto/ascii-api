"""Shared FastAPI dependencies.

All reusable Depends() callables live here so routers stay thin and
dependencies can be easily overridden in tests.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    The cache means the .env file is read only once per process lifetime.
    In tests, override this dependency with app.dependency_overrides.
    """
    return Settings()


# Convenience type alias used in route signatures:
#   def my_route(settings: SettingsDep) -> ...:
SettingsDep = Annotated[Settings, Depends(get_settings)]
