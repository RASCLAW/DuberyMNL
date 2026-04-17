"""Central registration of all service monitors.

Imported once by app.py at startup. Each monitor module exposes `check()`
and optionally `EXPENSIVE = True` (for API-heavy checks gated behind
manual refresh).
"""
from __future__ import annotations

from monitors import register
from monitors import chatbot as m_chatbot
from monitors import tunnel as m_tunnel
from monitors import worker_fallback as m_worker
from monitors import meta_ads as m_ads
from monitors import story_rotation as m_story
from monitors import rasclaw_tg as m_rasclaw
from monitors import chatbot_tg as m_chatbot_tg
from monitors import crm_sheet as m_crm
from monitors import inventory as m_inventory


def _exp(mod) -> bool:
    return bool(getattr(mod, "EXPENSIVE", False))


def register_all() -> None:
    register("chatbot", m_chatbot.check, _exp(m_chatbot))
    register("tunnel", m_tunnel.check, _exp(m_tunnel))
    register("worker_fallback", m_worker.check, _exp(m_worker))
    register("meta_ads", m_ads.check, _exp(m_ads))
    register("story_rotation", m_story.check, _exp(m_story))
    register("rasclaw_tg", m_rasclaw.check, _exp(m_rasclaw))
    register("chatbot_tg", m_chatbot_tg.check, _exp(m_chatbot_tg))
    register("crm_sheet", m_crm.check, _exp(m_crm))
    register("inventory", m_inventory.check, _exp(m_inventory))
