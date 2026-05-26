from django.db.models import Count, Sum
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ActivityRecord, AuditEvent, IngestionBatch, Organization
from .normalizers import ingest_sap, ingest_travel, ingest_utility
from .serializers import ActivityRecordSerializer, AuditEventSerializer, IngestionBatchSerializer


def demo_org():
    return Organization.objects.get(slug="demo-enterprise")


@api_view(["GET"])
def health(_request):
    return Response({"ok": True})


@api_view(["GET"])
def dashboard(_request):
    org = demo_org()
    records = ActivityRecord.objects.filter(organization=org)
    by_status = records.values("status").annotate(count=Count("id")).order_by("status")
    by_scope = records.values("scope").annotate(count=Count("id"), co2e_kg=Sum("co2e_kg")).order_by("scope")
    suspicious = records.exclude(flags=[]).count()
    latest_batches = IngestionBatch.objects.filter(organization=org).order_by("-created_at")[:5]
    return Response(
        {
            "totals": {
                "records": records.count(),
                "pending": records.filter(status__in=["pending", "needs_attention"]).count(),
                "approved": records.filter(status="approved").count(),
                "locked": records.filter(status="locked").count(),
                "suspicious": suspicious,
                "co2e_kg": records.aggregate(total=Sum("co2e_kg"))["total"] or 0,
            },
            "by_status": list(by_status),
            "by_scope": list(by_scope),
            "latest_batches": IngestionBatchSerializer(latest_batches, many=True).data,
        }
    )


@api_view(["GET"])
def records(request):
    org = demo_org()
    queryset = ActivityRecord.objects.filter(organization=org).select_related("facility", "source_system")
    status_filter = request.query_params.get("status")
    source_filter = request.query_params.get("source")
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if source_filter:
        queryset = queryset.filter(source_system__source_type=source_filter)
    return Response(ActivityRecordSerializer(queryset[:200], many=True).data)


@api_view(["GET"])
def audit_events(_request, record_id):
    org = demo_org()
    events = AuditEvent.objects.filter(organization=org, record_id=record_id)
    return Response(AuditEventSerializer(events, many=True).data)


@api_view(["POST"])
def review_record(request, record_id):
    org = demo_org()
    action = request.data.get("action")
    note = request.data.get("note", "")
    if action not in {"approve", "reject", "lock"}:
        return Response({"detail": "action must be approve, reject, or lock"}, status=status.HTTP_400_BAD_REQUEST)
    record = ActivityRecord.objects.get(organization=org, id=record_id)
    before = {"status": record.status, "review_note": record.review_note}
    record.mark_reviewed(action=action, note=note, actor="demo.analyst@breatheesg.com")
    AuditEvent.objects.create(
        organization=org,
        record=record,
        event_type=action,
        actor="demo.analyst@breatheesg.com",
        before=before,
        after={"status": record.status, "review_note": record.review_note},
    )
    return Response(ActivityRecordSerializer(record).data)


@api_view(["POST"])
def upload(request, source_type):
    org = demo_org()
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response({"detail": "file is required"}, status=status.HTTP_400_BAD_REQUEST)
    handlers = {"sap": ingest_sap, "utility": ingest_utility, "travel": ingest_travel}
    if source_type not in handlers:
        return Response({"detail": "unknown source type"}, status=status.HTTP_400_BAD_REQUEST)
    batch = handlers[source_type](org, uploaded_file)
    return Response(IngestionBatchSerializer(batch).data, status=status.HTTP_201_CREATED)
