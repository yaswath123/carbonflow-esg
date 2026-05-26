import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .models import ActivityRecord, AuditEvent, Facility, IngestionBatch, SourceSystem

UNIT_FACTORS = {
    "l": ("l", Decimal("1")),
    "liter": ("l", Decimal("1")),
    "litre": ("l", Decimal("1")),
    "gal": ("l", Decimal("3.78541")),
    "kwh": ("kwh", Decimal("1")),
    "mwh": ("kwh", Decimal("1000")),
    "km": ("km", Decimal("1")),
    "mi": ("km", Decimal("1.60934")),
    "mile": ("km", Decimal("1.60934")),
    "night": ("night", Decimal("1")),
    "nights": ("night", Decimal("1")),
}

EMISSION_FACTORS = {
    ("stationary_combustion", "l"): Decimal("2.680000"),
    ("purchased_electricity", "kwh"): Decimal("0.716000"),
    ("flight", "km"): Decimal("0.158000"),
    ("hotel", "night"): Decimal("22.000000"),
    ("ground_transport", "km"): Decimal("0.171000"),
    ("purchased_goods", "inr"): Decimal("0.000120"),
}


def parse_date(value):
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported date: {value}")


def decimal_or_none(value):
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        return None


def normalize_quantity(value, unit):
    quantity = decimal_or_none(value)
    raw_unit = (unit or "").strip().lower()
    if quantity is None or raw_unit not in UNIT_FACTORS:
        return quantity, raw_unit, None, "", ["unknown_unit_or_quantity"]
    normalized_unit, factor = UNIT_FACTORS[raw_unit]
    return quantity, raw_unit, quantity * factor, normalized_unit, []


def calculate_co2e(activity_type, quantity, unit):
    factor = EMISSION_FACTORS.get((activity_type, unit))
    if factor is None or quantity is None:
        return None, None
    return factor, quantity * factor


def create_batch(org, source_type, filename):
    source = SourceSystem.objects.get(organization=org, source_type=source_type)
    return IngestionBatch.objects.create(organization=org, source_system=source, filename=filename)


