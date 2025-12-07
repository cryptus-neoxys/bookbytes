---
trigger: glob
description: Rules for working with Python and FastAPI backend development.
globs: *.py
---

You are an expert in Python, FastAPI, and scalable API development.

FastAPI
Pydantic v2
Async database libraries
SQLAlchemy 2.0 (if using ORM features)

Write concise, technical responses with accurate Python examples.
Prefer iteration and modularization over code duplication.
Favour composition over inheritence. Smart core, Thin interfaces.
Use descriptive variable names with auxiliary verbs (e.g., is_active, has_permission).
Use lowercase with underscores for directories and files (e.g., routers/user_routes.py).
Favor named exports for routes and utility functions.
Use def for synchronous operations and async def for asynchronous ones.
Use type hints for all function signatures. Prefer Pydantic models over raw dictionaries for input validation.
Write typed python code strictly, and avoid the use of `Any`

Prioritize error handling and edge cases

Use functional components (plain functions) and Pydantic models/basemodel for consistent input/output validation and response schemas.
Ensure proper input validation, sanitization, and error handling throughout the application.
Use HTTPException for expected errors and model them as specific HTTP responses.
Use declarative route definitions with clear return type annotations.
Minimize @app.on_event("startup") and @app.on_event("shutdown"); prefer lifespan context managers for managing startup and shutdown events.
Use middleware for logging, error monitoring, and performance optimization and for handling unexpected errors.
Optimize for performance using async functions for I/O-bound tasks, caching strategies, and lazy loading.
Minimize blocking I/O operations; use asynchronous operations for all database calls and external API requests.
Implement caching for static and frequently accessed data using tools like Redis or in-memory stores.
Optimize data serialization and deserialization with Pydantic.
Use lazy loading techniques for large datasets and substantial API responses.
Refer to FastAPI, Pydantic, SQLAlachemy, other library documentation for Data Models, Shemas, Path Operations, Middleware and for best practices.
