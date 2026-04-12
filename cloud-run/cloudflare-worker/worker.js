/**
 * DuberyMNL Chatbot Fallback Worker
 *
 * Sits in front of the Cloudflare Tunnel. When the laptop (origin) is up,
 * requests pass through transparently. When the origin is down (502/530),
 * the Worker sends a friendly fallback reply via Meta Send API so the
 * customer isn't left hanging.
 *
 * Secrets (set via `wrangler secret put`):
 *   PAGE_ACCESS_TOKEN - Meta Page Access Token
 *
 * Env vars (in wrangler.toml):
 *   VERIFY_TOKEN      - Messenger webhook verify token
 *   FALLBACK_MESSAGE  - The away message text
 */

const GRAPH_API = "https://graph.facebook.com/v21.0/me/messages";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // --- GET /webhook: Meta verification handshake ---
    if (request.method === "GET" && url.pathname === "/webhook") {
      // Try origin first
      try {
        const resp = await fetch(request);
        if (resp.status < 500) return resp;
      } catch (_) {}

      // Origin down -- handle verification ourselves
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
      // Clone body so we can read it if origin fails
      const bodyText = await request.text();

      // Forward to origin
      try {
        const originReq = new Request(request.url, {
          method: "POST",
          headers: request.headers,
          body: bodyText,
        });
        const resp = await fetch(originReq);

        if (resp.status < 500) {
          return resp; // Origin handled it -- pass through
        }
      } catch (_) {
        // Origin unreachable -- fall through to fallback
      }

      // --- Origin is down -- send fallback reply ---
      try {
        const body = JSON.parse(bodyText);
        if (body.object === "page") {
          for (const entry of body.entry || []) {
            for (const event of entry.messaging || []) {
              const senderId = event.sender?.id;
              const hasMessage = event.message?.text || event.message?.attachments;

              if (senderId && hasMessage) {
                await sendFallbackReply(senderId, env);
              }
            }
          }
        }
      } catch (e) {
        // Parsing failed -- still return 200 so Meta doesn't retry
      }

      return new Response("OK", { status: 200 });
    }

    // --- All other paths: pass through, show error if origin down ---
    try {
      const resp = await fetch(request);
      return resp;
    } catch (_) {
      return new Response(
        JSON.stringify({ status: "offline", message: "Chatbot is currently offline" }),
        { status: 503, headers: { "Content-Type": "application/json" } }
      );
    }
  },
};

async function sendFallbackReply(senderId, env) {
  const token = env.PAGE_ACCESS_TOKEN;
  if (!token) return;

  const resp = await fetch(`${GRAPH_API}?access_token=${token}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      recipient: { id: senderId },
      message: { text: env.FALLBACK_MESSAGE },
    }),
  });

  if (!resp.ok) {
    console.log(`Fallback reply failed: ${resp.status} ${await resp.text()}`);
  }
}
