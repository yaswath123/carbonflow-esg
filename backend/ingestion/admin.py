from django.contrib import admin

from .models import ActivityRecord, AuditEvent, Facility, IngestionBatch, Organization, SourceSystem


admin.site.register([Organization, Facility, SourceSystem, IngestionBatch, ActivityRecord, AuditEvent])
