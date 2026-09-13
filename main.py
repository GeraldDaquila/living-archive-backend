# USE PRODUCTION VERSION: v387 — secondary pathway relevance correction
# Preserve v386 proven Guide bridge; exclude acute-risk-specific secondary essays
# from ordinary grief navigation unless the visitor explicitly raises that domain.
# Protected use_core.py remains unchanged.
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v387"
DEPLOYMENT_FINGERPRINT = "USE-v387-secondary-pathway-relevance"
CANONICAL_BUILD_ID = "USE-BUILD-v387-secondary-pathway-relevance"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v387 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v387 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response
_original_recommendation_output_authority = getattr(use_core, "_enforce_recommendation_output_authority", None)
_original_recommendation_resource_identity = getattr(use_core, "_enforce_recommendation_resource_identity", None)
_original_violation = getattr(use_core, "_v308_compassionate_voice_violation", None)

def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    docs = []
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        tm = re.search(r"^Title:\s*(.+?)\s*$", block, re.M)
        um = re.search(r"^URL:\s*(https?://\S+)\s*$", block, re.M | re.I)
        cm = re.search(r"^Content:\s*(.*)$", block, re.M | re.S)
        if tm and um and cm:
            docs.append({"title": tm.group(1).strip(), "url": um.group(1).strip().rstrip(".,;"), "text": cm.group(1).strip()})
    return docs

def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "canonical_link_context", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            return str(kwargs[key])
    for index in (1, 2, 3, 4, 5):
        if len(args) > index and isinstance(args[index], str) and any(k in args[index] for k in ("Title:", "URL:", "Content:")):
            return args[index]
    return ""

def _normalize_title(text: str) -> str:
    return re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", str(text or "").strip()).strip()

def _resource_link(doc: dict) -> str:
    title = _normalize_title(doc.get("title") or "")
    url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return f"[{title}]({url})" if title and url else ""

def _query_profile(user_query: str, docs: list) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "sensitive": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one|trauma|abuse|coercion|suicid|self-harm|overdose)\b", q)),
        "grief": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|death|died|dying|loved one)\b", q)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief)\b", q)),
        "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|astrology|tarot)\b", q)),
    }

def _evidence_boundary_note(docs: list, profile: dict) -> str:
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    if has_science and has_spiritual:
        return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if has_spiritual:
        return "Where the material turns toward spiritual or afterlife possibilities, those are perspectives offered by the work rather than established facts you need to accept."
    if profile.get("meaning"):
        return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."

