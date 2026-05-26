# MODEL

## Core idea

The model separates source evidence from normalized ESG activity rows. Every imported row keeps the raw payload, source system, source record id, tenant, normalization result, review status, and audit events. That makes the prototype useful for analysts while preserving enough lineage for auditors.

## Entities

### Organization

Represents a tenant. All operational records carry `organization_id`, so multiple client companies can use the same installation without sharing data.

### Facility

Tenant-owned plant/site/location lookup. SAP plant codes and utility meters are not meaningful by themselves, so imported records resolve to a facility where possible and are flagged when the lookup fails.

### SourceSystem

Tracks the source of truth: SAP, utility portal, or Concur-style travel platform. The model stores the source type, name, and connection mode, such as export upload or API pull.

### IngestionBatch

One uploaded file or pulled API window. It records who imported it, when, source system, filename, row counts, status, and import errors. This gives analysts an operational view of what came in and what failed.

### ActivityRecord

The normalized review row. Important fields:

- `organization`, `facility`, `source_system`, `batch`
- `source_record_id` and `raw_payload` for provenance
- `scope`: Scope 1, 2, or 3
- `activity_type`: stationary combustion, purchased electricity, flight, hotel, ground transport, or purchased goods
- `period_start`, `period_end`
- `quantity_original`, `unit_original`
- `quantity_normalized`, `unit_normalized`
- `emission_factor`, `co2e_kg`
- `status`: pending, needs_attention, approved, rejected, locked
- `flags`: machine-readable analyst warnings
- `review_note`, `approved_by`, `approved_at`, `locked_at`

### AuditEvent

Append-only log for import, normalization, edit, approve, reject, and lock actions. It stores before/after JSON snapshots when a reviewed row changes.

## Multi-tenancy

Every table that contains client data is keyed by `Organization`. In production I would enforce tenant scoping through authentication middleware and database constraints. In the prototype, the API uses a demo organization but the model already supports real tenant isolation.

## Scope mapping

- SAP diesel / natural gas fuel consumption: Scope 1
- SAP purchased goods and services: Scope 3
- Utility purchased electricity: Scope 2
- Corporate travel flights, hotels, and ground transport: Scope 3

## Unit normalization

The prototype normalizes common units into canonical units:

- `L`, `liter`, `litre` to `l`
- `gal` to `l`
- `kWh`, `MWh` to `kwh`
- travel distance `mi`, `mile`, `km` to `km`
- hotel nights to `night`

The original value and unit are always retained. Records with unknown units are not thrown away; they are marked `needs_attention` with a flag.

## Audit locking

Rows can be approved, rejected, or locked. Approval is an analyst decision. Locking represents audit finalization and prevents further edits in a production version. The prototype exposes lock status in the model and dashboard; hard edit prevention would be implemented in serializer validation before production.
