"""
Meta Catalog Manager
Create, update, and list products in the DuberyMNL Facebook catalog.
"""
import requests
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

CATALOG_ID = "1803474156468627"
TOKEN = os.getenv("META_CATALOG_TOKEN")
if not TOKEN:
    raise RuntimeError("META_CATALOG_TOKEN not set in .env")
BASE_URL = "https://graph.facebook.com/v19.0"
BASE_SITE = "https://duberymnl.com"

PRODUCTS = [
    {
        "retailer_id": "bandits-matte-black",
        "name": "Dubery Bandits - Matte Black",
        "description": "Matte black frame with a red-mirror polarized lens. Tough finish, bold color. The everyday pair built for long drives and longer days.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=bandits-matte-black",
        "image_url": f"{BASE_SITE}/assets/catalog/bandits-matte-black-card-shot.jpg",
    },
    {
        "retailer_id": "bandits-glossy-black",
        "name": "Dubery Bandits - Glossy Black",
        "description": "Gloss-black frame with a smoked polarized lens. Clean, no-flash look that cuts glare without drawing attention. The pair that works everywhere.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=bandits-glossy-black",
        "image_url": f"{BASE_SITE}/assets/catalog/bandits-glossy-black-card-shot.jpg",
    },
    {
        "retailer_id": "bandits-green",
        "name": "Dubery Bandits - Green",
        "description": "Translucent frame with a green-mirror polarized lens. Light enough to show off the frame, bold enough to own the look.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=bandits-green",
        "image_url": f"{BASE_SITE}/assets/catalog/bandits-green-card-shot.jpg",
    },
    {
        "retailer_id": "bandits-blue",
        "name": "Dubery Bandits - Blue",
        "description": "Translucent frame with a blue-mirror polarized lens. Clean coastal look, light on the face. The pair that goes with everything.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=bandits-blue",
        "image_url": f"{BASE_SITE}/assets/catalog/bandits-blue-card-shot.jpg",
    },
    {
        "retailer_id": "bandits-tortoise",
        "name": "Dubery Bandits - Tortoise",
        "description": "Tortoise frame with a smoked brown polarized lens. Warm, rich tone that cuts glare and adds depth. The classic pair.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=bandits-tortoise",
        "image_url": f"{BASE_SITE}/assets/catalog/bandits-tortoise-card-shot.jpg",
    },
    {
        "retailer_id": "outback-black",
        "name": "Dubery Outback - Black",
        "description": "All-black Outback frame with smoked polarized lenses. Rubberized nose pads, spring hinges. Built for long drives and longer days.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=outback-black",
        "image_url": f"{BASE_SITE}/assets/catalog/hero-outback-black.png",
    },
    {
        "retailer_id": "outback-blue",
        "name": "Dubery Outback - Blue",
        "description": "Matte frame with a blue-mirror polarized lens. Built for bright days on the water — cuts glare, keeps the view.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=outback-blue",
        "image_url": f"{BASE_SITE}/assets/catalog/outback-blue-card-shot.jpg",
    },
    {
        "retailer_id": "outback-red",
        "name": "Dubery Outback - Red",
        "description": "Matte black frame with a red-mirror polarized lens. Bold on the road, built for the sun. The pair that turns heads.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=outback-red",
        "image_url": f"{BASE_SITE}/assets/catalog/outback-red-card-shot.jpg",
    },
    {
        "retailer_id": "outback-green",
        "name": "Dubery Outback - Green",
        "description": "Matte black frame with a green-mirror polarized lens. Boosts contrast on trails, water, and open roads. Built for the outdoors.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=outback-green",
        "image_url": f"{BASE_SITE}/assets/catalog/outback-green-card-shot.jpg",
    },
    {
        "retailer_id": "rasta-red",
        "name": "Dubery Rasta - Red",
        "description": "Matte black frame with a red-mirror polarized lens. Round profile, bold color. The pair that makes a statement without trying.",
        "price": 49900, "currency": "PHP", "availability": "in stock", "condition": "new",
        "url": f"{BASE_SITE}/products/item.html?slug=rasta-red",
        "image_url": f"{BASE_SITE}/assets/catalog/rasta-red-card-shot.jpg",
    },
]


def create_product(product: dict) -> dict:
    url = f"{BASE_URL}/{CATALOG_ID}/products"
    resp = requests.post(url, params={"access_token": TOKEN}, data=product)
    return resp.json()


def get_product(product_id: str) -> dict:
    url = f"{BASE_URL}/{product_id}"
    params = {
        "fields": "id,name,price,description,availability,condition,url,image_url,retailer_id",
        "access_token": TOKEN,
    }
    resp = requests.get(url, params=params)
    return resp.json()


def update_product(product_id: str, fields: dict) -> dict:
    url = f"{BASE_URL}/{product_id}"
    resp = requests.post(url, params={"access_token": TOKEN}, data=fields)
    return resp.json()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "create"

    if cmd == "create":
        for product in PRODUCTS:
            print(f"Creating: {product['name']} ...")
            result = create_product(product)
            print(json.dumps(result, indent=2))

    elif cmd == "get" and len(sys.argv) > 2:
        result = get_product(sys.argv[2])
        print(json.dumps(result, indent=2))
