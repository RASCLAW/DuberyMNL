/**
 * DuberyMNL Chatbot Fallback Worker
 *
 * Sits in front of the Cloudflare Tunnel. When the laptop (origin) is up,
 * requests pass through transparently. When origin is down:
 *   1. Classify intent from the customer message
 *   2. Send a canned FAQ reply if intent matches, else polite hold
 *   3. Dedup per-sender per-intent via Workers KV (10 min TTL)
 *   4. Suppress polite hold if an FAQ reply already fired recently
 *
 * Telegram pings fire ONLY for order_intent (🚨). Routine FAQ-answered
 * questions and generic polite-hold messages handle themselves silently --
 * RA checks the inbox on his own cadence. This keeps TG noise tied to
 * moments where human action is actually required.
 *
 * Skips fallback for Meta-generated events (quick_reply clicks, postbacks,
 * echoes, delivery/read receipts).
 *
 * Secrets (set via `wrangler secret put`):
 *   PAGE_ACCESS_TOKEN    - Meta Page Access Token
 *   TELEGRAM_BOT_TOKEN   - Rasclaw bot token for order_intent urgent pings
 *
 * Env vars (in wrangler.toml):
 *   VERIFY_TOKEN         - Messenger webhook verify token
 *   FALLBACK_MESSAGE     - Polite hold message (fresh-contact fallback)
 *   TG_CHAT_ID           - RA's Telegram chat ID
 *
 * KV bindings (in wrangler.toml):
 *   FAQ_DEDUP            - per-sender per-intent dedup, 10min TTL
 */

const GRAPH_API_BASE = "https://graph.facebook.com/v21.0";
const DEDUP_TTL_SECONDS = 600; // 10 minutes
const DEDUP_INTENTS = ["pricing", "polarized", "shipping", "how_to_order"];

const DISCLAIMER =
  "\n\n(This is quick auto-reply po — owner will follow up for anything else soon 🙏)";

const TEMPLATES = {
  pricing:
    "Each pair is 499 po. Shipping fee is separate for a single pair (depends on your address). " +
    "Order 2 or more pairs and shipping is FREE — any mix of models.\n\n" +
    "Check out the full lineup: https://www.facebook.com/share/p/1SuARZpPUz/",

  polarized:
    "Yep po, all our lenses are polarized with UV400 protection. " +
    "Cuts out harsh glare from sun, road, and water — easier on your eyes, " +
    "clearer view overall.",

  shipping:
    "Shipping po:\n" +
    "- Single pair: shipping fee applies, varies by address\n" +
    "- Metro Manila: COD available\n" +
    "- Provincial: prepaid only (GCash/bank/InstaPay)\n" +
    "- Order 2 or more pairs: FREE shipping nationwide",

  how_to_order:
    "To order po, just send these details:\n\n" +
    "1. Full name\n" +
    "2. Complete delivery address\n" +
    "3. Nearest landmarks\n" +
    "4. Phone number\n" +
    "5. Model + color (e.g. Outback Blue)\n" +
    "6. COD or prepaid\n" +
    "7. Preferred delivery time\n\n" +
    "Owner will confirm total + shipping once received.",

  order_intent_reassurance:
    "Got it po 🙏 owner will reach out within a few minutes to confirm your order.",
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // --- GET /webhook: Meta verification handshake ---
    if (request.method === "GET" && url.pathname === "/webhook") {
      try {
        const resp = await fetch(request);
        if (resp.status < 500) return resp;
      } catch (_) {}

      const mode = url.searchParams.get("hub.mode");
      const token = url.searchParams.get("hub.verify_token");
      const challenge = url.searchParams.get("hub.challenge");
      if (mode === "subscribe" && token === env.VERIFY_TOKEN) {
        return new Response(challenge, { status: 200 });
      }
      return new Response("Forbidden", { status: 403 });
    }

    // --- POST /webhook: incoming Messenger messages ---
    if (request.method === "POST" && url.pathname === "/webhook") {
      const bodyText = await request.text();

      // Try origin first -- forward headers (incl. X-Hub-Signature-256) + body
      try {
        const originReq = new Request(request.url, {
          method: "POST",
          headers: request.headers,
          body: bodyText,
        });
        const resp = await fetch(originReq);
        if (resp.status < 500) return resp;
      } catch (_) {
        // Origin unreachable -- fall through
      }

      // Origin is down -- parse payload and handle each qualifying event
      try {
        const body = JSON.parse(bodyText);
        if (body.object === "page") {
          for (const entry of body.entry || []) {
            for (const event of entry.messaging || []) {
              if (!isCustomerMessage(event)) continue;
              const senderId = event.sender.id;
              const messageText = event.message?.text || "";
              ctx.waitUntil(handleFallback(senderId, messageText, env));
            }
          }
        }
      } catch (_) {
        // Parse failure -- still 200 so Meta doesn't retry
      }
      return new Response("OK", { status: 200 });
    }

    // --- All other paths: pass through; 503 if origin down ---
    try {
      return await fetch(request);
    } catch (_) {
      return new Response(
        JSON.stringify({ status: "offline", message: "Chatbot is currently offline" }),
        { status: 503, headers: { "Content-Type": "application/json" } }
      );
    }
  },
};

function isCustomerMessage(event) {
  if (event.message?.is_echo) return false;
  if (event.delivery || event.read) return false;
  if (event.postback) return false;
  if (event.message?.quick_reply) return false;
  const hasContent = Boolean(event.message?.text || event.message?.attachments);
  return Boolean(event.sender?.id) && hasContent;
}

// --- Intent classification -------------------------------------------------

