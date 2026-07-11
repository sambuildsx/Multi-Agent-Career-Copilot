from typing import Any


class BaseAgent:
    """Plain base class — no abstract enforcement. Subclasses are expected
    to implement `run`, but a missing implementation will only fail when
    `run()` is actually called (AttributeError), not at instantiation time.
    This avoids opaque `TypeError: Can't instantiate abstract class` crashes
    when a subclass is mid-development."""

    def run(self, state: Any) -> dict:
        raise NotImplementedError(f"{self.__class__.__name__} must implement run()")