def _secondary_role(doc: dict, profile: dict) -> str:
    title = _normalize_title(doc.get("title") or "")
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
    corpus = f"{title} {text}"
    if re.search(r"\b(?:afterlife|reincarnation)\b", corpus, re.I): return "a broader exploration of what different traditions and experiences have made of life after death"
    if re.search(r"\b(?:continuity|connection|bond|relationship|identity|endure)\b", corpus, re.I): return "questions of continuity, connection, and what may endure"
    if re.search(r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b", corpus, re.I): return "the lived experience of loss and mortality"
    if re.search(r"\b(?:meaning|purpose|perspective|wisdom)\b", corpus, re.I): return "meaning, perspective, and ways of understanding the experience"
    if re.search(r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b", corpus, re.I): return "a more grounded or research-oriented way of looking at the question"
    if re.search(r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b", corpus, re.I): return "spiritual or contemplative possibilities"
    return "another perspective on the question"

def _is_acute_risk_resource(doc: dict) -> bool:
    title = _normalize_title(doc.get("title") or "")
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
    corpus = f"{title} {text}"
    return bool(re.search(r"\b(?:suicid(?:e|al|ality)|suicidal ideation|self-harm|overdose|acute crisis|crisis intervention|immediate danger)\b", corpus, re.I))

def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:
    seen = {_normalize_title(primary_title).casefold()}
    candidates = []
    used_roles = set()
    for doc in docs:
        title = _normalize_title(doc.get("title") or "")
        if not title or title.casefold() in seen:
            continue
        text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
        corpus = f"{title} {text}"
        if profile.get("sensitive") and not profile.get("explicit_framework") and not profile.get("risk") and _is_acute_risk_resource(doc):
            continue
        score = 0
        if profile.get("grief") and re.search(r"\b(?:grief|loss|death|mortality|meaning|continuity)\b", corpus, re.I): score += 3
        if profile.get("meaning") and re.search(r"\b(?:meaning|identity|purpose|perspective|wisdom|continuity)\b", corpus, re.I): score += 2
        role = _secondary_role(doc, profile)
        if role in used_roles: score -= 4
        if profile.get("sensitive") and not profile.get("explicit_framework") and re.search(r"\b(?:afterlife|reincarnation)\b", corpus, re.I): score -= 3
        if score > 0: candidates.append((score, role, title, doc))
    candidates.sort(key=lambda x: (-x[0], x[1].casefold(), x[2].casefold()))
    out = []
    for _, role, _, doc in candidates:
        if role in used_roles: continue
        out.append(doc); used_roles.add(role)
        if len(out) >= limit: break
    return out

def _extract_archive_metadata(doc: dict, docs: list) -> dict:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
    title = _normalize_title(doc.get("title") or "")
    def _first(patterns):
        for pattern in patterns:
            m = re.search(pattern, text, re.I)
            if m:
                phrase = re.sub(r"\s+", " ", m.group(1)).strip(" ,;:")
                if phrase and phrase.casefold() not in title.casefold(): return phrase
        return ""
    collection = _first([r"(?:collection|series)\s*[:\-]?\s*([^.!?]{3,100})", r"(?:within|inside|part of)\s+(?:the\s+)?(?:collection|series)\s+([^.!?]{3,100})"])
    section = _first([r"(?:section|chapter|part)\s*[:\-]?\s*([^.!?]{3,100})", r"(?:under|within)\s+(?:the\s+)?(?:section|chapter|part)\s+([^.!?]{3,100})"])
    page = _first([r"(?:page)\s*[:\-]?\s*([^.!?]{3,120})", r"(?:found|situated|located)\s+(?:within|under)\s+([^.!?]{3,120})"])
    related_titles = []
    for candidate in docs:
        candidate_title = _normalize_title(candidate.get("title") or "")
        if candidate_title and candidate_title.casefold() != title.casefold() and any(t in candidate_title.casefold() for t in ("grief", "loss", "death", "continuity", "mortality", "meaning", "journey")):
            related_titles.append(candidate_title)
    return {"collection": collection, "section": section, "page": page, "related_titles": related_titles[:3]}

def _archive_context(meta: dict) -> str:
    parts = []
    if meta.get("collection"): parts.append(f"It sits within {meta['collection']}")
    if meta.get("page"): parts.append(f"the surrounding page is {meta['page']}")
    if meta.get("section"): parts.append(f"where the material turns toward {meta['section']}")
    if not parts and meta.get("related_titles"):
        parts.append(f"It also belongs to a wider conversation in the Archive, alongside {', '.join(meta['related_titles'][:2])}")
    return " and ".join(parts).strip()

def _archive_bridge(profile: dict, meta: dict, secondaries: list) -> str:
    titles = [_normalize_title(v) for v in meta.get("related_titles") or [] if _normalize_title(v)]
    secondary_corpora = []
    for d in secondaries:
        title = _normalize_title(d.get("title") or "")
        text = re.sub(r"\s+", " ", str(d.get("text") or "").strip())
        secondary_corpora.append(f"{title} {text}")
    corpus = (" ".join(titles) + " " + " ".join(secondary_corpora)).casefold()
    axes = []
    if re.search(r"\b(?:continuity|connection|bond|relationship|identity|endure)\b", corpus): axes.append("continuity, connection, and what may endure")
    if re.search(r"\b(?:grief|loss|death|mortality|mourning|bereavement)\b", corpus): axes.append("the lived experience of loss and mortality")
    if profile.get("meaning") or re.search(r"\b(?:meaning|purpose|perspective|wisdom)\b", corpus): axes.append("the search for meaning when ordinary answers feel insufficient")
    if profile.get("sensitive"): axes.append("space for personal meaning without requiring certainty")
    axes = list(dict.fromkeys(axes))
    if not axes: return ""
    if len(axes) == 1: return f"Taken together, the nearby material gives this question a wider frame around {axes[0]}."
    if len(axes) == 2: return f"Taken together, the nearby material gives this question a wider frame around {axes[0]} and {axes[1]}."
    return f"Taken together, the nearby material gives this question a wider frame around {', '.join(axes[:-1])}, and {axes[-1]}."

def _guide_answer_architecture(user_query: str, primary: dict, docs: list) -> dict:
    profile = _query_profile(user_query, docs)
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I): return {}
    meta = _extract_archive_metadata(primary, docs)
    secondaries = _select_secondary_pathways(docs, title, profile)
    return {"profile": profile, "title": title, "url": url, "opening": "When you are grieving the death of someone you love, there may be no easy place to begin. Grief can bring pain, longing, questions, and uncertainty all at once." if profile.get("grief") else "A question like this is often easier to approach when there is a clear place to begin and room for the question to remain open.", "boundary": _evidence_boundary_note(docs, profile), "secondaries": secondaries, "archive_context": _archive_context(meta), "archive_bridge": _archive_bridge(profile, meta, secondaries)}

def _build_sensitive_recommendation_answer(user_query: str, primary: dict, docs: list) -> str:
    architecture = _guide_answer_architecture(user_query, primary, docs)
    if not architecture: return ""
    profile = architecture["profile"]
    sections = [architecture["opening"], f"A gentle place to begin is [{architecture['title']}]({architecture['url']}).", architecture["boundary"]]
    if architecture["archive_context"]: sections.append(architecture["archive_context"] + ".")
    if architecture["archive_bridge"]: sections.append(architecture["archive_bridge"])
    if architecture["secondaries"]:
        links = []
        for doc in architecture["secondaries"]:
            link = _resource_link(doc)
            if link: links.append(f"{link} — a way to explore {_secondary_role(doc, profile)}.")
        if links: sections.append("From there, you can follow a couple of nearby reflections:\n\n" + "\n\n".join(links))
    if profile.get("risk"): sections.append("The Archive can offer reflection and orientation, but where there is immediate danger or coercion, real-world safety and trusted human support matter more than reflection alone.")
    else: sections.append("You do not need to agree with every idea in these pieces. Take what feels useful, leave what does not, and let the questions remain open where they need to.")
    return "\n\n".join(s for s in sections if s)

def _transition_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "transition": bool(re.search(r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|beginning again|begin again|moving forward|identity|uncertain what comes next)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|why am i here|what is the point|what does it all mean|make sense|understand the experience)\b", q)),
        "open_question": bool(re.search(r"\b(?:how do i make sense|what do people believe|what are the possibilities|is there more|what happens after|what if there is no|i don't know what to believe|not sure what to believe|does anyone know|can anyone know|different perspectives|many perspectives|open question|no single answer|not sure|uncertain)\b", q)),
        "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|starseed|ascension|awakening|kundalini|soul|indigenous|traditional wisdom|ai|artificial intelligence|astrology|tarot|political|capitalism|socialism)\b", q)),
    }

