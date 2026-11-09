"""Controlled publisher for the Living Archive canonical territorial map.

Pinecone remains the semantic retrieval layer. Canonical publication identity
comes from the public WordPress registry, so this workflow never enumerates the
vector database.
"""
from __future__ import annotations
import hashlib, html, json, re, time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/"archive_crosslink_snapshot.json"
CHECKSUM=ROOT/"archive_crosslink_snapshot.sha256"
BASE="https://geralddaquila.com/wp-json/wp/v2"
PAGE_SIZE=100
MAX_PAGES=50

def clean(value):
    return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",str(value or "")))).strip()

def load(kind):
    assets=[]
    for page in range(1,MAX_PAGES+1):
        req=Request(f"{BASE}/{kind}?per_page={PAGE_SIZE}&page={page}&status=publish&_fields=id,link,title",headers={"Accept":"application/json","User-Agent":"LivingArchiveSnapshot/2.0"})
        with urlopen(req,timeout=10) as response: payload=json.loads(response.read().decode("utf-8"))
        if not isinstance(payload,list): raise RuntimeError(f"WordPress {kind} registry response was not a list")
        for item in payload:
            title_obj=item.get("title")
            title=clean(title_obj.get("rendered") if isinstance(title_obj,dict) else title_obj)[:300]
            wp_id=str(item.get("id") or "").strip()
            url=str(item.get("link") or "").strip().rstrip("/")
            if wp_id.isdigit() and title and "ARCHIVED" not in title.upper() and re.match(r"^https://geralddaquila\.com/\S+$",url,re.I):
                assets.append({"title":title,"url":url,"wp_id":wp_id,"resource_type":kind[:-1],"tier":"public","access_class":"public","summary":""})
        if len(payload)<PAGE_SIZE: break
    else: raise RuntimeError(f"WordPress {kind} registry exceeded page limit")
    return assets

def main_publish():
    records=load("posts")+load("pages")
    assets={}
    for item in records:
        key=item["url"].casefold()
        existing=assets.get(key)
        if existing is None or (existing.get("resource_type")=="page" and item.get("resource_type")=="post"):
            assets[key]=item
    # A title is descriptive metadata, not a publication identity. Distinct
    # WordPress records with distinct canonical URLs must remain independently
    # addressable even when their normalized titles collide. Numeric URL suffixes
    # are also retained: deciding whether a record is superseded is an editorial
    # classification task, not something the publisher may infer silently.
    assets=list(assets.values())
    if not assets: raise RuntimeError("canonical WordPress registry returned no publishable assets")
    snapshot={"contract":"archive-crosslink-inventory-v2","crosslink_ready":True,"complete":True,"source":"wordpress-canonical-registry","asset_count":len(assets),"refreshed_at":time.time(),"assets":sorted(assets.values(),key=lambda x:(x["resource_type"],x["title"].casefold()))}
    raw=json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n"
    OUTPUT.write_text(raw,encoding="utf-8")
    digest=hashlib.sha256(raw.encode()).hexdigest()
    CHECKSUM.write_text(digest+"\n",encoding="utf-8")
    print(f"validated_snapshot=true source=wordpress assets={snapshot['asset_count']} sha256={digest}")
if __name__=="__main__": main_publish()
