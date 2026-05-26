# DECISIONS

## SAP source

I chose a SAP S/4HANA OData-style export rather than IDoc or BAPI. SAP exposes purchase order and material document APIs through OData services, and OData can be queried by integration services without asking a sustainability analyst to understand SAP transaction screens.

The prototype handles a CSV export shaped like an OData result set because most candidate reviewers can run it locally without SAP credentials. Columns include material document or purchase order id, plant code, material text, movement date, quantity, unit, and spend fields.

Ignored: direct SAP auth, delta tokens, BAPI calls, IDoc parsing, account assignment hierarchies, and full material master classification.

## Utility source

I chose a Green Button-style utility usage export. Facilities teams commonly download usage data from portals, and Green Button is a recognized data-sharing format for utility interval and billing data.

The prototype handles CSV rows with meter id, service address, billing period, kWh, demand, tariff, and cost. It accepts billing periods that do not align to calendar months.

Ignored: PDF bill extraction, OCR, tariff line-item reconstruction, demand charge emissions, and utility OAuth.

## Travel source

I chose a Concur-like expense/travel export instead of a live API pull. SAP Concur APIs exist for expense entries, configuration, attendees, receipts, workflow actions, and travel allowance/receipt flows, but access is gated and customer-specific.

The prototype handles CSV rows for flights, hotels, and ground transport. Flights can provide either distance or origin/destination airport codes. Missing distance is flagged because a production system would need an airport distance service.

Ignored: OAuth, receipt image APIs, itinerary reconciliation, employee PII beyond a hashed/opaque traveler id, cabin class multipliers, and multi-leg journey expansion.

## Review workflow

Rows are imported as pending unless normalization cannot be completed or heuristic checks find suspicious data. Analysts can approve or reject rows and add notes. This is intentionally simple because the assignment is about data judgement, not building a full workflow engine.

## What I would ask the PM

- Which emission factor library should be authoritative for each geography and reporting year?
- Are auditors expecting row-level evidence attachments, or is source-system lineage enough for round one?
- Do clients need self-service source mapping, or will Breathe configure mappings during onboarding?
- Which source is highest-volume in current customer onboarding: SAP, utilities, or travel?
- Does approval happen at row level, batch level, facility-month level, or all three?
