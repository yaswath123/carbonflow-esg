from django.conf import settings
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Facility(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="facilities")
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=160)
    country = models.CharField(max_length=64, default="India")
    grid_region = models.CharField(max_length=80, blank=True)

    class Meta:
        unique_together = ("organization", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class SourceSystem(models.Model):
    class SourceType(models.TextChoices):
        SAP = "sap", "SAP"
        UTILITY = "utility", "Utility"
        TRAVEL = "travel", "Travel"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sources")
    name = models.CharField(max_length=160)
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    connection_mode = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class IngestionBatch(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="batches")
    source_system = models.ForeignKey(SourceSystem, on_delete=models.PROTECT, related_name="batches")
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.RECEIVED)
    rows_received = models.PositiveIntegerField(default=0)
    rows_created = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_system.name} {self.filename}"


class ActivityRecord(models.Model):
    class Scope(models.TextChoices):
        SCOPE_1 = "scope_1", "Scope 1"
        SCOPE_2 = "scope_2", "Scope 2"
        SCOPE_3 = "scope_3", "Scope 3"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        NEEDS_ATTENTION = "needs_attention", "Needs attention"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        LOCKED = "locked", "Locked"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="activity_records")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, related_name="activity_records", null=True, blank=True)
    source_system = models.ForeignKey(SourceSystem, on_delete=models.PROTECT, related_name="activity_records")
    batch = models.ForeignKey(IngestionBatch, on_delete=models.SET_NULL, related_name="activity_records", null=True, blank=True)
    source_record_id = models.CharField(max_length=160)
    raw_payload = models.JSONField(default=dict)
    scope = models.CharField(max_length=32, choices=Scope.choices)
    activity_type = models.CharField(max_length=80)
    period_start = models.DateField()
    period_end = models.DateField()
    quantity_original = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    unit_original = models.CharField(max_length=40, blank=True)
    quantity_normalized = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    unit_normalized = models.CharField(max_length=40, blank=True)
    emission_factor = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    co2e_kg = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)
    confidence_score = models.PositiveSmallIntegerField(default=80)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    flags = models.JSONField(default=list, blank=True)
    review_note = models.TextField(blank=True)
    approved_by = models.CharField(max_length=160, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("organization", "source_system", "source_record_id")
        ordering = ("-created_at",)

    def mark_reviewed(self, action, note="", actor="analyst"):
        if action == "approve":
            self.status = self.Status.APPROVED
            self.approved_by = actor
            self.approved_at = timezone.now()
        elif action == "reject":
            self.status = self.Status.REJECTED
        elif action == "lock":
            self.status = self.Status.LOCKED
            self.locked_at = timezone.now()
        self.review_note = note
        self.save()


class AuditEvent(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="audit_events")
    record = models.ForeignKey(ActivityRecord, on_delete=models.CASCADE, related_name="audit_events", null=True, blank=True)
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="audit_events", null=True, blank=True)
    event_type = models.CharField(max_length=64)
    actor = models.CharField(max_length=160, default="system")
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
