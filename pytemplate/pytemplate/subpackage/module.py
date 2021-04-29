"""Sample module.

This module demonstrates that you can access resources from subpackages.

  Typical usage example:

  y = get_something(x)
"""

import numpy as np
from pytemplate import resource_text

something_path = "resource.txt"


def get_something(x=None):
    """Gets something.

    Returns something useful. Demonstrates that you can access resources from subpackages.

    Args:
        x: Anything. Defaults to None.

    Returns:
        String with something useful.
    """
    _ = np.array(x)  # third-party packages work
    return resource_text(something_path)
