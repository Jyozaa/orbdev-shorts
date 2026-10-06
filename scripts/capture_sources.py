from __future__ import annotations
import html,json,re,shutil,subprocess,sys,urllib.parse,urllib.request
from pathlib import Path

BUILD=Path("build"); PUBLIC=Path("public/sources"); REPORT=BUILD/"source-assets.json"
MAX_IMAGES_PER_SOURCE=8

def fetch(url:str,timeout:int=30,referer:str|None=None)->tuple[bytes,str]:
    headers={"User-Agent":"Mozilla/5.0 orbdev-renderer","Accept":"text/html,application/xhtml+xml,image/avif,image/webp,image/*,*/*;q=0.8"}
    if referer: headers["Referer"]=referer
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=timeout) as r:
        return r.read(),r.headers.get("Content-Type","")

def absolute(base:str,value:str)->str:
    return urllib.parse.urljoin(base,html.unescape(value.strip()))

def clean_text(value:str)->str:
    value=re.sub(r"<[^>]+>"," ",value)
    return " ".join(html.unescape(value).split())[:600]

def attr(tag:str,name:str)->str:
    m=re.search(rf'\b{name}=["\']([^"\']+)["\']',tag,flags=re.I)
    return html.unescape(m.group(1)).strip() if m else ""

def github_readme_candidates(repo_url:str)->list[dict[str,object]]:
    """Extract real screenshots/demos linked by a public GitHub README.

    GitHub repository pages often lazy-render README media, so HTML scraping only
    sees the OpenGraph card. Reading the public raw README exposes the actual
    demo attachments without any external API key.
    """
    parsed=urllib.parse.urlparse(repo_url)
    if parsed.netloc.lower() not in {"github.com","www.github.com"}:return []
    parts=[p for p in parsed.path.split("/") if p]
    if len(parts)<2:return []
    owner,repo=parts[0],parts[1].removesuffix(".git")
    raw_url=f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md"
    try:
        data,_=fetch(raw_url,timeout=20,referer=repo_url)
        md=data.decode("utf-8",errors="ignore")
    except Exception as e:
        print(f"GitHub README media discovery failed: {e}")
        return []

    candidates=[];seen=set()
    headings=[]
    for match in re.finditer(r"(?m)^#{2,4}\s+(.+?)\s*$",md):
        headings.append((match.start(),clean_text(match.group(1))))

    def section_for(pos:int)->str:
        prior=[title for start,title in headings if start<=pos]
        return prior[-1] if prior else f"{owner}/{repo}"

    def add(raw:str,pos:int,score:int,alt:str=""):
        raw=html.unescape(raw.strip().strip("<>"))
        if not raw:return
        if raw.startswith("./") or ("://" not in raw and not raw.startswith("/")):
            raw=f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{raw.lstrip('./')}"
        url=absolute(repo_url,raw)
        low=url.lower()
        if url in seen or any(x in low for x in ("shields.io","badge.svg","trendshift.io/api/badge")):return
        seen.add(url)
        context=clean_text(md[max(0,pos-420):min(len(md),pos+720)])
        text=" ".join(x for x in (section_for(pos),clean_text(alt),context) if x)
        candidates.append({"url":url,"baseScore":score,"text":text})

    # GitHub user attachments are frequently MP4/GIF demo recordings. ffmpeg
    # later extracts a representative frame, so they are useful source visuals.
    for m in re.finditer(r"https://github\.com/user-attachments/assets/[A-Za-z0-9-]+",md,re.I):
        add(m.group(0),m.start(),88)

    for m in re.finditer(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)",md):
        add(m.group(2),m.start(),76,m.group(1))

    for m in re.finditer(r"<img\b[^>]*>",md,re.I):
        tag=m.group(0);src=attr(tag,"src")
        add(src,m.start(),72,attr(tag,"alt"))

    return sorted(candidates,key=lambda x:int(x["baseScore"]),reverse=True)

def extract_image_candidates(page:str,base_url:str)->list[dict[str,object]]:
    candidates=[]; seen=set()
    title=clean_text((re.search(r"<title[^>]*>(.*?)</title>",page,flags=re.I|re.S) or [None,""])[1])
    desc=""
    dm=re.search(r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']+)["\']',page,flags=re.I)
    if dm: desc=clean_text(dm.group(1))

    def add(raw:str,score:int,text:str):
        if not raw or raw.startswith("data:"): return
        url=absolute(base_url,raw); low=url.lower()
        if url in seen or any(x in low for x in ("avatar","favicon","sprite","emoji","tracking","pixel.gif","author")): return
        seen.add(url)
        candidates.append({"url":url,"baseScore":score,"text":clean_text(text)})

    for pattern,score in [
        (r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)["\']',75),
        (r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']',70),
    ]:
        for m in re.finditer(pattern,page,flags=re.I): add(m.group(1),score,f"hero {title} {desc}")

    for m in re.finditer(r"<img\b[^>]*>",page,flags=re.I):
        tag=m.group(0); low=tag.lower(); score=45
        raw_context=page[max(0,m.start()-360):min(len(page),m.end()+360)]
        surrounding=(tag+" "+raw_context).lower()
        if any(x in surrounding for x in ("post-sidebar","post-card","related-post","recommended","footer","author-card","more-stories")):continue
        if any(x in low for x in ("hero","featured","article","content","media","gallery")): score+=20
        context=clean_text(raw_context)
        semantic=" ".join(x for x in (attr(tag,"alt"),attr(tag,"title"),context) if x)
        src=""
        for name in ("src","data-src","data-lazy-src","data-original"):
            src=attr(tag,name)
            if src: break
        srcset=attr(tag,"srcset")
        if srcset:
            parts=[p.strip().split()[0] for p in srcset.split(",") if p.strip()]
            if parts: src=parts[-1]; score+=5
        add(src,score,semantic)

    return sorted(candidates,key=lambda x:int(x["baseScore"]),reverse=True)

def normalize_image(source:Path,target:Path)->tuple[int,int]|None:
    try:
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(source),"-vf","scale='min(1400,iw)':-2","-frames:v","1","-q:v","2",str(target)],check=True)
        dims=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=p=0:s=x",str(target)],text=True).strip()
        w,h=[int(v) for v in dims.split("x")]
        if w<480 or h<260:
            target.unlink(missing_ok=True)
            return None
        return w,h
    except Exception:
        target.unlink(missing_ok=True)
        return None

