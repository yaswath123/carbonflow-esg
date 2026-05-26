# TRADEOFFS

## 1. No live enterprise integrations

I did not build live SAP, utility, or Concur connectors. Real credentials, tenant-specific schemas, and customer network setup would dominate the prototype. Instead I modeled realistic export shapes and kept source metadata so live connectors can later feed the same normalization path.

## 2. Limited emission factor coverage

The prototype uses a tiny demo factor table embedded in code. Production should use an approved factor library with region, year, greenhouse gas breakdown, and versioning. I kept the prototype factors small so the review can focus on ingestion, lineage, and analyst workflow.

## 3. No full audit immutability layer

The model has audit events and lock timestamps, but it does not implement WORM storage, cryptographic hashes, or database-level immutability. Those are important for production but too heavy for this assignment compared with showing source-of-truth tracking and approval state clearly.
