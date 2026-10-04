from __future__ import annotations
import argparse,base64,html,json,os,re,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo
USER_AGENT="orbdev-editorial/1.0 (+https://github.com/Jyozaa/orbdev-shorts)"
ROLES={"fact","setup","explanation","analogy","joke","reaction","punchline","callback","transition"}
VISUALS={"source","kinetic","metric","logo","explain","comparison"};ABSTRACT={"explain","comparison"}
EXPLAIN={"pixel-upscale","network-shrink","capacity","stability","pipeline","fanout"};SFX={"scratch","impact","whoosh","tick","none"}
MEME_PURPOSES={"reaction","punchline","contrast","confusion","failure","success","waiting","absurdity","emphasis","none"}
MEME_TONES={"positive","negative","surprised","confused","awkward","deadpan","chaotic","neutral"};MEDIA={"audio","image","video","any"};PRESENTATIONS={"auto","overlay","cutaway"}
def clean(v:str)->str:return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",v or ""))).strip()
def slugify(v:str,limit:int=72)->str:
    v=re.sub(r"[^a-z0-9]+","-",v.lower().replace("&"," and ")).strip("-");return (re.sub(r"-+","-",v)[:limit].rstrip("-") or "orbdev-story")
def norm_url(url:str)->str:
    try:p=urllib.parse.urlparse(url)
    except Exception:return ""
    if p.scheme!="https" or not p.netloc:return ""
    q=[(k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith("utm_") and k.lower() not in {"ref","source"}]
    return urllib.parse.urlunparse(("https",p.netloc.lower().removeprefix("www."),p.path.rstrip("/"),"",urllib.parse.urlencode(q),""))
def host(url:str)->str:
    try:return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:return ""
def same_host(a:str,b:str)->bool:
    x,y=host(a),host(b);return bool(x and y and (x==y or x.endswith("."+y) or y.endswith("."+x)))
def load(p:Path,f:Any)->Any:return json.loads(p.read_text(encoding="utf-8")) if p.exists() else f
def fetch(url:str,headers:dict[str,str]|None=None,limit:int=800000)->tuple[str,str]:
    h={"User-Agent":USER_AGENT,"Accept-Language":"en-GB,en;q=0.9"}
    if headers:h.update(headers)
    with urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=18) as r:
        raw=r.read(limit);return raw.decode(r.headers.get_content_charset() or "utf-8",errors="replace"),r.geturl()
def source_snapshot(url:str)->str:
    if host(url)=="github.com":
        parts=[p for p in urllib.parse.urlparse(url).path.split("/") if p]
        if len(parts)>=2:
            h={"Accept":"application/vnd.github+json"};token=os.getenv("GITHUB_TOKEN","").strip()
            if token:h["Authorization"]=f"Bearer {token}"
            try:
                raw,_=fetch(f"https://api.github.com/repos/{parts[0]}/{parts[1]}/readme",h);payload=json.loads(raw)
                return clean(base64.b64decode(payload.get("content","")).decode("utf-8",errors="replace"))[:9000]
            except Exception:pass
    if host(url)=="huggingface.co":
        parts=[p for p in urllib.parse.urlparse(url).path.split("/") if p]
        if len(parts)>=2:
            try:body,_=fetch(f"https://huggingface.co/{parts[0]}/{parts[1]}/raw/main/README.md");return clean(body)[:9000]
            except Exception:pass
    try:
        body,_=fetch(url);body=re.sub(r"<script\b[^>]*>.*?</script>"," ",body,flags=re.I|re.S);body=re.sub(r"<style\b[^>]*>.*?</style>"," ",body,flags=re.I|re.S);return clean(body)[:9000]
    except Exception:return ""
