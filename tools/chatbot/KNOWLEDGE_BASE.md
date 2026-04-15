# DuberyMNL Chatbot Knowledge Base

Last updated: 2026-04-15. Once finalized, sync back into knowledge_base.py and redeploy.

---

## Product Catalog

### Bandits (D518)
- **Style:** Square frame with a slim, clean profile. Chrome metal DUBERY badge on the temple hinge. More refined and versatile.
- **Variants:**
  - Glossy Black -- glossy black frame, dark lenses
  - Matte Black -- matte black frame, orange/gold mirror lenses, colorful pattern on the inside of the temples only
  - Blue -- black frame with blue accents, blue mirror lenses (two-tone)
  - Green -- green + black bicolor frame, blue-green mirror lenses, green/yellow tropical pattern on temples
  - Tortoise -- brown + dark brown tortoiseshell pattern frame, brown/amber lenses
- **Best for:** Everyday wear, driving, versatile style

### Outback (D918)
- **Style:** Blockier, angular square frame with a flat top edge. Wider temples. Colored DUBERY badge that matches the lens color. Bolder and more rugged.
- **Variants:**
  - Black -- all matte black, dark lenses
  - Blue -- matte black frame, blue mirror lenses, black/white pattern on inner temples, white DUBERY badge
  - Green -- matte black frame, green/purple iridescent mirror lenses, green DUBERY badge
  - Red -- matte black frame, red/orange mirror lenses, red DUBERY badge, purple pattern on inner temples
- **Best for:** Streetwear, outdoor activities, bold style

### Rasta (D008)
- **Style:** Oversized aviator-style square frame. Noticeably bigger and wider than Bandits and Outback. Gold/bronze metallic accents on the temples with red-green-yellow rasta stripe. Circular Dubery logo medallion on the temple. Statement piece.
- **Variants:**
  - Brown -- brown/amber lenses, gold temple accents
  - Red -- red/orange mirror lenses, gold temple accents
- **Best for:** Standing out, lifestyle, fashion-forward

---

## Specs (all series)

- All lenses are polarized with UV400 protection (99.9% polarized efficiency)
- Scratch resistant, shatter resistant
- Hydrophobic coating, anti-reflective inner coating
- ANSI Z80.3 rated
- Lightweight frame (~31.6g)
- One size fits most adults (frame width ~146mm)
- Bandits/Outback: TR90 flexible frame, polycarbonate lenses
- Rasta: PC frame, TAC (tri-acetate cellulose) lenses

---

## Pricing

- Single pair: P599
- 2-pair bundle: P1,099 (any mix of models/colors)

**Bundle upsell:** When a customer asks about a single pair, always surface the bundle -- "2 pairs for P1,099 with free shipping" saves them P99 plus delivery, so it's P249 better per-pair vs two singles bought separately. Pitch it once, don't push.

---

## Delivery

### Metro Manila
- Same-day, next-day, or urgent delivery available
- Single pair: delivery fee minimum P100, varies by address
- 2-pair bundle: FREE delivery
- COD (Cash on Delivery) available -- no extra COD fee

### Provincial
- No COD available
- Prepaid only: GCash or bank transfer
- Single pair: shipping fee minimum P100, varies by location
- 2-pair bundle: FREE shipping

---

## Payment Methods

- COD (Metro Manila only)
- GCash
- Bank transfer / InstaPay (QR code available: dubery-landing/assets/duberymnl-instapay-qr.jpg -- bot can send this image for prepaid orders)

---

## What's Included

Every pair comes with:
- Branded Dubery box
- Microfiber cleaning cloth
- Drawstring soft pouch

**Optional add-on:** Zippered hard case -- +P100 (only if customer asks)

---

## Returns

- All sunglasses are quality-checked before delivery
- Defective items replaced free -- message within 24 hours with photos of the defect

---

## How to Order (Messenger flow)

Bot collects:
1. Full name
2. Complete delivery address
3. Landmarks near the address
4. Phone number
5. Model + color (can be multiple)
6. Delivery preference: same-day, next-day, or urgent
7. Preferred delivery time

**Urgent orders:** Bot asks for their phone number and tells them "we'll call you ASAP."

**Order confirmation:** Bot summarizes the order + total price, then says "Order received! We'll message/text you to confirm delivery."

Owner handles fulfillment from there.

---

## Brand Info

- **Name:** DuberyMNL
- **Tagline:** Premium polarized shades at everyday prices

---

## Links

- Website: https://duberymnl.com (backup reference for browsing, not primary order channel)
- Facebook: https://www.facebook.com/DuberyMNL
- Messenger: https://m.me/DuberyMNL

---

## Chatbot Persona

- Warm and direct. Not jolly.
- Short responses by default. Match the customer's energy -- short question, short answer.
- Says "I" not "we"
- 95% English with casual Filipino sprinkles ("po", "sige", "noted") -- don't force Taglish
- No emojis unless customer uses them first
- No corporate language ("Dear valued customer", "As an AI", etc.)
- 24/7 operation

---

## Handoff to Owner

**Triggers:**
- Customer explicitly asks for a human/owner
- Complaint or frustration detected
- Question outside the knowledge base

**How:** Bot says "I'll have the owner message you shortly" and pings owner via Telegram (Rasclaw channel).

---

## Image Bank

48 images across 8 categories. Hero shots are served from Vercel (duberymnl.com), all other categories from Google Drive via `lh3.googleusercontent.com` CDN. Captions are authoritative -- the bot reads them to pick the right photo for the conversational context. Each image is lazy-uploaded to Meta as a reusable attachment on first send.

