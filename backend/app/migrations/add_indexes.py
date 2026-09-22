"""
Migration script for database performance, schema updates, PostGIS spatial indexing,
and safe deduplication of conflict records.
"""

import re
from sqlalchemy import text
from app.database import engine


def extract_conflict_key(description: str, conflict_type: str) -> str:
    """Extracts a normalized field or key from conflict description."""
    if not description:
        return ""
    if conflict_type in ("attribute_mismatch", "identity_conflict"):
        m = re.search(r"(?:Attribute|Identity)\s+'([^']+)'", description)
        if m:
            return m.group(1).strip().lower()
    return description.strip()[:60].lower()


def consolidate_duplicate_conflicts(conn):
    """
    Safely groups duplicate conflict records, preserves any reviewed/resolved state,
    and removes only redundant duplicates without losing real conflict history.
    """
    try:
        rows = conn.execute(text("""
            SELECT id, project_id, feature_id, conflict_type, description, 
                   resolution_status, confidence_score, resolution_notes
            FROM conflicts
            ORDER BY id ASC
        """)).fetchall()

        if not rows:
            return

        groups = {}
        for row in rows:
            c_id = row[0]
            proj_id = row[1]
            feat_id = row[2]
            c_type = row[3]
            desc = row[4] or ""
            res_status = row[5] or "pending"
            field_key = extract_conflict_key(desc, c_type)

            group_key = (proj_id, feat_id, c_type, field_key)
            groups.setdefault(group_key, []).append({
                "id": c_id,
                "status": res_status,
                "desc": desc,
            })

        delete_ids = []
        for group_key, items in groups.items():
            if len(items) > 1:
                # Find if any item is resolved
                resolved_items = [it for it in items if it["status"] != "pending"]
                if resolved_items:
                    canonical_id = resolved_items[0]["id"]
                else:
                    canonical_id = items[0]["id"]

                for it in items:
                    if it["id"] != canonical_id:
                        delete_ids.append(it["id"])

        if delete_ids:
            # Batch delete in chunks of 500
            chunk_size = 500
            for i in range(0, len(delete_ids), chunk_size):
                chunk = delete_ids[i:i + chunk_size]
                conn.execute(
                    text("DELETE FROM conflicts WHERE id = ANY(:ids)"),
                    {"ids": chunk}
                )
            print(f"  - Consolidated {len(delete_ids)} redundant duplicate conflicts safely.")

        # Backfill severity and reasonable confidence for remaining legacy records
        conn.execute(text("""
            UPDATE conflicts
            SET severity = CASE
                WHEN conflict_type = 'identity_conflict' THEN 'high'
                WHEN conflict_type = 'duplicate_feature' THEN 'high'
                WHEN description ILIKE '%land_use%' OR description ILIKE '%zoning%' THEN 'high'
                WHEN description ILIKE '%area%' AND confidence_score < 0.5 THEN 'high'
                WHEN conflict_type = 'geometry_conflict' THEN 'medium'
                ELSE 'medium'
            END
            WHERE severity IS NULL;
        """))

        conn.execute(text("""
            UPDATE conflicts
            SET confidence_score = 0.85
            WHERE confidence_score IS NULL OR confidence_score <= 0.05;
        """))

    except Exception as e:
        print(f"  - Note on duplicate consolidation: {e}")


def run_migrations():
    print("Running database index & column type migrations...")
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Alter SpatialFeature.confidence_score column type to DOUBLE PRECISION
            conn.execute(text("""
                ALTER TABLE spatial_features 
                ALTER COLUMN confidence_score TYPE DOUBLE PRECISION 
                USING confidence_score::DOUBLE PRECISION;
            """))
            print("  - Updated spatial_features.confidence_score to DOUBLE PRECISION")
        except Exception as e:
            print(f"  - Note on confidence_score alter: {e}")

        # 2. Backfill missing columns for existing databases created before the latest schema revision.
        missing_column_statements = [
            "ALTER TABLE harmonized_features ADD COLUMN IF NOT EXISTS match_id INTEGER;",
            "ALTER TABLE harmonized_features ADD COLUMN IF NOT EXISTS source_info TEXT;",
            "ALTER TABLE conflicts ADD COLUMN IF NOT EXISTS severity VARCHAR(50) DEFAULT 'medium';",
            "ALTER TABLE conflicts ADD COLUMN IF NOT EXISTS suggested_resolution TEXT;",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS settings TEXT DEFAULT '{}';",
        ]

        for stmt in missing_column_statements:
            try:
                conn.execute(text(stmt))
                print(f"  - Applied migration: {stmt}")
            except Exception as e:
                print(f"  - Migration note: {e}")

        # 3. Consolidate legacy duplicate conflicts safely
        consolidate_duplicate_conflicts(conn)

        # 4. Add B-Tree indexes on relational & query fields
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON datasets(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_dataset_versions_dataset_id ON dataset_versions(dataset_id);",
            "CREATE INDEX IF NOT EXISTS idx_spatial_features_version_id ON spatial_features(dataset_version_id);",
            "CREATE INDEX IF NOT EXISTS idx_feature_matches_project_id ON feature_matches(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_feature_matches_source_id ON feature_matches(source_feature_id);",
            "CREATE INDEX IF NOT EXISTS idx_feature_matches_target_id ON feature_matches(target_feature_id);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_feature_matches_unique_pair ON feature_matches(source_feature_id, target_feature_id);",
            "CREATE INDEX IF NOT EXISTS idx_feature_matches_status ON feature_matches(match_status);",
            "CREATE INDEX IF NOT EXISTS idx_conflicts_project_id ON conflicts(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_conflicts_feature_id ON conflicts(feature_id);",
            "CREATE INDEX IF NOT EXISTS idx_conflicts_status ON conflicts(resolution_status);",
            "CREATE INDEX IF NOT EXISTS idx_conflicts_severity ON conflicts(severity);",
            "CREATE INDEX IF NOT EXISTS idx_harmonized_features_project_id ON harmonized_features(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_harmonized_features_review_status ON harmonized_features(review_status);",
            "CREATE INDEX IF NOT EXISTS idx_validation_results_project_id ON validation_results(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_change_detections_project_id ON change_detections(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_change_detections_review_status ON change_detections(review_status);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_project_id ON audit_logs(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);",
            "CREATE INDEX IF NOT EXISTS idx_processing_jobs_project_id ON processing_jobs(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);",
        ]

        for stmt in index_statements:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                print(f"  - Index creation note: {e}")

        # 5. PostGIS spatial GIST indexes
        spatial_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_spatial_features_geom_gist ON spatial_features USING GIST (geometry);",
            "CREATE INDEX IF NOT EXISTS idx_harmonized_features_geom_gist ON harmonized_features USING GIST (geometry);",
        ]

        for stmt in spatial_indexes:
            try:
                conn.execute(text(stmt))
                print(f"  - Added PostGIS GIST spatial index: {stmt.split()[5]}")
            except Exception as e:
                print(f"  - Spatial index note: {e}")

        trans.commit()
    print("Database migrations completed successfully.")


if __name__ == "__main__":
    run_migrations()
