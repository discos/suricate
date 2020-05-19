class CannotGetComponentError(Exception):
    """The Component reference is broken"""


class ComponentAttributeError(Exception):
    """The attribute is not available"""


class ACSNotRunningError(Exception):
    """ACS not running"""