def _transition_evidence_fit(doc: dict, query: str):
    title = _normalize_title(doc.get("title") or "").casefold()
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip()).casefold()
    hay = f"{title} {text}"
    clusters = {
        "transition": bool(re.search(r"\b(?:transition|change|chapter|starting over|moving forward|uncertain|flux|reorientation|turning point|new beginning|life change|before and after|crossroads|in-between|rebuild|reorient|adjust|adapt)\b", hay)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|identity|sensemaking|sense-making|making sense|what it means)\b", hay)),
        "experience": bool(re.search(r"\b(?:experience|lived|personal|human|everyday|relationships|routine|role|journey|navigate|navigating|felt|feeling)\b", hay)),
        "grounding": bool(re.search(r"\b(?:ground|grounding|practical|reflect|reflection|notice|naming|journal|practice|orientation)\b", hay)),
        "open": bool(re.search(r"\b(?:perspective|perspectives|possibilit|different views|different approaches|uncertainty|no single answer|question|open|ambiguous|ambiguity)\b", hay)),
        "worldview": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|astrology|tarot|political|capitalism|socialism)\b", hay)),
        "belief": bool(re.search(r"\b(?:belief|believe|faith|spiritual|religious|worldview)\b", hay)),
    }
    score = sum(int(clusters[k]) for k in ("transition", "meaning", "experience", "grounding", "open"))
    q = str(query or "").casefold()
    if re.search(r"\b(?:what comes next|major change|change in my life|life transition|new chapter|lost since|understand the experience|not sure what i believe|without being told what i should feel|without being told what i should believe)\b", q):
        if clusters["transition"] or clusters["meaning"] or clusters["experience"]: score += 2
    return score, clusters