function classifyIntent(text) {
  if (!text) return null;
  const lower = text.toLowerCase();

  // order_intent: phone (09xxxxxxxxx) + any address keyword
  const hasPhone = /\b09\d{9}\b/.test(text);
  const hasAddress = /\b(st\.?|street|brgy\.?|barangay|city|subd\.?|village|ave\.?|avenue|road|rd\.?|purok|sitio|phase|block|blk\.?|lot)\b/i.test(text);
  if (hasPhone && hasAddress) return "order_intent";

  // how_to_order (priority over pricing — "how to order" contains "how")
  if (/how to order|paano (po )?(mag[- ]?)?order|pano (po )?(mag[- ]?)?order|pa[- ]?order|order po\b|steps? to order/i.test(lower)) {
    return "how_to_order";
  }

  // pricing — explicit price words + PH shorthand
  if (/\bhow much\b|\bmagkano\b|\bprice\b|\bpresyo\b|\bhm\b|\btag\??\b/i.test(lower)) {
    return "pricing";
  }
  // Standalone "how" (Kingpin pattern) or bare "?"
  if (/^how\s*\??$/i.test(lower.trim()) || /^\?+$/.test(lower.trim())) {
    return "pricing";
  }

  // shipping
  if (/\bship(ping|ment)?\b|\bsf\b|\bdelivery fee\b|\bmagkano ang ship\b|\bshipping fee\b/i.test(lower)) {
    return "shipping";
  }

  // polarized
  if (/polariz(ed|e)|\bpola\b/i.test(lower)) {
    return "polarized";
  }

  return null;
}

function buildFaqResponse(intent) {
  if (intent === "order_intent") return TEMPLATES.order_intent_reassurance;
  return TEMPLATES[intent] + DISCLAIMER;
}

// --- KV dedup helpers ------------------------------------------------------

async function wasIntentDeduped(senderId, intent, env) {
  if (!env.FAQ_DEDUP) return false;
  const key = `faq:${senderId}:${intent}`;
  return (await env.FAQ_DEDUP.get(key)) !== null;
}

async function markIntentFired(senderId, intent, env) {
  if (!env.FAQ_DEDUP) return;
  const key = `faq:${senderId}:${intent}`;
  await env.FAQ_DEDUP.put(key, "1", { expirationTtl: DEDUP_TTL_SECONDS });
}

async function hasAnyRecentFaq(senderId, env) {
  if (!env.FAQ_DEDUP) return false;
  for (const intent of DEDUP_INTENTS) {
    const key = `faq:${senderId}:${intent}`;
    if ((await env.FAQ_DEDUP.get(key)) !== null) return true;
  }
  return false;
}

// --- Fallback orchestration ------------------------------------------------

async function handleFallback(senderId, messageText, env) {
  const intent = classifyIntent(messageText);

  // ORDER INTENT: reassurance + urgent TG, bypasses dedup.
  // This is the only path that pings RA.
  if (intent === "order_intent") {
    const firstName = await getFirstName(senderId, env);
    await Promise.allSettled([
      sendReply(senderId, TEMPLATES.order_intent_reassurance, env),
      notifyTelegramUrgent(senderId, firstName, messageText, env),
    ]);
    return;
  }

  // FAQ INTENT matched — template only, no TG ping
  if (intent) {
    if (await wasIntentDeduped(senderId, intent, env)) return;
    await sendReply(senderId, buildFaqResponse(intent), env);
    await markIntentFired(senderId, intent, env);
    return;
  }

  // NO INTENT matched — if we already canned-replied this sender, stay silent
  // (suppresses the follow-up polite-hold that used to trigger the triple-reply)
  if (await hasAnyRecentFaq(senderId, env)) return;

  // Fresh contact — polite hold only, no TG ping
  await sendReply(senderId, env.FALLBACK_MESSAGE, env);
}

// --- Outbound send ---------------------------------------------------------

async function sendReply(senderId, text, env) {
  const token = env.PAGE_ACCESS_TOKEN;
  if (!token) return;
  const resp = await fetch(`${GRAPH_API_BASE}/me/messages?access_token=${token}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      recipient: { id: senderId },
      message: { text },
    }),
  });
  if (!resp.ok) {
    console.log(`Send failed: ${resp.status} ${await resp.text()}`);
  }
}

// --- Telegram notifications (order_intent only) ----------------------------

async function notifyTelegramUrgent(senderId, firstName, messageText, env) {
  const nameDisplay = firstName ? firstName : `ID ${senderId}`;
  const preview = (messageText || "(attachment, no text)").slice(0, 500);
  const text =
    `🚨 ORDER INTENT — origin down\n\n` +
    `${nameDisplay}: "${preview}"\n\n` +
    `Reply NOW: https://www.facebook.com/messages/t/${senderId}`;
  await sendTelegram(text, env);
}

async function sendTelegram(text, env) {
  const token = env.TELEGRAM_BOT_TOKEN;
  const chatId = env.TG_CHAT_ID;
  if (!token || !chatId) return;
  const resp = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      disable_web_page_preview: true,
    }),
  });
  if (!resp.ok) {
    console.log(`TG notify failed: ${resp.status} ${await resp.text()}`);
  }
}

// --- Graph API helpers -----------------------------------------------------

async function getFirstName(senderId, env) {
  const token = env.PAGE_ACCESS_TOKEN;
  if (!token) return null;
  try {
    const resp = await fetch(
      `${GRAPH_API_BASE}/${senderId}?fields=first_name&access_token=${token}`
    );
    if (!resp.ok) return null;
    const data = await resp.json();
    return data.first_name || null;
  } catch (_) {
    return null;
  }
}
