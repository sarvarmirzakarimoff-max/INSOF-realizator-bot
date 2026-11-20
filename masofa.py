"""Zavoddan obyektgacha yo'l masofasi (km).

Avval bepul OSRM xizmati orqali haqiqiy yo'l bo'yicha masofa olinadi.
Internet yoki xizmat ishlamasa, to'g'ri chiziq masofasi × 1.3 olinadi.
"""
import math

import aiohttp

from config import ZAVOD_LAT, ZAVOD_LON

OSRM = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"


def togri_chiziq_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


async def yol_masofa_km(lat: float, lon: float) -> tuple[float, str]:
    """(km, manba) qaytaradi. manba: 'yo'l' yoki 'taxminiy'."""
    url = OSRM.format(lat1=ZAVOD_LAT, lon1=ZAVOD_LON, lat2=lat, lon2=lon)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as s:
            async with s.get(url) as r:
                js = await r.json()
                metr = js["routes"][0]["distance"]
                return round(metr / 1000, 1), "yo'l"
    except Exception:
        km = togri_chiziq_km(ZAVOD_LAT, ZAVOD_LON, lat, lon) * 1.3
        return round(km, 1), "taxminiy"
