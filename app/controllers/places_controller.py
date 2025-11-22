# app/controllers/places_controller.py
from fastapi import APIRouter, Query, HTTPException
import httpx
import os

router = APIRouter(prefix="/places", tags=["Places"])

@router.get("/autocomplete")
async def autocomplete_address(q: str = Query(..., min_length=3)):
    """
    Proxy para Google Places Autocomplete API.
    Devuelve sugerencias de direcciones basadas en la consulta.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Google Maps API Key no configurada")
    
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": q,
        "key": api_key,
        "components": "country:pe",  # Restringir a Perú
        "language": "es"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error en Google Places API: {str(e)}")

@router.get("/reverse-geocode")
async def reverse_geocode(
    lat: float = Query(..., description="Latitud"),
    lng: float = Query(..., description="Longitud")
):
    """
    Proxy para Google Geocoding API (Reverse Geocoding).
    Devuelve la dirección formateada basada en coordenadas.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Google Maps API Key no configurada")
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": api_key,
        "language": "es"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error en Google Geocoding API: {str(e)}")
