import geopandas as gpd


def extract_features(gdf: gpd.GeoDataFrame) -> list:
    """
    Extract individual GIS features from a GeoDataFrame.
    """

    if gdf.empty:
        raise ValueError("Dataset contains no features")

    features = []

    for index, row in gdf.iterrows():

        geometry = row.geometry

        if geometry is None or geometry.is_empty:
            continue

        attributes = {}

        for column in gdf.columns:
            if column == gdf.geometry.name:
                continue

            value = row[column]

            # Convert values to JSON-friendly strings when necessary
            if value is not None:
                try:
                    attributes[column] = value.item()
                except AttributeError:
                    attributes[column] = value

        features.append(
            {
                "source_index": int(index),
                "feature_type": geometry.geom_type,
                "geometry": geometry,
                "attributes": attributes
            }
        )

    return features