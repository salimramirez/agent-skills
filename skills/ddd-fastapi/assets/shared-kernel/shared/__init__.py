"""Shared kernel.

The small set of building blocks every bounded context uses the same way: the
aggregate root base class and domain event type, the domain exception
hierarchy, the unit-of-work port, the database session and declarative base,
the application settings, and the handler that turns domain exceptions into
HTTP responses. Nothing here knows about any particular context.
"""
