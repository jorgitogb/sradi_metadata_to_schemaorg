import requests
import json
import logging
from typing import List, Dict, Any
import re
import html
import os


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://129.187.232.198:5000/api/3/action"
OUTPUT_FILE = "output/schema_org_metadata.json"

def fetch_package_list() -> List[str]:
    """Fetch the list of all package names from CKAN."""
    url = f"{BASE_URL}/package_list"
    logger.info(f"Fetching package list from {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return data["result"]
        else:
            logger.error(f"Failed to fetch package list: {data.get('error')}")
            return []
    except Exception as e:
        logger.error(f"Error fetching package list: {e}")
        return []

def fetch_package_details(package_id: str) -> Dict[str, Any]:
    """Fetch detailed metadata for a specific package."""
    url = f"{BASE_URL}/package_show?id={package_id}"
    logger.info(f"Fetching package details for: {package_id}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return data["result"]
        else:
            logger.error(f"Failed to fetch package details for {package_id}: {data.get('error')}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching package details for {package_id}: {e}")
        return {}

def try_parse_json_list(value: Any) -> List[Dict[str, Any]]:
    """Helper to parse JSON strings that should be lists of dicts (like author/maintainer)."""
    if not value or not isinstance(value, str):
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        return [parsed] if isinstance(parsed, dict) else []
    except (json.JSONDecodeError, TypeError):
        return []


def cleanup_text(text: Any) -> str:
    """Remove \r, \n, and all HTML tags from text."""
    if not text or not isinstance(text, str):
        return ""
    # Remove all HTML tags
    text = re.sub(r'<[^>]*>', ' ', text)
    # Unescape HTML entities (e.g., &amp; -> &)
    text = html.unescape(text)
    # Remove carriage returns and newlines
    text = text.replace('\r', ' ').replace('\n', ' ')
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_person_name(name: str) -> Dict[str, str]:
    """Split a full name into givenName and familyName."""
    if not name:
        return {}
    parts = name.strip().split()
    if len(parts) == 0:
        return {}
    if len(parts) == 1:
        return {"name": name, "givenName": name}
    
    # Simple split: first part as givenName, rest as familyName
    # Or last part as familyName, rest as givenName.
    # Usually: Given Family or Given Middle Family.
    # Let's go with Given Name as everything before the last space, 
    # and Family Name as the last space-separated word.
    given_name = " ".join(parts[:-1])
    family_name = parts[-1]
    return {
        "name": name,
        "givenName": given_name,
        "familyName": family_name
    }

def map_to_schema_org(ckan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map CKAN metadata to Schema.org Dataset format."""
    
    # Extract authors and maintainers
    authors_raw = try_parse_json_list(ckan_data.get("author"))
    creators = []
    for auth in authors_raw:
        name = auth.get("author_name")
        person = {"@type": "Person"}
        person.update(parse_person_name(name))
        if auth.get("author_email"):
            person["email"] = auth.get("author_email")
        if person.get("name"): # Only add if we have a name
            creators.append(person)

    maintainers_raw = try_parse_json_list(ckan_data.get("maintainer"))
    maintainers = []
    for maint in maintainers_raw:
        name = maint.get("maintainer_name")
        person = {"@type": "Person"}
        person.update(parse_person_name(name))
        if maint.get("maintainer_email"):
            person["email"] = maint.get("maintainer_email")
        if person.get("name"): # Only add if we have a name
            maintainers.append(person)

    # Keywords (Tags)
    keywords = [tag["display_name"] for tag in ckan_data.get("tags", []) if "display_name" in tag]

    # Distributions (Resources)
    distributions = []
    for res in ckan_data.get("resources", []):
        dist = {
            "@type": "DataDownload",
            "name": res.get("name"),
            "contentUrl": res.get("url"),
            "encodingFormat": res.get("format"),
            "description": cleanup_text(res.get("description"))
        }
        distributions.append(dist)

    schema_org = {
        "@context": "https://schema.org/",
        "@type": "Dataset",
        "name": ckan_data.get("title"),
        "description": cleanup_text(ckan_data.get("notes")),
        "identifier": ckan_data.get("id"),
        "url": f"http://129.187.232.198:5000/dataset/{ckan_data.get('name')}",
        "license": ckan_data.get("license_url") or ckan_data.get("license_title"),
        "datePublished": ckan_data.get("metadata_created"),
        "dateModified": ckan_data.get("metadata_modified"),
        "inLanguage": ckan_data.get("language"),
        "keywords": keywords,
        "creator": creators,
        "maintainer": maintainers,
        "distribution": distributions
    }
    
    # Add organization if available
    org_data = ckan_data.get("organization")
    if org_data:
        schema_org["publisher"] = {
            "@type": "Organization",
            "name": org_data.get("title"),
            "description": org_data.get("description")
        }

    return schema_org

def main():
    package_names = fetch_package_list()
    if not package_names:
        logger.warning("No packages found.")
        return

    # For large lists, we might want to limit for testing or handle pagination/bursting
    # For now, we process all.
    all_schema_metadata = []
    
    # LIMITING to first 5 for initial verification if needed, or remove for full run
    # For initial task, let's process all but be mindful of output size.
    for name in package_names:
        ckan_metadata = fetch_package_details(name)
        if ckan_metadata:
            schema_data = map_to_schema_org(ckan_metadata)
            all_schema_metadata.append(schema_data)

    
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir and not os.path.exists(output_dir):
        logger.info(f"Creating directory: {output_dir}")
        os.makedirs(output_dir)

    logger.info(f"Saving {len(all_schema_metadata)} datasets to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_schema_metadata, f, indent=2, ensure_ascii=False)
    
    logger.info("Transfer completed successfully.")

if __name__ == "__main__":
    main()
