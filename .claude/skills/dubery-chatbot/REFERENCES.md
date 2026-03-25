# References -- dubery-chatbot

## Reads
- tools/chatbot/knowledge_base.py (product specs, pricing, FAQ)
- Conversation history (per-user JSON files)

## Writes
- Conversation store (per-user JSON history)
- Escalation email to RA (via tools/chatbot/handoff.py)

## Depends On
- Flask server: tools/chatbot/messenger_webhook.py (port 5002)
- tools/chatbot/conversation_engine.py (Claude wrapper)
- tools/chatbot/conversation_store.py (JSON storage + locking)
- tools/chatbot/start_chatbot.sh (startup script + ngrok)
- Meta webhook (Facebook Messenger integration)

## Referenced By
- Independent workflow -- no cross-skill dependencies
