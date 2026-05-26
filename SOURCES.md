# SOURCES

## SAP fuel and procurement

Researched format: SAP S/4HANA OData APIs and SAPData metadata. SAP documents OData endpoints for purchase-order operations and SAP-specific OData metadata annotations.

What I learned:

- SAP OData payloads expose typed entity properties, but customer configuration still affects field names, language, material groups, and account assignment.
- Purchase/procurement data usually carries ids that are meaningful only with SAP lookup tables, such as plant, material, supplier, and cost center.
- Fuel consumption may appear as material movements or purchasing documents depending on how the client records fuel.

Sample data shape:

- `source_record_id`
- `plant_code`
- `plant_name`
- `material_text`
- `posting_date`
- `quantity`
- `unit`
- `spend_amount`
- `currency`
- `category_hint`

What would break in real deployment:

- Unknown customer-specific material groups
- German or localized labels
- Split account assignments
- OData pagination and delta extraction
- Unit conversions for density-based fuel units

References:

- SAP OData protocol documentation: https://www.sap.com/protocols/sapdata
- SAP S/4HANA purchase order OData documentation: https://help.sap.com/docs/SAP_S4HANA_CLOUD/bb9f1469daf04bd894ab2167f8132a1a/46dcde53d7964b768dcf75f97f4e3db9.html

## Utility electricity

Researched format: Green Button utility usage data.

What I learned:

- Green Button is intended for utility interval usage and billing data.
- Utilities may provide 15-minute, hourly, daily, or monthly intervals.
- Billing periods often do not match calendar months, which matters for ESG reporting allocation.

Sample data shape:

- `meter_id`
- `facility_code`
- `period_start`
- `period_end`
- `usage`
- `unit`
- `tariff`
- `cost`

What would break in real deployment:

- PDF-only utilities
- Interval data mixed with billing adjustments
- Multiple meters per facility
- Solar export/net metering
- Region-specific grid emission factors

References:

- Green Button Connect My Data: https://www.greenbuttonalliance.org/green-button-connect-my-data-cmd
- UtilityAPI Green Button notes: https://utilityapi.com/docs/greenbutton

## Corporate travel

Researched format: SAP Concur expense/travel APIs and expense configuration.

What I learned:

- Concur data is highly configurable by client.
- Expense entries and configuration include expense types, payment types, attendees, and workflow state.
- Travel-related APIs may expose receipts, travel allowances, or supplier/direct-connect flows, but access is limited and product-specific.

Sample data shape:

- `trip_id`
- `traveler_ref`
- `category`
- `start_date`
- `end_date`
- `origin`
- `destination`
- `distance`
- `distance_unit`
- `nights`
- `amount`
- `currency`

What would break in real deployment:

- Missing flight distances
- Multi-leg trips represented as one expense
- Client-specific expense categories
- Rail mixed into ground transport
- Personal data retention requirements

References:

- SAP Concur Expense Configuration v4: https://preview.developer.concur.com/api-reference/expense/expense-config/v4.expense.config.html
- SAP Concur Travel Receipts getting started: https://preview.developer.concur.com/api-reference/travel-receipts/getting-started.html
- SAP Concur Travel Allowance calculation results: https://preview.developer.concur.com/api-reference/travelallowance/v4.travelallowance-calculationresults-endpoints.html
