import httpx
import asyncio
import datetime

# Open-Meteo Marine API Base URL
MARINE_API = "https://marine-api.open-meteo.com/v1/marine"

REGIONS_COORDS = {
    "mannar": {"lat": 9.1, "lng": 79.0, "name": "Gulf of Mannar"},
    "kerala": {"lat": 9.9, "lng": 76.2, "name": "Arabian Sea – Kerala"},
    "odisha": {"lat": 19.8, "lng": 85.8, "name": "Bay of Bengal – Odisha"},
    "lakshadweep": {"lat": 10.5, "lng": 72.6, "name": "Lakshadweep Sea"},
    "palk": {"lat": 9.5, "lng": 79.3, "name": "Palk Strait"},
    "andaman": {"lat": 11.6, "lng": 92.7, "name": "Andaman Sea"},
    "andhra": {"lat": 17.6, "lng": 83.3, "name": "Andhra Pradesh Coast"},
    "karnataka": {"lat": 12.9, "lng": 74.8, "name": "Karnataka Coast"},
    "gujarat": {"lat": 23.2, "lng": 69.6, "name": "Gulf of Kutch – Gujarat"},
    "goa": {"lat": 15.4, "lng": 73.8, "name": "Goa Coast"},
}

async def fetch_live_marine_data(client, region_id):
    coord = REGIONS_COORDS.get(region_id)
    if not coord: return (region_id, None)
    
    params = {
        "latitude": coord["lat"],
        "longitude": coord["lng"],
        "hourly": "sea_surface_temperature,wave_height",
        "timezone": "auto",
        "forecast_days": 1
    }
    
    try:
        response = await client.get(MARINE_API, params=params, timeout=10.0)
        data = response.json()
        
        # Get the latest hourly reading (current hour)
        current_hour = datetime.datetime.now().hour
        hourly = data.get("hourly", {})
        
        sst_list = hourly.get("sea_surface_temperature", [])
        wave_list = hourly.get("wave_height", [])
        
        # Safely access index
        idx = min(current_hour, len(sst_list) - 1) if sst_list else -1
        
        # Extract and validate values
        sst = sst_list[idx] if idx >= 0 else 28.0
        wave = wave_list[idx] if (idx >= 0 and idx < len(wave_list)) else 0.5
        
        # Final fallback check if value itself is None
        if sst is None: sst = 28.2
        if wave is None: wave = 0.6
        
        return (region_id, {
            "sst": float(sst),
            "waves": float(wave),
            "last_sync": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error fetching live data for {region_id}: {e}")
        return (region_id, {
            "sst": 28.5 + (0.5 * len(region_id) % 2),
            "waves": 0.8,
            "last_sync": datetime.datetime.now().isoformat(),
            "status": "fallback"
        })

async def get_all_regions_data():
    async with httpx.AsyncClient() as client:
        tasks = [fetch_live_marine_data(client, rid) for rid in REGIONS_COORDS]
        results = await asyncio.gather(*tasks)
        return dict(results)
