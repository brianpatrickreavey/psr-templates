"""PSR Templates Arranger Package."""

from typing import Any

# Register custom Jinja2 filters globally when this package is imported
# This ensures they're available when PSR runs templates
try:
    from jinja2 import Environment

    from . import jinja_filters

    # Store the original __init__ method
    _original_env_init = Environment.__init__

    def _patched_env_init(self: Any, *args: Any, **kwargs: Any) -> None:
        """Patched Environment.__init__ to register custom filters."""
        # Call original init
        _original_env_init(self, *args, **kwargs)
        # Add custom filters after initialization
        self.filters.update(jinja_filters.FILTERS)

    # Replace the __init__ method
    Environment.__init__ = _patched_env_init

except ImportError:
    # Jinja2 not available, skip patching
    pass