def chrome_screenshot(url:str,target:Path)->bool:
    chrome=next((x for x in (shutil.which("google-chrome"),shutil.which("google-chrome-stable"),shutil.which("chromium"),shutil.which("chromium-browser")) if x),None)
    if not chrome:return False
    try:
        subprocess.run([chrome,"--headless=new","--disable-gpu","--no-sandbox","--hide-scrollbars","--window-size=1080,1400","--virtual-time-budget=3500",f"--screenshot={target.resolve()}",url],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=25)
        return target.exists()
    except Exception:return False

def visual_hash(path:Path)->str:
    """64-bit difference hash independent of filename, URL, and image encoding."""
    try:
        b=subprocess.check_output(
            ["ffmpeg","-v","error","-i",str(path),"-vf","scale=9:8,format=gray",
             "-frames:v","1","-f","rawvideo","-"],timeout=15)
        if len(b)!=72:return ""
        bits=0
        for row in range(8):
            for col in range(8):
                bits=(bits<<1)|int(b[row*9+col]>b[row*9+col+1])
        return f"{bits:016x}"
    except Exception:return ""

def capture(candidate:dict[str,object],referer:str,index:int,variant:int)->dict[str,object]|None:
    temp=BUILD/f"source-{index}-{variant}.asset"; target=PUBLIC/f"source-{index}-{variant}.jpg"
    try:
        data,ctype=fetch(str(candidate["url"]),referer=referer)
        if "text/html" in ctype:return None
        temp.write_bytes(data)
        dims=normalize_image(temp,target)
        if not dims:return None
        w,h=dims
        return {"src":f"sources/{target.name}","url":candidate["url"],"text":candidate.get("text",""),"baseScore":candidate.get("baseScore",0),"width":w,"height":h,"aspectRatio":round(w/max(1,h),4),"visualHash":visual_hash(target)}
    except Exception as e:
        print(f"Source {index} image {variant} failed: {e}"); return None
    finally: temp.unlink(missing_ok=True)

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: capture_sources.py <story.json>")
    story=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sources=story.get("editorial",{}).get("sources",[])
    requested=sorted({int(b["visual"]["sourceIndex"]) for b in story.get("beats",[]) if b.get("visual",{}).get("type")=="source"})
    PUBLIC.mkdir(parents=True,exist_ok=True); BUILD.mkdir(parents=True,exist_ok=True)
    report={}
    for index in requested:
        if not 0<=index<len(sources):continue
        url=sources[index].get("url")
        if not isinstance(url,str):continue
        assets=[]
        try:
            page_bytes,ctype=fetch(url)
            if "text/html" in ctype or page_bytes.lstrip().startswith(b"<"):
                page=page_bytes.decode("utf-8",errors="ignore")
                discovered=github_readme_candidates(url)+extract_image_candidates(page,url)
                seen_urls=set()
                for cand in discovered:
                    if len(assets)>=MAX_IMAGES_PER_SOURCE:break
                    candidate_url=str(cand.get("url",""))
                    if not candidate_url or candidate_url in seen_urls:continue
                    seen_urls.add(candidate_url)
                    item=capture(cand,url,index,len(assets))
                    if item:
                        digest=str(item.get("visualHash") or "")
                        duplicate=any(
                            digest and prev.get("visualHash") and
                            (int(digest,16)^int(prev["visualHash"],16)).bit_count()<=3
                            for prev in assets
                        )
                        if duplicate:
                            (PUBLIC/str(item["src"]).split("/")[-1]).unlink(missing_ok=True)
                        else:
                            assets.append(item)
        except Exception as e: print(f"Source {index}: discovery failed: {e}")
        if len(assets)<MAX_IMAGES_PER_SOURCE:
            shot=PUBLIC/f"source-{index}-page.png"
            if chrome_screenshot(url,shot):
                title=str(sources[index].get("title",""))
                screenshot={"src":f"sources/{shot.name}","url":url,"text":f"official source page screenshot {title}","baseScore":34,"width":1080,"height":1400,"aspectRatio":round(1080/1400,4),"visualHash":visual_hash(shot)}
                digest=screenshot["visualHash"]
                if digest and any(prev.get("visualHash") and
                    (int(digest,16)^int(prev["visualHash"],16)).bit_count()<=3 for prev in assets):
                    shot.unlink(missing_ok=True)
                else:
                    assets.append(screenshot)
        report[str(index)]={"assets":assets,"count":len(assets)}
        print(f"Source {index}: captured {len(assets)} candidate assets with semantic metadata")
    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")

if __name__=="__main__":main()
