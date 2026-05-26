from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health),
    path("dashboard/", views.dashboard),
    path("records/", views.records),
    path("records/<int:record_id>/review/", views.review_record),
    path("records/<int:record_id>/audit/", views.audit_events),
    path("upload/<str:source_type>/", views.upload),
]
