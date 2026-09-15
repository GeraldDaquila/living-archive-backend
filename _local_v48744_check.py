# local validation only; never deployed
import importlib
import runpy

m = importlib.import_module("main")
query = "I keep finding myself angry at someone I care about, and I don’t know what to do with that anger. Is there anything in the Living Archive that might help me think about it?"
profile = m._base._inquiry_profile(query)
docs = [
    {"title": "Suicide and the Journey of the Soul: A Unified Exploration of Mind, Spirit, and Society", "url": "https://geralddaquila.com/suicide", "text": "A discussion of suicide, despair, anger, and the soul."},
    {"title": "Unraveling Abuse: The Harm We Inherit, The Healing We Choose", "url": "https://geralddaquila.com/2025/06/01/unraveling-abuse-the-harm-we-inherit-the-healing-we-choose/", "text": "Abuse in relationships involves power, control, trauma, conflict, projection, and anger. The material examines cycles of harm and healing."},
    {"title": "Emotional Hijacking and the Search for Meaning: Reconnecting with Our True Needs Beyond Materialism", "url": "https://geralddaquila.com/2025/06/09/emotional-hijacking-and-the-search-for-meaning-reconnecting-with-our-true-needs-beyond-materialism/", "text": "Emotional hijacking includes intense emotional responses such as fear or anger. Mindful awareness and reflective practice can help identify emotional triggers and their true sources. The article examines emotional needs, neuroscience, self-reflection, and internal validation. " + ("The discussion remains focused on emotional awareness, triggers, needs, reflection, and practical sensemaking. " * 24) + "Later sections also discuss spiritual and metaphysical perspectives on inner fulfillment, including Buddhism, Advaita Vedanta, self-transcendence, meditation, and prayer."},
    {"title": "The Divine Feminine: Reawakening Sacred Balance in the Ascension Process and Its Intersections with Feminism", "url": "https://geralddaquila.com/divine-feminine", "text": "Sacred balance and spiritual transformation."},
]
assert profile["action"] == "recommendation"
answer, mode = m._unified_visitor_construction(query, docs, [docs[2], docs[0], docs[1], docs[3]])
assert mode == "recommendation"
assert answer.startswith("A useful place to begin with this question is [Emotional Hijacking")
assert "Suicide and the Journey of the Soul" not in answer
assert "The Divine Feminine" not in answer
assert m._role_evidence(docs[2])["worldview"] is False
assert m._role_evidence(docs[0])["risk"] is True
assert m._role_evidence(docs[1])["abuse"] is True
assert m._role_evidence(docs[3])["worldview"] is True
print("v487.44 direct anger doorway audit: PASS")
