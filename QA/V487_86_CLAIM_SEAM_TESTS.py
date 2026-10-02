"""v487.86 compatibility probe for shared claim normalization."""
from __future__ import annotations

import re
from shared_intelligence_primitives import normalize_claims

def legacy_claims(candidates):
    claims=[]; seen=set()
    for c in candidates:
        core=" ".join(str(c.get("sentence") or "").replace("..",".").strip().rstrip(".").split())
        if not core or len(core.split()) < 6: continue
        key=" ".join(re.sub(r"\W+"," ",core.casefold()).split())
        if key in seen: continue
        seen.add(key)
        claims.append({
            "text":core,
            "title":c.get("title",""),
            "url":c.get("url",""),
            "score":c.get("score",0),
            "epistemic":"interpretive" if c.get("worldview") else "supported",
        })
    return claims

def shared_claims(candidates):
    raw=[]
    for c in candidates:
        core=" ".join(str(c.get("sentence") or "").replace("..",".").strip().rstrip(".").split())
        if not core or len(core.split()) < 6: continue
        raw.append({
            "text":core,
            "evidence_ids":[str(c.get("id"))] if c.get("id") else [],
            "claim_type":"interpretation" if c.get("worldview") else "observation",
            "epistemic":"interpretive" if c.get("worldview") else "supported",
        })
    evidence_ids=[str(c.get("id")) for c in candidates if c.get("id")]
    return {item.text:item for item in normalize_claims(raw,evidence_ids=evidence_ids)}

def main()->int:
    cases=[
        {"id":"a","sentence":"A supported proposition about human attention.","title":"Attention","url":"https://geralddaquila.com/attention/","score":20,"worldview":False},
        {"id":"b","sentence":"A supported proposition about human attention.","title":"Attention","url":"https://geralddaquila.com/attention/","score":10,"worldview":False},
        {"id":"c","sentence":"A spiritual proposition about the human search for continuity.","title":"Continuity","url":"https://geralddaquila.com/continuity/","score":15,"worldview":True},
        {"id":"d","sentence":"Too short","title":"Ignored","url":"https://geralddaquila.com/ignored/","score":1,"worldview":False},
    ]
    legacy=legacy_claims(cases)
    shared=shared_claims(cases)
    assert len(legacy)==2
    assert list(shared)==[legacy[0]["text"],legacy[1]["text"]]
    assert shared[legacy[0]["text"]].evidence_ids==("a",)
    assert shared[legacy[0]["text"]].epistemic=="supported"
    assert shared[legacy[1]["text"]].evidence_ids==("c",)
    assert shared[legacy[1]["text"]].epistemic=="interpretive"
    assert shared[legacy[1]["text"]].claim_type=="interpretation"
    print("v487.86 claim normalization compatibility probes: PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
