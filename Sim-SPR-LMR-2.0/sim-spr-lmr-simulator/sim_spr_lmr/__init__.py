"""Simulation package organized by architectural responsibility.

The intended maintenance flow is:
Qt widgets -> application -> core -> presentation/infrastructure

- ``application`` normalizes UI state and orchestrates use cases.
- ``core`` contains the physical and mathematical simulation logic.
- ``presentation`` renders results back to the UI.
- ``infrastructure`` persists or exchanges generated artifacts.
"""