def heat_bonus(item:dict[str,Any],threshold:float=7.2)->float:
    score=float(item.get("score") or 0);lanes=item.get("lanes") or [];creators=item.get("creators") or [];sources=item.get("sourceNames") or [];signals=set(item.get("signals") or [])
    h=.15+min(.55,max(0.0,score-threshold)*.16)
    if len(lanes)>=2:h+=.35
    if len(sources)>=2:h+=.18
    h+=min(.25,len(creators)*.10)
    if "github-trending" in signals:h+=.30
    if "hacker-news" in signals:h+=.20
    if "hugging-face" in signals:h+=.15
    return round(min(2.0,h),2)
def previous_decision(state:dict[str,Any],cid:str)->dict[str,Any]|None:
    for d in reversed(state.get("decisions") or []):
        if d.get("clusterId")==cid:return d
    return None
def should_recheck(item:dict[str,Any],state:dict[str,Any],now:datetime,hours:float,delta:float)->tuple[bool,str]:
    prev=previous_decision(state,str(item.get("clusterId","")))
    if not prev:return True,"new"
    if prev.get("decision") in {"accepted","queued","published"}:return False,"already accepted"
    try:
        dt=datetime.fromisoformat(str(prev.get("decidedAt")));dt=dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc);age=(now.astimezone(timezone.utc)-dt.astimezone(timezone.utc)).total_seconds()/3600
    except Exception:age=9999
    if age<hours and float(item.get("score") or 0)<float(prev.get("discoveryScore") or 0)+delta:return False,"recent rejection without new heat"
    return True,"recheck"
def compact(i:dict[str,Any])->dict[str,Any]:
    b=i.get("bestCandidate") or {}
    return {"clusterId":i.get("clusterId"),"title":i.get("title"),"discoveryScore":i.get("score"),"lanes":i.get("lanes") or [],"creators":i.get("creators") or [],"creatorCategories":i.get("creatorCategories") or [],"signals":i.get("signals") or [],"qualityGate":i.get("qualityGate"),"primaryUrls":i.get("primaryUrls") or [],"relatedUrls":i.get("relatedUrls") or [],"sourceNames":i.get("sourceNames") or [],"sourceKind":b.get("sourceKind"),"summary":str(b.get("summary") or "")[:1600],"metrics":b.get("metrics") or {}}
def triage_schema()->dict[str,Any]:
    return {"type":"object","properties":{"decisions":{"type":"array","items":{"type":"object","properties":{"clusterId":{"type":"string"},"pursue":{"type":"boolean"},"interestScore":{"type":"number"},"reason":{"type":"string"}},"required":["clusterId","pursue","interestScore","reason"],"additionalProperties":False}}},"required":["decisions"],"additionalProperties":False}
