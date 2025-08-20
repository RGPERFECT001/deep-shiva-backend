from fastapi import FastAPI, Query
from typing import List, Dict, Optional
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
import sys

app = FastAPI()


origins = [
    "http://localhost:8080", # Your frontend's local development address
    # "https://your-deployed-frontend.com", # TODO: Add your deployed frontend URL here later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)


def get_location_suggestions(latitude: float, longitude: float, radius: int = 2000) -> List[Dict]:
    """
    Fetch nearby clinics/hospitals using Overpass API.
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="clinic"](around:{radius},{latitude},{longitude});
      node["amenity"="hospital"](around:{radius},{latitude},{longitude});
    );
    out body;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    if response.status_code != 200:
        return []
    data = response.json()
    results = []
    for element in data.get('elements', []):
        name = element.get('tags', {}).get('name', 'Unknown')
        phone = element.get('tags', {}).get('phone', 'Not available')
        lat = element.get('lat')
        lon = element.get('lon')
        map_link = generate_map_link(lat, lon)
        results.append({
            'name': name,
            'phone': phone,
            'location': f"Latitude: {lat}, Longitude: {lon}",
            'map_link': map_link
        })
    return results

def generate_map_link(latitude: float, longitude: float) -> str:
    """
    Generate a Google Maps link to open the location in a browser.
    """
    return f"https://www.google.com/maps?q={latitude},{longitude}"

@app.get("/clinics_hospitals")
def clinics_hospitals(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
    radius: int = Query(2000, description="Radius in meters to search for clinics/hospitals")
):
    """
    Get nearby clinics and hospitals based on latitude, longitude, and radius.
    """
    suggestions = get_location_suggestions(latitude, longitude, radius)
    if suggestions:
        return {"results": suggestions}
    else:
        return {"results": [], "message": "No clinics or hospitals found within the specified radius."}

@app.get("/")
def root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Welcome to the Clinics and Hospitals API. Use /clinics_hospitals to find nearby clinics and hospitals."}


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8080)
