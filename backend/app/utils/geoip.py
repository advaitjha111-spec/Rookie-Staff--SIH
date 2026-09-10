import os
import geoip2.database

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CITY_DB_PATH = os.path.join(BASE_DIR, "data", "geo", "GeoLite2-City.mmdb")
ASN_DB_PATH = os.path.join(BASE_DIR, "data", "geo", "GeoLite2-ASN.mmdb")

def get_geo_info(ip_address: str) -> dict:
    """
    Looks up IP geolocation and ASN/Hosting info from MaxMind offline databases.
    Gracefully degrades to "Unknown" if databases are missing.
    """
    info = {
        "country": "Unknown",
        "region": "Unknown",
        "city": "Unknown",
        "asn": "Unknown",
        "isp": "Unknown",
        "is_hosting": False,
        "latitude": None,
        "longitude": None
    }

    if not ip_address:
        return info

    # City Lookup
    if os.path.exists(CITY_DB_PATH):
        try:
            with geoip2.database.Reader(CITY_DB_PATH) as reader:
                response = reader.city(ip_address)
                info["country"] = response.country.name or "Unknown"
                if response.subdivisions:
                    info["region"] = response.subdivisions.most_specific.name or "Unknown"
                info["city"] = response.city.name or "Unknown"
                if response.location:
                    info["latitude"] = response.location.latitude
                    info["longitude"] = response.location.longitude
        except Exception as e:
            print(f"Error querying MaxMind City DB: {e}")

    # ASN Lookup
    if os.path.exists(ASN_DB_PATH):
        try:
            with geoip2.database.Reader(ASN_DB_PATH) as reader:
                response = reader.asn(ip_address)
                info["asn"] = f"AS{response.autonomous_system_number}" if response.autonomous_system_number else "Unknown"
                info["isp"] = response.autonomous_system_organization or "Unknown"
                
                # Heuristic to guess if it's a hosting provider instead of residential ISP
                isp_lower = info["isp"].lower()
                hosting_keywords = ["amazon", "aws", "google", "microsoft", "azure", "digitalocean", "linode", "ovh", "hetzner", "choopa", "vultr", "alibaba", "tencent"]
                if any(kw in isp_lower for kw in hosting_keywords):
                    info["is_hosting"] = True
        except Exception as e:
            print(f"Error querying MaxMind ASN DB: {e}")

    return info