def review_schema()->dict[str,Any]:
    src={"type":"object","properties":{"title":{"type":"string"},"publisher":{"type":"string"},"url":{"type":"string"},"publishedAt":{"type":"string"},"primary":{"type":"boolean"}},"required":["title","publisher","url","publishedAt","primary"],"additionalProperties":False}
    beat={"type":"object","properties":{"text":{"type":"string"},"editorialRole":{"type":"string","enum":sorted(ROLES)},"visualType":{"type":"string","enum":sorted(VISUALS)},"sourceIndex":{"type":"integer"},"visualQuery":{"type":"string"},"mustMatch":{"type":"array","items":{"type":"string"}},"visualLabel":{"type":"string"},"visualAltLabel":{"type":"string"},"explainMode":{"type":"string","enum":sorted(EXPLAIN)},"metricValue":{"type":"string"},"logoSlug":{"type":"string"},"sfx":{"type":"string","enum":sorted(SFX)},"memePurpose":{"type":"string","enum":sorted(MEME_PURPOSES)},"memeTone":{"type":"string","enum":sorted(MEME_TONES)},"memeIntensity":{"type":"integer"},"memeMedia":{"type":"string","enum":sorted(MEDIA)},"memePresentation":{"type":"string","enum":sorted(PRESENTATIONS)},"memeMaxDurationSeconds":{"type":"number"},"memeConcepts":{"type":"array","items":{"type":"string"}}},"required":["text","editorialRole","visualType","sourceIndex","visualQuery","mustMatch","visualLabel","visualAltLabel","explainMode","metricValue","logoSlug","sfx","memePurpose","memeTone","memeIntensity","memeMedia","memePresentation","memeMaxDurationSeconds","memeConcepts"],"additionalProperties":False}
    return {"type":"object","properties":{"accept":{"type":"boolean"},"rejectionReason":{"type":"string"},"headline":{"type":"string"},"slug":{"type":"string"},"storyKey":{"type":"string"},"topics":{"type":"array","items":{"type":"string"}},"companies":{"type":"array","items":{"type":"string"}},"whyItMatters":{"type":"string"},"caveat":{"type":"string"},"rubric":{"type":"object","properties":{"significance":{"type":"number"},"practicalImpact":{"type":"number"},"novelty":{"type":"number"},"sourceConfidence":{"type":"number"},"visualClarity":{"type":"number"}},"required":["significance","practicalImpact","novelty","sourceConfidence","visualClarity"],"additionalProperties":False},"sources":{"type":"array","items":src},"beats":{"type":"array","items":beat},"publish":{"type":"object","properties":{"youtubeTitle":{"type":"string"},"description":{"type":"string"},"tags":{"type":"array","items":{"type":"string"}},"category":{"type":"string"}},"required":["youtubeTitle","description","tags","category"],"additionalProperties":False}},"required":["accept","rejectionReason","headline","slug","storyKey","topics","companies","whyItMatters","caveat","rubric","sources","beats","publish"],"additionalProperties":False}
def model_json(client:Any,model:str,input_items:list[dict[str,str]],schema:dict[str,Any],name:str,effort:str="low",tools:list[dict[str,Any]]|None=None,tool_choice:str|None=None)->tuple[dict[str,Any],Any]:
    kw={"model":model,"input":input_items,"reasoning":{"effort":effort},"text":{"format":{"type":"json_schema","name":name,"strict":True,"schema":schema}}}
    if tools:kw["tools"]=tools
    if tool_choice:kw["tool_choice"]=tool_choice
    r=client.responses.create(**kw)
    if not r.output_text:raise RuntimeError("model returned no output")
    return json.loads(r.output_text),r
