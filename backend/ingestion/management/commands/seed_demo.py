from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from ingestion.models import ActivityRecord, AuditEvent, Facility, IngestionBatch, Organization, SourceSystem
from ingestion.normalizers import ingest_sap, ingest_travel, ingest_utility


class Command(BaseCommand):
    help = "Seed demo tenant, sources, and sample imported activity records."

    def handle(self, *args, **options):
        AuditEvent.objects.all().delete()
        ActivityRecord.objects.all().delete()
        IngestionBatch.objects.all().delete()
        Facility.objects.all().delete()
        SourceSystem.objects.all().delete()
        Organization.objects.all().delete()

        org = Organization.objects.create(name="Demo Manufacturing Ltd", slug="demo-enterprise")
        Facility.objects.create(organization=org, code="BLR-01", name="Bangalore Assembly Plant", country="India", grid_region="IN-KA")
        Facility.objects.create(organization=org, code="MUM-DC", name="Mumbai Distribution Centre", country="India", grid_region="IN-MH")
        SourceSystem.objects.create(
            organization=org,
            name="SAP S/4HANA OData export",
            source_type=SourceSystem.SourceType.SAP,
            connection_mode="CSV export from OData integration job",
            description="Prototype stand-in for material document and purchase order OData feeds.",
        )
        SourceSystem.objects.create(
            organization=org,
            name="Utility Green Button portal",
            source_type=SourceSystem.SourceType.UTILITY,
            connection_mode="Facilities CSV upload",
            description="Green Button-style electricity usage export with billing periods.",
        )
        SourceSystem.objects.create(
            organization=org,
            name="Concur-like travel export",
            source_type=SourceSystem.SourceType.TRAVEL,
            connection_mode="Monthly expense/travel CSV export",
            description="Travel rows for flights, hotels, and ground transport.",
        )

        samples = [
            ("sap_demo.csv", "sap", """source_record_id,plant_code,plant_name,material_text,posting_date,quantity,unit,spend_amount,currency,category_hint
4900003101,BLR-01,Bangalore Assembly Plant,Diesel for generator,2026-04-03,1200,L,0,INR,diesel fuel
4900003102,DE-77,Werk Hamburg,Erdgas,03.04.2026,330,gal,0,EUR,natural gas fuel
4500009812,MUM-DC,Mumbai Distribution Centre,Packaging corrugate,2026-04-10,,EA,540000,INR,purchased goods
"""),
            ("utility_demo.csv", "utility", """meter_id,facility_code,service_address,period_start,period_end,usage,unit,tariff,cost
KA-BLR-7781,BLR-01,Bangalore Assembly Plant,2026-03-18,2026-04-17,184500,kWh,HT Industrial,1562200
MH-MUM-1902,MUM-DC,Mumbai Distribution Centre,2026-03-25,2026-04-24,276000,kWh,Commercial Demand,2310000
"""),
            ("travel_demo.csv", "travel", """trip_id,traveler_ref,category,start_date,end_date,origin,destination,distance,distance_unit,nights,amount,currency
TR-1001,EMP-884,flight,2026-04-05,2026-04-05,BLR,DEL,1740,km,,42000,INR
TR-1002,EMP-102,hotel,2026-04-06,2026-04-08,Delhi,Delhi,,,2,18000,INR
TR-1003,EMP-884,flight,2026-04-12,2026-04-12,BLR,SFO,,,,185000,INR
TR-1004,EMP-551,ground,2026-04-14,2026-04-14,Bangalore,Bangalore,32,mi,,2400,INR
"""),
        ]
        handlers = {"sap": ingest_sap, "utility": ingest_utility, "travel": ingest_travel}
        for filename, source_type, content in samples:
            handlers[source_type](org, ContentFile(content.encode("utf-8"), name=filename))

        self.stdout.write(self.style.SUCCESS("Seeded demo data."))