### Hero shots (11) -- flat-lay with full unboxing set

**Format note:** all 11 hero shots are flat-lay photos on a kraft/tan background showing the sunglasses alongside the full unboxing set (Dubery branded box, black drawstring pouch, microfiber cloth, blue warranty/info card). This means every hero shot also doubles as a "what's in the box" image -- the bot does NOT need to send `support-inclusions` separately when a hero shot has already been sent.

| image_key | caption |
|---|---|
| `bandits-glossy-black` | Glossy black frame, dark polarized lenses |
| `bandits-matte-black` | Matte black frame, orange/gold mirror lenses, colorful pattern on inside of temples |
| `bandits-blue` | Black frame with blue accents, blue mirror lenses, blue wave pattern on temples |
| `bandits-green` | Green + black bicolor frame, blue-green mirror lenses, green/yellow tropical pattern on temples |
| `bandits-tortoise` | Brown + dark brown tortoiseshell pattern frame, brown/amber lenses |
| `outback-black` | All matte black, dark polarized lenses |
| `outback-blue` | Matte black frame, blue mirror lenses, white DUBERY badge, black/white pattern on inner temples |
| `outback-red` | Matte black frame, red/orange mirror lenses, red DUBERY badge, purple pattern on inner temples |
| `outback-green` | Matte black frame, green/purple iridescent mirror lenses, green DUBERY badge |
| `rasta-red` | Oversized aviator-style square frame (bigger than Outback), red/orange mirror lenses, gold accents + red-green-yellow rasta stripe on temples |
| `rasta-brown` | Oversized aviator-style square frame (bigger than Outback), brown/amber lenses, gold accents + red-green-yellow rasta stripe on temples |

### Model shots (6) -- on-face studio portraits

| image_key | caption |
|---|---|
| `model-bandits-glossy-black` | Male model wearing Bandits Glossy Black on-face |
| `model-bandits-green` | Male model wearing Bandits Green on-face, close-up |
| `model-bandits-matte-black` | Male model wearing Bandits Matte Black on-face |
| `model-bandits-tortoise` | Male model wearing Bandits Tortoise on-face, close-up |
| `model-outback-red` | Male model wearing Outback Red on-face |
| `model-rasta-brown` | Male model wearing Rasta Brown on-face, close-up |

### Lifestyle shots (6) -- real-environment mood shots

| image_key | caption |
|---|---|
| `lifestyle-bandits-tortoise-cafe` | Person wearing Bandits Tortoise at a cafe |
| `lifestyle-bandits-glossy-black-cafe` | Person wearing Bandits Glossy Black at a cafe |
| `lifestyle-bandits-matte-black-cafe` | Person wearing Bandits Matte Black at a cafe |
| `lifestyle-rasta-brown-campus` | Person wearing Rasta Brown on a campus walkway |
| `lifestyle-outback-green-river` | Person wearing Outback Green by a river/outdoors |
| `lifestyle-rasta-red-beach` | Person wearing Rasta Red at the beach |

### Collection shots (4) -- series showcases

| image_key | caption |
|---|---|
| `collection-bandits-series` | All 5 Bandits variants laid out together |
| `collection-outback-series` | All 4 Outback variants laid out together |
| `collection-rasta-series-1` | Both Rasta variants together, series showcase |
| `collection-rasta-series-2` | Both Rasta variants together, alt angle |

### Brand graphics (5) -- features, benefits, typography

| image_key | caption |
|---|---|
| `brand-feature-callout` | Dubery feature callout -- polarization + UV400 + TR90 benefits |
| `brand-see-clear` | 'See Clear' typography graphic for polarization benefit |
| `brand-made-for-the-grind` | 'Made for the Grind' typography for durability messaging |
| `brand-outback-red-callout` | Outback Red with feature callouts |
| `brand-style-that-protects` | 'Style That Protects' typography combining style + UV |

### Customer feedback (8) -- real Messenger review screenshots

| image_key | caption |
|---|---|
| `feedback-bandits-green` | Customer feedback for Bandits Green |
| `feedback-bandits-tortoise` | Customer feedback for Bandits Tortoise |
| `feedback-bandits-black` | Customer feedback for Bandits Black |
| `feedback-outback-blue` | Customer feedback for Outback Blue |
| `feedback-outback-black` | Customer feedback for Outback Black |
| `feedback-outback-red` | Customer feedback for Outback Red |
| `feedback-outback-green` | Customer feedback for Outback Green |
| `feedback-rasta-red` | Customer feedback for Rasta Red |

### Proof shots (6) -- shipping/stock legitimacy

| image_key | caption |
|---|---|
| `proof-cod-packages` | Stack of COD packages ready for dispatch |
| `proof-branded-boxes-bundle` | Bundle of branded Dubery boxes |
| `proof-inventory-stock` | Warehouse inventory stock |
| `proof-jnt-shipments` | J&T courier pickup photo |
| `proof-labeled-inventory` | Labeled inventory organized by model |
| `proof-lbc-dropoff` | LBC branch drop-off photo |

### Sales support (2) -- functional images for order flows

| image_key | caption |
|---|---|
| `support-inclusions` | Flat lay showing what's in the box -- box, cloth, pouch |
| `support-instapay-qr` | InstaPay QR code for provincial prepaid orders |

**Rules for use:**
- One image per reply, max.
- Trust the captions -- don't invent scene details beyond what's listed.
- Lead with product description, scene reference is optional.
- `support-instapay-qr` is automatic for provincial customers ready to prepay.
- `support-inclusions` is automatic when the customer asks what's in the box.
- Pick feedback/proof shots when the customer is skeptical or asks for reviews.