def response_urls(r:Any)->set[str]:
    try:data=r.model_dump()
    except Exception:return set()
    out=set()
    def walk(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k=="url" and isinstance(x,str):
                    u=norm_url(x)
                    if u:out.add(u)
                walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    walk(data);return out
def known_context(i:dict[str,Any])->tuple[list[str],str]:
    urls=[]
    for k in ("primaryUrls","relatedUrls"):
        for raw in i.get(k) or []:
            u=norm_url(str(raw))
            if u and u not in urls:urls.append(u)
    pieces=[]
    for u in urls[:4]:
        s=source_snapshot(u)
        if s:pieces.append("SOURCE "+u+"\n"+s)
    return urls,"\n\n".join(pieces)[:30000]
def source_backed(url:str,known:list[str],cited:set[str],domains:list[str])->bool:
    u=norm_url(url)
    if not u:return False
    if u in {norm_url(x) for x in known}:return True
    h=host(u)
    if h in {"github.com","huggingface.co","arxiv.org"} or any(h==d or h.endswith("."+d) for d in domains):return True
    return any(u==c or same_host(u,c) for c in cited)
def base_score(r:dict[str,Any])->float:
    limits={"significance":4,"practicalImpact":2,"novelty":2,"sourceConfidence":1,"visualClarity":1}
    return round(sum(max(0,min(hi,float(r.get(k) or 0))) for k,hi in limits.items()),2)
def triage(client:Any,items:list[dict[str,Any]],model:str)->dict[str,dict[str,Any]]:
    if not items:return {}
    sysmsg="You are Orbdev's first-pass editor. Pursue timely specific technical stories AI/developer viewers would care about. Preserve niche open-source tools with real momentum. Reject generic marketing repos, tutorial collections, sponsor segments, finance/culture stories, stale projects without a current angle, and weak announcements. Creator mentions are discovery signals, not proof. Return JSON only."
    result,_=model_json(client,model,[{"role":"system","content":sysmsg},{"role":"user","content":json.dumps([compact(x) for x in items])}],triage_schema(),"orbdev_triage")
    out={str(x.get("clusterId")):x for x in result.get("decisions",[]) if x.get("clusterId")}
    for i in items:
        cid=str(i.get("clusterId"));out.setdefault(cid,{"clusterId":cid,"pursue":True,"interestScore":float(i.get("score") or 0),"reason":"fail-open"})
    return out
def final_review(client:Any,item:dict[str,Any],policy:dict[str,Any],system_prompt:str,model:str,repair:str="")->tuple[dict[str,Any],set[str],list[str]]:
    known,snapshot=known_context(item);h=heat_bonus(item,float(policy.get("minimumScore") or 7.2))
    prompt=f"""Verify this technical-news candidate using live web search. At least one primary source is mandatory: official announcement, project GitHub/model card, release notes, or paper. Creator commentary is only a lead. Reject unsupported hype, generic marketing, hiring/funding/partnership stories, or stale topics with no meaningful current momentum. Attribute vendor benchmarks.

If accepted, write an ORIGINAL Orbdev script: 80-105 spoken words, 12-22 exact sequential beats, clear to someone who has not read the source, explaining what changed, what it is, why it matters, comparison/price/access when material, the caveat, and a concise payoff. Use dry/playful humor but do not imitate named creators.
Base rubric: significance 0-4, practicalImpact 0-2, novelty 0-2, sourceConfidence 0-1, visualClarity 0-1. Pipeline heat bonus: {h:.2f}/2; heat never replaces verification.
CANDIDATE: {json.dumps(compact(item),ensure_ascii=False)}
KNOWN SOURCES: {snapshot or "(none; find a primary source)"}
{("REPAIR: "+repair) if repair else ""}
Return schema JSON. Rejections may use empty beats/sources."""
    result,r=model_json(client,model,[{"role":"system","content":system_prompt},{"role":"user","content":prompt}],review_schema(),"orbdev_editorial_review","medium",[{"type":"web_search","external_web_access":True}],"required")
    return result,response_urls(r),known
def split_beats(beats:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for b in beats:
        w=clean(str(b.get("text") or "")).split()
        while len(w)>10:c=dict(b);c["text"]=" ".join(w[:10]);out.append(c);w=w[10:]
        if w:c=dict(b);c["text"]=" ".join(w);out.append(c)
    while len(out)<12:
        idx=max(range(len(out)),key=lambda i:len(out[i]["text"].split()),default=-1)
        if idx<0 or len(out[idx]["text"].split())<4:break
        w=out[idx]["text"].split();p=len(w)//2;a,b=dict(out[idx]),dict(out[idx]);a["text"]=" ".join(w[:p]);b["text"]=" ".join(w[p:]);out[idx:idx+1]=[a,b]
    while len(out)>22:
        merged=False
        for i in range(len(out)-1):
            if len(out[i]["text"].split())+len(out[i+1]["text"].split())<=12:
                c=dict(out[i]);c["text"]=out[i]["text"]+" "+out[i+1]["text"];out[i:i+2]=[c];merged=True;break
        if not merged:break
    return out
def label(v:str,fallback:str="TECH UPDATE",words:int=6)->str:
    x=clean(v).split();return " ".join(x[:words]) if x else fallback
def visual(p:dict[str,Any],n:int)->dict[str,Any]:
    k=str(p.get("visualType") or "kinetic")
    if k=="source" and n:
        idx=max(0,min(n-1,int(p.get("sourceIndex") or 0)));mm=[clean(str(x))[:32] for x in (p.get("mustMatch") or [])[:3] if clean(str(x))]
        return {"type":"source","sourceIndex":idx,"query":clean(str(p.get("visualQuery") or p.get("text") or ""))[:180],"mustMatch":mm}
    if k=="metric":return {"type":"metric","value":label(str(p.get("metricValue") or p.get("visualLabel") or "NEW"),"NEW",4)}
    if k=="logo":return {"type":"logo","slug":slugify(str(p.get("logoSlug") or p.get("visualLabel") or "technology"),36),"label":label(str(p.get("visualLabel") or ""),"THE UPDATE",4)}
    if k=="comparison":return {"type":"comparison","left":label(str(p.get("visualLabel") or ""),"BEFORE",4),"right":label(str(p.get("visualAltLabel") or ""),"AFTER",4)}
    if k=="explain":
        mode=str(p.get("explainMode") or "pipeline");mode=mode if mode in EXPLAIN else "pipeline";v={"type":"explain","mode":mode};a,b=label(str(p.get("visualLabel") or ""),"INPUT",3),label(str(p.get("visualAltLabel") or ""),"OUTPUT",3)
        if mode=="network-shrink":v.update({"fromLayers":[5,4,4,3],"toLayers":[3,3,2],"labels":[a,b]})
        elif mode=="capacity":v.update({"load":88,"labels":[a]})
        elif mode=="pipeline":v["stages"]=[a,b,"RESULT"]
        elif mode=="fanout":v["nodes"]=[a,b,"OUTPUT"]
        else:v["labels"]=[a,b]
        return v
    t=label(str(p.get("visualLabel") or p.get("text") or ""),"TECH UPDATE",6).upper();return {"type":"kinetic","text":t,"emphasis":t.split()[-1] if t.split() else "UPDATE"}
def meme(p:dict[str,Any])->dict[str,Any]|None:
    purpose=str(p.get("memePurpose") or "none")
    if purpose=="none" or purpose not in MEME_PURPOSES:return None
    tone=str(p.get("memeTone") or "neutral");tone=tone if tone in MEME_TONES else "neutral";media=str(p.get("memeMedia") or "any");media=media if media in MEDIA else "any";pres=str(p.get("memePresentation") or "overlay");pres=pres if pres in PRESENTATIONS else "overlay"
    concepts=[clean(str(x))[:32] for x in (p.get("memeConcepts") or [])[:6] if clean(str(x))]
    return {"purpose":purpose,"tone":tone,"intensity":max(1,min(3,int(p.get("memeIntensity") or 1))),"preferredMedia":media,"presentation":pres,"maxDurationSeconds":round(max(.35,min(3.4,float(p.get("memeMaxDurationSeconds") or 1))),2),"concepts":concepts or [purpose]}
def constrain(beats:list[dict[str,Any]],sources:int)->None:
    for i in range(1,len(beats)):
        if beats[i-1]["visual"]["type"] in ABSTRACT and beats[i]["visual"]["type"] in ABSTRACT:beats[i]["visual"]={"type":"source","sourceIndex":i%sources,"query":beats[i]["text"],"mustMatch":[]} if sources else {"type":"kinetic","text":label(beats[i]["text"],words=5).upper(),"emphasis":"UPDATE"}
    logos=0
    for b in beats:
        if b["visual"]["type"]=="logo":
            logos+=1
            if logos>2:b["visual"]={"type":"kinetic","text":label(b["text"],words=5).upper(),"emphasis":"UPDATE"}
    if len(beats)>=14:
        for idx in (len(beats)//3,2*len(beats)//3):
            if sum(1 for b in beats if b["visual"]["type"]=="explain")>=2:break
            if beats[idx]["visual"]["type"] not in ABSTRACT and beats[idx-1]["visual"]["type"] not in ABSTRACT:beats[idx]["visual"]={"type":"explain","mode":"pipeline","stages":["INPUT","SYSTEM","RESULT"]}
    families=set("abstract" if b["visual"]["type"] in ABSTRACT else b["visual"]["type"] for b in beats);kin=[i for i,b in enumerate(beats) if b["visual"]["type"]=="kinetic"]
    if "metric" not in families and kin:beats[kin.pop()]["visual"]={"type":"metric","value":"NEW"}
    if "logo" not in families and kin:beats[kin.pop()]["visual"]={"type":"logo","slug":"technology","label":"THE UPDATE"}
    if "source" not in families and sources and kin:
        i=kin.pop(0);beats[i]["visual"]={"type":"source","sourceIndex":0,"query":beats[i]["text"],"mustMatch":[]}
def add_memes(beats:list[dict[str,Any]],target:int=4)->None:
    n=sum(1 for b in beats if b.get("memeIntent"))
    for role in ("punchline","joke","reaction","callback","analogy"):
        for b in beats:
            if n>=target:return
            if b.get("memeIntent") or b.get("editorialRole")!=role:continue
            b["memeIntent"]={"purpose":"punchline" if role in {"punchline","joke","callback"} else "reaction","tone":"deadpan" if role in {"punchline","joke"} else "surprised","intensity":2,"preferredMedia":"image","presentation":"overlay","maxDurationSeconds":1.0,"concepts":[role,"reaction"]};n+=1
def build_story(review:dict[str,Any],item:dict[str,Any],score:float,selected:str)->tuple[dict[str,Any]|None,list[str]]:
    issues=[];sources=[]
    for s in review.get("sources") or []:
        u=norm_url(str(s.get("url") or ""))
        if u:sources.append({"title":clean(str(s.get("title") or "Source"))[:180],"publisher":clean(str(s.get("publisher") or host(u)))[:80],"url":u,"publishedAt":clean(str(s.get("publishedAt") or ""))[:64],"primary":bool(s.get("primary"))})
    if not sources or not any(s["primary"] for s in sources):issues.append("no primary source")
    raw=split_beats([dict(x) for x in review.get("beats") or [] if clean(str(x.get("text") or ""))]);narration=clean(" ".join(x["text"] for x in raw));wc=len(narration.split())
    if not 12<=len(raw)<=22:issues.append(f"beat count {len(raw)}")
    if not 80<=wc<=105:issues.append(f"word count {wc}")
    beats=[]
    for p in raw:
        role=str(p.get("editorialRole") or "fact");role=role if role in ROLES else "fact";b={"text":clean(str(p.get("text") or "")),"editorialRole":role,"visual":visual(p,len(sources))}
        sf=str(p.get("sfx") or "none")
        if sf in SFX and sf!="none":b["sfx"]=sf
        m=meme(p)
        if m:b["memeIntent"]=m
        beats.append(b)
    constrain(beats,len(sources));add_memes(beats);slug=slugify(str(review.get("slug") or review.get("headline") or item.get("title") or "story"));key=slugify(str(review.get("storyKey") or f"{slug}-{datetime.now().year}"),100);pub=review.get("publish") or {};desc=clean(str(pub.get("description") or ""));prim=[s["url"] for s in sources if s["primary"]]
    if prim:desc=(desc+"\n\nSources:\n"+"\n".join(prim)).strip()
    story={"slug":slug,"title":clean(str(review.get("headline") or item.get("title") or slug))[:180],"narration":narration,"beats":beats,"editorial":{"storyKey":key,"selectedAt":selected,"score":round(score,2),"topics":[clean(str(x))[:80] for x in (review.get("topics") or [])[:10] if clean(str(x))],"companies":[clean(str(x))[:100] for x in (review.get("companies") or [])[:10] if clean(str(x))],"sources":sources,"discovery":{"clusterId":item.get("clusterId"),"lanes":item.get("lanes") or [],"creators":item.get("creators") or [],"signals":item.get("signals") or [],"discoveryScore":item.get("score"),"qualityGate":item.get("qualityGate")}},"publish":{"youtubeTitle":clean(str(pub.get("youtubeTitle") or review.get("headline") or ""))[:100],"description":desc[:5000],"tags":[clean(str(x))[:60] for x in (pub.get("tags") or [])[:20] if clean(str(x))],"category":clean(str(pub.get("category") or "SCIENCE_TECHNOLOGY")) or "SCIENCE_TECHNOLOGY","madeForKids":False}}
    return (None if issues else story),issues
def existing_keys(covered:dict[str,Any],queue:Path)->set[str]:
    keys={str(x.get("storyKey")) for x in covered.get("stories",[]) if x.get("storyKey")}
    for p in queue.glob("*.json"):
        try:
            k=json.loads(p.read_text(encoding="utf-8")).get("editorial",{}).get("storyKey")
            if k:keys.add(str(k))
        except Exception:pass
    return keys
def write_report(p:Path,m:dict[str,Any])->None:
    lines=["# Orbdev editorial batch","",f"Inbox: {m.get('inboxGeneratedAt')}",f"Reviewed: {m.get('reviewedCount',0)}",f"Accepted: {m.get('acceptedCount',0)}","","## Decisions",""]
    for d in m.get("decisions",[]):lines.append(f"- {d.get('decision')}: {d.get('title')} — {d.get('reason','')}")
    p.write_text("\n".join(lines)+"\n",encoding="utf-8")
def main()->None:
    a=argparse.ArgumentParser();a.add_argument("--inbox",default="editorial/inbox/latest.json");a.add_argument("--policy",default="editorial/policy.json");a.add_argument("--discovery-config",default="editorial/discovery.json");a.add_argument("--prompt",default="editorial/editorial-agent.md");a.add_argument("--state",default="history/editorial-state.json");a.add_argument("--covered",default="history/covered.json");a.add_argument("--queue-dir",default="stories/queue");a.add_argument("--output",default="build/editorial");a.add_argument("--expected-generated-at",default="");a.add_argument("--triage-model",default=os.getenv("ORBDEV_TRIAGE_MODEL","gpt-6-luna"));a.add_argument("--editorial-model",default=os.getenv("ORBDEV_EDITORIAL_MODEL","gpt-6.1-sol"));a.add_argument("--dry-run",action="store_true");x=a.parse_args()
    out=Path(x.output);stories=out/"stories";out.mkdir(parents=True,exist_ok=True);stories.mkdir(parents=True,exist_ok=True);inbox=load(Path(x.inbox),{"qualified":[]});policy=load(Path(x.policy),{});cfg=load(Path(x.discovery_config),{});state=load(Path(x.state),{"version":1,"decisions":[]});covered=load(Path(x.covered),{"version":1,"stories":[]});queue=Path(x.queue_dir);actual=str(inbox.get("generatedAt") or "")
    if x.expected_generated_at and x.expected_generated_at!=actual:raise SystemExit(f"inbox race: expected {x.expected_generated_at}, got {actual}")
    now=datetime.now(ZoneInfo("Europe/London"));selected=now.isoformat();decisions=[];eligible=[]
    for item in inbox.get("qualified") or []:
        ok,why=should_recheck(item,state,now,float(cfg.get("editorialRecheckHours",24)),float(cfg.get("editorialRecheckScoreDelta",.6)))
        if ok:eligible.append(item)
        else:decisions.append({"clusterId":item.get("clusterId"),"title":item.get("title"),"decision":"skipped","reason":why,"discoveryScore":float(item.get("score") or 0),"finalScore":0.0,"decidedAt":selected})
    if x.dry_run:
        m={"version":1,"inboxGeneratedAt":actual,"dryRun":True,"reviewedCount":0,"acceptedCount":0,"rejectedCount":0,"skippedCount":len(decisions),"queueFiles":[],"decisions":decisions};(out/"manifest.json").write_text(json.dumps(m,indent=2));(out/"editorial-state-next.json").write_text(json.dumps(state,indent=2));write_report(out/"report.md",m);print(f"Editorial dry run: {len(eligible)} eligible");return
    if not os.getenv("OPENAI_API_KEY","").strip():raise SystemExit("OPENAI_API_KEY required")
    from openai import OpenAI
    client=OpenAI();tr=triage(client,eligible,x.triage_model);pursued=[]
    for item in eligible:
        t=tr[str(item.get("clusterId"))]
        if t.get("pursue"):pursued.append(item)
        else:decisions.append({"clusterId":item.get("clusterId"),"title":item.get("title"),"decision":"rejected","reason":"triage: "+clean(str(t.get("reason") or "")),"discoveryScore":float(item.get("score") or 0),"finalScore":0.0,"decidedAt":selected})
    system=Path(x.prompt).read_text(encoding="utf-8");keys=existing_keys(covered,queue);queue_files=[];minimum=float(policy.get("minimumScore") or 7.2);minbase=float(cfg.get("minimumBaseEditorialScore",6.0));domains=list(policy.get("primarySources") or [])
    for item in pursued:
        cid=str(item.get("clusterId"));h=heat_bonus(item,minimum);review=None;issues=[];err=""
        for attempt in range(2):
            try:review,cited,known=final_review(client,item,policy,system,x.editorial_model,"; ".join(issues) if attempt else "")
            except Exception as e:err=f"{type(e).__name__}: {e}";break
            if not review.get("accept"):issues=[clean(str(review.get("rejectionReason") or "editorial rejection"))];break
            prim=[s for s in review.get("sources") or [] if s.get("primary") and source_backed(str(s.get("url") or ""),known,cited,domains)];base=base_score(review.get("rubric") or {});final=round(min(10.0,base+h),2)
            if not prim:issues=["primary source not backed"];continue
            if base<minbase:issues=[f"base score {base:.2f} below {minbase:.2f}"];break
            if final<minimum:issues=[f"final score {final:.2f} below {minimum:.2f}"];break
            story,issues=build_story(review,item,final,selected)
            if story:
                key=story["editorial"]["storyKey"]
                if key in keys:issues=["already covered or queued"];break
                keys.add(key);name=f"{now.strftime('%Y-%m-%d')}-{story['slug']}.json";p=stories/name;n=2
                while p.exists():name=f"{now.strftime('%Y-%m-%d')}-{story['slug']}-{n}.json";p=stories/name;n+=1
                p.write_text(json.dumps(story,indent=2,ensure_ascii=False)+"\n",encoding="utf-8");q=f"stories/queue/{name}";queue_files.append(q);decisions.append({"clusterId":cid,"storyKey":key,"title":story["title"],"decision":"accepted","reason":clean(str(review.get("whyItMatters") or "verified")),"discoveryScore":float(item.get("score") or 0),"baseScore":base,"heatBonus":h,"finalScore":final,"queueFile":q,"decidedAt":selected});break
        if not any(d.get("clusterId")==cid for d in decisions):
            base=base_score((review or {}).get("rubric") or {});decisions.append({"clusterId":cid,"title":item.get("title"),"decision":"rejected","reason":err or "; ".join(issues) or "editorial rejection","discoveryScore":float(item.get("score") or 0),"baseScore":base,"heatBonus":h,"finalScore":round(min(10.0,base+h),2),"decidedAt":selected})
    ns={"version":1,"lastInboxGeneratedAt":actual,"lastRunAt":selected,"decisions":((state.get("decisions") or [])+decisions)[-500:]};m={"version":1,"inboxGeneratedAt":actual,"dryRun":False,"reviewedCount":len(pursued),"acceptedCount":len(queue_files),"rejectedCount":sum(d.get("decision")=="rejected" for d in decisions),"skippedCount":sum(d.get("decision")=="skipped" for d in decisions),"queueFiles":queue_files,"decisions":decisions}
    (out/"manifest.json").write_text(json.dumps(m,indent=2,ensure_ascii=False));(out/"editorial-state-next.json").write_text(json.dumps(ns,indent=2,ensure_ascii=False));write_report(out/"report.md",m);print(f"Editorial batch: {len(eligible)} eligible -> {len(pursued)} deep-reviewed -> {len(queue_files)} accepted")
if __name__=="__main__":main()