def read_csv(uploaded_file):
    text = uploaded_file.read().decode("utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def facility_for(org, code, name=""):
    code = (code or "").strip()
    if not code:
        return None
    facility, _ = Facility.objects.get_or_create(
        organization=org,
        code=code,
        defaults={"name": name or code, "country": "India", "grid_region": "IN-KA"},
    )
    return facility


def ingest_sap(org, uploaded_file):
    batch = create_batch(org, SourceSystem.SourceType.SAP, uploaded_file.name)
    rows = read_csv(uploaded_file)
    batch.rows_received = len(rows)
    created = 0
    errors = []
    for idx, row in enumerate(rows, start=2):
        try:
            category = (row.get("category_hint") or "").lower()
            is_fuel = any(token in category for token in ("fuel", "diesel", "gas"))
            activity_type = "stationary_combustion" if is_fuel else "purchased_goods"
            scope = ActivityRecord.Scope.SCOPE_1 if is_fuel else ActivityRecord.Scope.SCOPE_3
            amount = row.get("quantity") if is_fuel else row.get("spend_amount")
            unit = row.get("unit") if is_fuel else "inr"
            original, raw_unit, normalized, norm_unit, flags = normalize_quantity(amount, unit)
            if not is_fuel:
                norm_unit = "inr"
                normalized = decimal_or_none(amount)
                flags = [] if normalized is not None else ["unknown_unit_or_quantity"]
            factor, co2e = calculate_co2e(activity_type, normalized, norm_unit)
            if row.get("plant_code", "").startswith("DE"):
                flags.append("localized_or_foreign_plant_code")
            status = ActivityRecord.Status.NEEDS_ATTENTION if flags else ActivityRecord.Status.PENDING
            record = ActivityRecord.objects.create(
                organization=org,
                facility=facility_for(org, row.get("plant_code"), row.get("plant_name")),
                source_system=batch.source_system,
                batch=batch,
                source_record_id=row.get("source_record_id") or f"sap-row-{idx}",
                raw_payload=row,
                scope=scope,
                activity_type=activity_type,
                period_start=parse_date(row.get("posting_date")),
                period_end=parse_date(row.get("posting_date")),
                quantity_original=original,
                unit_original=raw_unit,
                quantity_normalized=normalized,
                unit_normalized=norm_unit,
                emission_factor=factor,
                co2e_kg=co2e,
                flags=flags,
                status=status,
                confidence_score=65 if flags else 88,
            )
            AuditEvent.objects.create(organization=org, record=record, batch=batch, event_type="imported", after={"status": status})
            created += 1
        except Exception as exc:
            errors.append({"row": idx, "error": str(exc), "raw": row})
    batch.rows_created = created
    batch.errors = errors
    batch.status = IngestionBatch.Status.FAILED if errors and not created else IngestionBatch.Status.PROCESSED
    batch.save()
    return batch


def ingest_utility(org, uploaded_file):
    batch = create_batch(org, SourceSystem.SourceType.UTILITY, uploaded_file.name)
    rows = read_csv(uploaded_file)
    batch.rows_received = len(rows)
    created = 0
    errors = []
    for idx, row in enumerate(rows, start=2):
        try:
            original, raw_unit, normalized, norm_unit, flags = normalize_quantity(row.get("usage"), row.get("unit"))
            factor, co2e = calculate_co2e("purchased_electricity", normalized, norm_unit)
            if normalized and normalized > Decimal("250000"):
                flags.append("usage_outlier")
            status = ActivityRecord.Status.NEEDS_ATTENTION if flags else ActivityRecord.Status.PENDING
            record = ActivityRecord.objects.create(
                organization=org,
                facility=facility_for(org, row.get("facility_code"), row.get("service_address")),
                source_system=batch.source_system,
                batch=batch,
                source_record_id=row.get("meter_id") + ":" + row.get("period_start"),
                raw_payload=row,
                scope=ActivityRecord.Scope.SCOPE_2,
                activity_type="purchased_electricity",
                period_start=parse_date(row.get("period_start")),
                period_end=parse_date(row.get("period_end")),
                quantity_original=original,
                unit_original=raw_unit,
                quantity_normalized=normalized,
                unit_normalized=norm_unit,
                emission_factor=factor,
                co2e_kg=co2e,
                flags=flags,
                status=status,
                confidence_score=70 if flags else 92,
            )
            AuditEvent.objects.create(organization=org, record=record, batch=batch, event_type="imported", after={"status": status})
            created += 1
        except Exception as exc:
            errors.append({"row": idx, "error": str(exc), "raw": row})
    batch.rows_created = created
    batch.errors = errors
    batch.status = IngestionBatch.Status.FAILED if errors and not created else IngestionBatch.Status.PROCESSED
    batch.save()
    return batch


def ingest_travel(org, uploaded_file):
    batch = create_batch(org, SourceSystem.SourceType.TRAVEL, uploaded_file.name)
    rows = read_csv(uploaded_file)
    batch.rows_received = len(rows)
    created = 0
    errors = []
    for idx, row in enumerate(rows, start=2):
        try:
            category = (row.get("category") or "").lower()
            activity_type = "flight" if category == "flight" else "hotel" if category == "hotel" else "ground_transport"
            value = row.get("distance") if activity_type != "hotel" else row.get("nights")
            unit = row.get("distance_unit") if activity_type != "hotel" else "night"
            original, raw_unit, normalized, norm_unit, flags = normalize_quantity(value, unit)
            if activity_type == "flight" and not normalized:
                flags.append("flight_distance_missing_airport_lookup_required")
            factor, co2e = calculate_co2e(activity_type, normalized, norm_unit)
            status = ActivityRecord.Status.NEEDS_ATTENTION if flags else ActivityRecord.Status.PENDING
            record = ActivityRecord.objects.create(
                organization=org,
                facility=None,
                source_system=batch.source_system,
                batch=batch,
                source_record_id=row.get("trip_id") or f"travel-row-{idx}",
                raw_payload=row,
                scope=ActivityRecord.Scope.SCOPE_3,
                activity_type=activity_type,
                period_start=parse_date(row.get("start_date")),
                period_end=parse_date(row.get("end_date") or row.get("start_date")),
                quantity_original=original,
                unit_original=raw_unit,
                quantity_normalized=normalized,
                unit_normalized=norm_unit,
                emission_factor=factor,
                co2e_kg=co2e,
                flags=flags,
                status=status,
                confidence_score=62 if flags else 86,
            )
            AuditEvent.objects.create(organization=org, record=record, batch=batch, event_type="imported", after={"status": status})
            created += 1
        except Exception as exc:
            errors.append({"row": idx, "error": str(exc), "raw": row})
    batch.rows_created = created
    batch.errors = errors
    batch.status = IngestionBatch.Status.FAILED if errors and not created else IngestionBatch.Status.PROCESSED
    batch.save()
    return batch
