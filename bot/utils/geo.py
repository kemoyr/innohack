import math


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula."""
    R = 6_371_000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_location_match(
    lat1: float, lon1: float, lat2: float, lon2: float, max_distance_m: int = 500
) -> bool:
    """Return True if two points are within max_distance_m meters of each other."""
    if None in (lat1, lon1, lat2, lon2):
        return False
    return haversine(lat1, lon1, lat2, lon2) <= max_distance_m
