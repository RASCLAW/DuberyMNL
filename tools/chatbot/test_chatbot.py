"""
Local CLI chat for testing the DuberyMNL chatbot.

No Meta API needed -- calls conversation_engine directly.
Test product knowledge, Taglish responses, and handoff detection.

Usage:
    python tools/chatbot/test_chatbot.py
    python tools/chatbot/test_chatbot.py --sender test_user_123
"""

import argparse
import json
import sys
from pathlib import Path

# Add tools/chatbot to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from conversation_engine import generate_reply
from conversation_store import ConversationStore


def main():
    parser = argparse.ArgumentParser(description="Test DuberyMNL chatbot locally")
    parser.add_argument("--sender", default="test_user", help="Simulated sender ID")
    args = parser.parse_args()

    store = ConversationStore()
    sender_id = args.sender

    print("=" * 50)
    print("  DuberyMNL Chatbot -- Test Mode")
    print("  Type messages as a customer.")
    print("  Commands: 'quit', 'history', 'reset'")
    print("=" * 50)
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Bye!")
            break

        if user_input.lower() == "history":
            conv = store.get_or_create(sender_id)
            print(f"\n--- Conversation History ({len(conv['messages'])} messages) ---")
            for m in conv["messages"]:
                role = "You" if m["role"] == "user" else "Bot"
                print(f"  {role}: {m['content']}")
            print(f"  Intents: {conv['metadata']['detected_intents']}")
            print(f"  Handoff: {conv['metadata']['handoff_flagged']}")
            print("---\n")
            continue

        if user_input.lower() == "reset":
            from conversation_store import _new_conversation
            store._write(sender_id, _new_conversation(sender_id))
            print("Conversation reset.\n")
            continue

        # Get history for context
        history = store.get_history_for_claude(sender_id)

        # Save user message
        store.append_message(sender_id, "user", user_input)

        # Generate reply
        print("  (thinking...)")
        result = generate_reply(user_input, history)

        reply = result["reply_text"]
        intent = result.get("detected_intent", "unknown")
        confidence = result.get("confidence", 0)
        handoff = result.get("should_handoff", False)

        # Save bot reply
        store.append_message(sender_id, "assistant", reply, intent=intent)

        # Display
        print(f"Bot: {reply}")
        print(f"  [intent: {intent} | confidence: {confidence} | handoff: {handoff}]")

        if handoff:
            reason = result.get("handoff_reason", "bot_triggered")
            print(f"  ** HANDOFF TRIGGERED: {reason} **")
            store.flag_handoff(sender_id, reason)

        print()


if __name__ == "__main__":
    main()
