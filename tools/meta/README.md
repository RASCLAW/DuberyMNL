# Meta Catalog API Tools

Tools for managing the DuberyMNL Facebook Commerce catalog via the Graph API.

## Setup

Add this to your `.env`:

```
META_CATALOG_TOKEN=<your system user token>
META_CATALOG_ID=1803474156468627
META_BUSINESS_ID=987721005024255
```

## How we got the token

1. Created a new **Business-type** app called **DuberyMNL Catalog** at developers.facebook.com
   - Use cases: all 9 (Marketing API, Catalog API, Messenger, Instagram, Pages, etc.)
2. Created a **System User** called **Claude API** (Admin role) in Business Manager
   - business.facebook.com/settings/system-users?business_id=987721005024255
3. Assigned the DuberyMNL Catalog app to the system user
4. Generated token with `catalog_management` + `business_management` permissions
   - System user token does NOT expire (set to Never when generating)

## Apps

| App | ID | Type | Purpose |
|-----|----|------|---------|
| DuberyMNL Automation | 908271865337799 | Facebook Login for Business | Legacy -- chatbot/page token |
| DuberyMNL Catalog | (check developers.facebook.com) | Business | Catalog management |

## System Users

| Name | ID | Role |
|------|----|------|
| Claude API | 61589341436755 | Admin |

## Tools

### `catalog_manager.py`

Create, read, and update products in the catalog.

```bash
# Create all products defined in PRODUCTS list
python tools/meta/catalog_manager.py create

# Read a specific product by ID
python tools/meta/catalog_manager.py get <product_id>
```

## Catalog

| Field | Value |
|-------|-------|
| Catalog ID | 1803474156468627 |
| Business ID | 987721005024255 |
| Commerce Manager | https://business.facebook.com/commerce/catalogs/1803474156468627/products/?business_id=987721005024255 |

## Product Fields

| Field | Format | Example |
|-------|--------|---------|
| `retailer_id` | slug | `rasta-brown` |
| `name` | string | `Dubery Rasta - Brown` |
| `description` | string | product copy |
| `price` | centavos (int) | `49900` = PHP 499 |
| `currency` | string | `PHP` |
| `availability` | string | `in stock` |
| `condition` | string | `new` |
| `url` | PDP URL | `https://duberymnl.com/products/item.html?slug=rasta-brown` |
| `image_url` | CDN URL | `https://duberymnl.com/assets/catalog/rasta-brown-card-shot.jpg` |

## Products Created

| Product | Retailer ID | Catalog Item ID |
|---------|-------------|-----------------|
| Rasta Brown | rasta-brown | 26620431140976536 |
