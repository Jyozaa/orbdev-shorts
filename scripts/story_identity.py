"""Conservative identity matching across queue and published receipts."""
from __future__ import annotations
import re
from urllib.parse import urlsplit,unquote

STOP={"the","and","for","with","from","that","into","this","your","just","new","now","its","are","will","gets","out","has","was","why","what","how","a","an","is","to","of","in","on","by","at","it","ai"}
def normalized_url(url:str)->str:
    try:
        p=urlsplit(str(url).strip())
        host=p.netloc.lower().removeprefix("www.")
        path=re.sub(r"/+","/",unquote(p.path).strip("/").lower())
        return f"{host}/{path}" if host and path else ""
    except (ValueError,TypeError):return ""

def words(text:str)->set[str]:
    return {w for w in re.findall(r"[a-z0-9]+",str(text).lower()) if len(w)>=3 and w not in STOP}

def urls(row:dict)->set[str]:
    src=(row.get("editorial") or {}).get("sources")
    if not isinstance(src,list):src=row.get("sourceUrls") or []
    result=set()
    for entry in src:
        if isinstance(entry,str):url=entry
        elif isinstance(entry,dict):
            if entry.get("primary") is False:continue
            url=entry.get("url","")
        else:continue
        key=normalized_url(url)
        if key:result.add(key)
    return result

def duplicate(a:dict,b:dict)->bool:
    akey=(a.get("editorial") or {}).get("storyKey") or a.get("storyKey")
    bkey=(b.get("editorial") or {}).get("storyKey") or b.get("storyKey")
    if akey and bkey and str(akey)==str(bkey):return True
    sa=re.sub(r"[^a-z0-9]","",str(a.get("slug") or "").lower())
    sb=re.sub(r"[^a-z0-9]","",str(b.get("slug") or "").lower())
    if sa and sa==sb:return True
    if urls(a)&urls(b):return True
    ta=words(str(a.get("title") or a.get("headline") or ""))
    tb=words(str(b.get("title") or b.get("headline") or ""))
    return len(ta)>=4 and len(tb)>=4 and len(ta&tb)>=4 and len(ta&tb)/min(len(ta),len(tb))>=0.85
