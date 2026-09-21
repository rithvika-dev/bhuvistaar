import os


ALLOWED_EXTENSIONS = {
    ".geojson",
    ".json",
    ".shp",
    ".gpkg",
    ".kml",
    ".kmz",
    ".tif",
    ".tiff",
    ".csv",
    ".zip"
}


def validate_file_extension(filename: str) -> bool:
    extension = os.path.splitext(filename)[1].lower()

    return extension in ALLOWED_EXTENSIONS


def get_file_type(filename: str) -> str:
    extension = os.path.splitext(filename)[1].lower()

    file_types = {
        ".geojson": "GeoJSON",
        ".json": "JSON",
        ".shp": "Shapefile",
        ".gpkg": "GeoPackage",
        ".kml": "KML",
        ".kmz": "KMZ",
        ".tif": "GeoTIFF",
        ".tiff": "GeoTIFF",
        ".csv": "CSV",
        ".zip": "ZIP"
    }

    return file_types.get(extension, "Unknown")