def _is_query_aligned_transition_doorway(doc: dict, query: str) -> bool:
    profile = _transition_profile(query)
    if not profile["transition"] or profile["explicit_framework"]: return False
    score, clusters = _transition_evidence_fit(doc, query)
    if clusters["worldview"]: return False
    substantive = int(clusters["transition"]) + int(clusters["meaning"]) + int(clusters["experience"])
    contextual = int(clusters["open"]) + int(clusters["grounding"])
    return substantive >= 2 or (substantive >= 1 and contextual >= 1 and score >= 4)

def _transition_doorway_score(doc: dict, query: str) -> int:
    score, clusters = _transition_evidence_fit(doc, query)
    profile = _transition_profile(query)
    score *= 5
    if clusters["transition"] and profile["transition"]: score += 8
    if clusters["meaning"] and profile["meaning"]: score += 5
    if clusters["open"] and profile["open_question"]: score += 5
    if clusters["experience"]: score += 3
    if clusters["grounding"]: score += 3
    if clusters["belief"] and profile["open_question"] and not profile["explicit_framework"]: score -= 6
    if clusters["worldview"]: score -= 30
    return score

def _transition_retrieval_strategy(query: str):
    source = getattr(use_core, "_transition_retrieval_strategy", None)
    if callable(source):
        try: retrieved = source(query)
        except Exception: retrieved = []
    else: retrieved = []
    ranked = []; seen = set()
    for doc in list(retrieved or []):
        if not isinstance(doc, dict): continue
        key = str(doc.get("url") or doc.get("canonical_url") or doc.get("title") or "").casefold().rstrip("/")
        if not key or key in seen or not _is_query_aligned_transition_doorway(doc, query): continue
        seen.add(key); ranked.append((_transition_doorway_score(doc, query), doc))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in ranked[:4]]

def _direct_open_transition_response(query: str, docs: list) -> dict:
    if not docs: return {"response": "A possible place to begin is with the transition itself: what changed, what feels uncertain now, and what remains open rather than already decided. The material available here does not establish one particular belief about what your experience means, so the question can remain open while you explore it.", "resources": []}
    primary = docs[0]
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I): return {"response": "A possible place to begin is with the transition itself: what changed, what feels uncertain now, and what remains open.", "resources": []}
    return {"response": "A possible place to begin is with the transition itself: a major change can leave what comes next genuinely open, especially while you are still finding your own language for what the experience means. The material surfaced here can offer a lens for that inquiry without requiring you to adopt a particular belief.\n\nOne useful doorway is [" + title + "](" + url + ").", "resources": [{"title": title, "url": url}]}

def _v387_finalize(*args, **kwargs):
    user_query = str(kwargs.get("user_query") or (args[0] if args else "") or "")
    intent = str(kwargs.get("intent") or (args[2] if len(args) > 2 else "") or "")
    raw_context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(raw_context)
    if not user_query or intent != "TOPICAL_INQUIRY": return _original_generate_llm_response(*args, **kwargs)
    profile = _query_profile(user_query, docs)
    tprofile = _transition_profile(user_query)
    if tprofile["transition"] and tprofile["open_question"] and not tprofile["explicit_framework"]:
        recovered = _transition_retrieval_strategy(user_query)
        aligned = [doc for doc in docs if _is_query_aligned_transition_doorway(doc, user_query)]
        merged = []; seen = set()
        for doc in aligned + recovered:
            key = str(doc.get("url") or doc.get("canonical_url") or doc.get("title") or "").casefold().rstrip("/")
            if key and key not in seen: seen.add(key); merged.append(doc)
        calibrated = sorted(merged, key=lambda d: _transition_doorway_score(d, user_query), reverse=True)[:1]
        return _direct_open_transition_response(user_query, calibrated)
    if profile.get("sensitive") and use_core._is_recommendation_question(user_query):
        primary = use_core._adjudicate_recommendation_resource(docs, user_query) if docs else None
        if primary:
            answer = _build_sensitive_recommendation_answer(user_query, primary, docs)
            if answer: return answer
    return _original_generate_llm_response(*args, **kwargs)

app=use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v387 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v387_finalize
