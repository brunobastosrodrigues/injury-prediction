def calculate_time_in_zones(heart_rate_stream, heart_rate_zones):
    time_in_zones = {zone: 0 for zone in heart_rate_zones.keys()}
    total_samples = len(heart_rate_stream)

    for hr in heart_rate_stream:
        for zone, (lower, upper) in heart_rate_zones.items():
            if lower <= hr <= upper:
                time_in_zones[zone] += 1
                break

    time_in_zones_percentage = {
        zone: (count / total_samples) * 100 if total_samples > 0 else 0.0
        for zone, count in time_in_zones.items()
    }
    return {
        "time_in_zones_raw": time_in_zones,
        "time_in_zones_percentage": time_in_zones_percentage,
    }
