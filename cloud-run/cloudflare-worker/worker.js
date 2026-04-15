/**
 * DuberyMNL Chatbot Fallback Worker
 *
 * Sits in front of the Cloudflare Tunnel. When the laptop (origin) is up,
 * requests pass through transparently. When origin is down:
 *   1. Send the customer a polite hold message (not "we're offline")
 *   2. Notify RA on Telegram so he can step in manually
 *
 * Skips fallback for Meta-generated events (quick_reply clicks, postbacks,
 * echoes, delivery/read receipts) -- those are Meta handling the customer
 * itself and piling on a hold message creates noise.
 *
 * Secrets (set via `wrangler secret put`):
 *   PAGE_ACCESS_TOKEN    - Meta Page Access Token
 *   TELEGRAM_BOT_TOKEN   - Rasclaw bot token for RA notifications
 *
 * Env vars (in wrangler.toml):
 *   VERIFY_TOKEN         - Messenger webhook verify token
 *   FALLBACK_MESSAGE     - Polite hold message sent to customer
 *   TG_CHAT_ID           - RA's Telegram chat ID
 */

const GRAPH_API_BASE = "https://graph.facebook.com/v21.0";

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
              // Fire-and-forget: polite hold to customer + TG ping to RA
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
  // Echo of our own page's outbound message
  if (event.message?.is_echo) return false;
  // Delivery / read receipts
  if (event.delivery || event.read) return false;
  // Postback (Meta-managed menu button)
  if (event.postback) return false;
  // Quick reply (Meta Instant Reply handles it)
  if (event.message?.quick_reply) return false;
  // Needs a sender and actual content
  const hasContent = Boolean(event.message?.text || event.message?.attachments);
  return Boolean(event.sender?.id) && hasContent;
}

async function handleFallback(senderId, messageText, env) {
  // Look up first name best-effort so the TG ping is readable
  const firstName = await getFirstName(senderId, env);
  // Send both in parallel; neither blocks the other
  await Promise.allSettled([
    sendHoldReply(senderId, env),
    notifyTelegram(senderId, firstName, messageText, env),
  ]);
}

async function sendHoldReply(senderId, env) {
  const token = env.PAGE_ACCESS_TOKEN;
  if (!token) return;
  const resp = await fetch(`${GRAPH_API_BASE}/me/messages?access_token=${token}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      recipient: { id: senderId },
      message: { text: env.FALLBACK_MESSAGE },
    }),
  });
  if (!resp.ok) {
    console.log(`Hold reply failed: ${resp.status} ${await resp.text()}`);
  }
}

async function notifyTelegram(senderId, firstName, messageText, env) {
  const token = env.TELEGRAM_BOT_TOKEN;
  const chatId = env.TG_CHAT_ID;
  if (!token || !chatId) return;

  const nameDisplay = firstName ? firstName : `ID ${senderId}`;
  const preview = (messageText || "(attachment, no text)").slice(0, 500);
  const text =
    `🔔 DuberyMNL customer waiting\n\n` +
    `${nameDisplay}: "${preview}"\n\n` +
    `Reply in Messenger:\nhttps://www.facebook.com/messages/t/${senderId}`;

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
