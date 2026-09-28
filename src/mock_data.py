"""Enterprise CRM and Telemetry Data Store (Backward-compatibility layer).

NOTE: The primary customer CRM, invoicing ledger, and telemetry databases have
been organized into `src.crm_store`. This module re-exports all constants and
functions to ensure 100% backward compatibility for existing imports and tests.
"""

from src.crm_store import (
    CUSTOMERS_DB,
    CUSTOMER_BY_EMAIL,
    INVOICES_DB,
    KNOWLEDGE_BASE,
    MOCK_SYSTEM_LOGS,
    SYSTEM_STATUS_DB,
    _SEED_CUSTOMERS,
    _SEED_INVOICES,
    _load_customers_db,
    _load_invoices_db,
)

__all__ = [
    "CUSTOMERS_DB",
    "CUSTOMER_BY_EMAIL",
    "INVOICES_DB",
    "KNOWLEDGE_BASE",
    "MOCK_SYSTEM_LOGS",
    "SYSTEM_STATUS_DB",
    "_SEED_CUSTOMERS",
    "_SEED_INVOICES",
    "_load_customers_db",
    "_load_invoices_db",
]
