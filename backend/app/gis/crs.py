import geopandas as gpd


# Common CRS used internally by BhuVistaar
TARGET_CRS = "EPSG:4326"


def normalize_crs(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Convert a GeoDataFrame to the common BhuVistaar CRS.
    """

    if gdf.crs is None:
        raise ValueError(
            "Dataset CRS is missing. Georeferencing is required."
        )

    if str(gdf.crs) == TARGET_CRS:
        return gdf

    return gdf.to_crs(TARGET_CRS)