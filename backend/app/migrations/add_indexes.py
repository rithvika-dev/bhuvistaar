"""
Migration script for database performance and PostGIS spatial indexing.

1. Safe column alteration: spatial_features.confidence_score (Integer -> Float / DOUBLE PRECISION)
2. Indexes on foreign keys and filter fields (project_id, dataset_id, dataset_version_id, feature_id, match_status, resolution_status, review_status)
3. PostGIS GIST spatial indexes on geometry columns.
"""

from sqlalchemy import text
from app.database import engine

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
        ]

        for stmt in missing_column_statements:
            try:
                conn.execute(text(stmt))
                print(f"  - Applied migration: {stmt}")
            except Exception as e:
                print(f"  - Migration note: {e}")

        # 3. Add B-Tree indexes on relational & query fields
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON datasets(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_dataset_versions_dataset_id ON dataset_versions(dataset_id);",
            "CREATE INDEX IF NOT EXISTS idx_spatial_features_version_id ON spatial_features(dataset_version_id);",
            "CREATE INDEX IF NOT EXISTS idx_feature_matches_project_id ON feature_matches(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_feature_matches_source_id ON feature_matches(source_feature_id);",
            "CREATE INDEX IF NOT EXISTS idx_feature_matches_target_id ON feature_matches(target_feature_id);",
            "CREATE INDEX IF NOT EXISTS idx_feature_matches_status ON feature_matches(match_status);",
            "CREATE INDEX IF NOT EXISTS idx_conflicts_project_id ON conflicts(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_conflicts_feature_id ON conflicts(feature_id);",
            "CREATE INDEX IF NOT EXISTS idx_conflicts_status ON conflicts(resolution_status);",
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

        # 4. PostGIS spatial GIST indexes
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
