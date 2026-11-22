from decimal import Decimal, ROUND_HALF_UP


def calculate_price_per_hour(length_cm, width_cm, height_cm):
    """
    Calculate hourly parking price based on space volume.

    Volume in cubic metres =
        (length_cm * width_cm * height_cm) / 1,000,000
    """

    volume_m3 = (
        Decimal(length_cm)
        * Decimal(width_cm)
        * Decimal(height_cm)
        / Decimal("1000000")
    )

    from django.conf import settings

    price = volume_m3 * settings.PARKING_RATE_PER_M3_PER_HOUR

    return price.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
