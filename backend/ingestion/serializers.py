from rest_framework import serializers

from .models import ActivityRecord, AuditEvent, Facility, IngestionBatch, SourceSystem


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "code", "name", "country", "grid_region"]


class SourceSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceSystem
        fields = ["id", "name", "source_type", "connection_mode", "description"]


class IngestionBatchSerializer(serializers.ModelSerializer):
    source_system = SourceSystemSerializer()

    class Meta:
        model = IngestionBatch
        fields = ["id", "source_system", "filename", "status", "rows_received", "rows_created", "errors", "created_at"]


class ActivityRecordSerializer(serializers.ModelSerializer):
    facility = FacilitySerializer()
    source_system = SourceSystemSerializer()

    class Meta:
        model = ActivityRecord
        fields = [
            "id",
            "facility",
            "source_system",
            "source_record_id",
            "scope",
            "activity_type",
            "period_start",
            "period_end",
            "quantity_original",
            "unit_original",
            "quantity_normalized",
            "unit_normalized",
            "emission_factor",
            "co2e_kg",
            "confidence_score",
            "status",
            "flags",
            "review_note",
            "approved_by",
            "approved_at",
            "locked_at",
            "raw_payload",
            "created_at",
            "updated_at",
        ]


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ["id", "record", "batch", "event_type", "actor", "before", "after", "message", "created_at"]
