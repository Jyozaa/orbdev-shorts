from __future__ import annotations
import asyncio,json,os,re,subprocess,sys
from pathlib import Path
import edge_tts

PUBLIC_DIR=Path("public"); RAW_AUDIO_PATH=PUBLIC_DIR/"voice-raw.mp3"; RAW_WAV_PATH=PUBLIC_DIR/"voice-kokoro.wav"; AUDIO_PATH=PUBLIC_DIR/"voice.mp3"; CAPTIONS_PATH=PUBLIC_DIR/"captions.json"
CAPTION_LEAD_MS=int(os.getenv("ORBDEV_CAPTION_LEAD_MS","70"))

def audio_duration_seconds(path:Path)->float:
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],text=True).strip())

def weighted_word_timings(text:str,start:float,duration:float)->list[dict[str,object]]:
    words=re.findall(r"\S+",text)
    if not words:return []
    weights=[max(1,len(re.sub(r"[^A-Za-z0-9]","",w))) for w in words]; total=max(1,sum(weights)); cursor=start; out=[]
    for word,weight in zip(words,weights):
        width=duration*(weight/total)
        out.append({"text":word,"startMs":round(cursor*1000),"endMs":round((cursor+width)*1000)})
        cursor+=width
    return out

def render_kokoro(text:str)->list[dict[str,object]]:
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline
    voice=os.getenv("ORBDEV_KOKORO_VOICE","am_michael"); speed=float(os.getenv("ORBDEV_KOKORO_SPEED","1.05"))
    pipeline=KPipeline(lang_code="a"); chunks=[]; captions=[]; cursor=0.0; sr=24000
    for result in pipeline(text,voice=voice,speed=speed):
        try: graphemes,_phonemes,audio=result
        except Exception:
            graphemes=getattr(result,"graphemes",""); audio=getattr(result,"audio",getattr(result,"output",None))
        if audio is None:continue
        arr=np.asarray(audio,dtype=np.float32).reshape(-1)
        if arr.size==0:continue
        spoken=str(graphemes).strip(); dur=arr.size/sr
        if spoken:captions.extend(weighted_word_timings(spoken,cursor,dur))
        chunks.append(arr);cursor+=dur
        if spoken.endswith((".","!","?")):
            pause=np.zeros(int(sr*.055),dtype=np.float32);chunks.append(pause);cursor+=pause.size/sr
    if not chunks:raise RuntimeError("Kokoro produced no audio")
    sf.write(RAW_WAV_PATH,np.concatenate(chunks),sr)
    print(f"Narration engine: Kokoro-82M / {voice} @ {speed:.2f}x")
    return captions

async def render_edge(text:str,voice:str)->list[dict[str,object]]:
    communicator=edge_tts.Communicate(text=text,voice=voice,rate=os.getenv("ORBDEV_EDGE_RATE","+6%"),pitch="+0Hz")
    captions=[];RAW_AUDIO_PATH.unlink(missing_ok=True)
    with RAW_AUDIO_PATH.open("wb") as f:
        async for chunk in communicator.stream():
            if chunk["type"]=="audio":f.write(chunk["data"])
            elif chunk["type"]=="WordBoundary":
                s=int(chunk["offset"]/10000);d=int(chunk["duration"]/10000);captions.append({"text":chunk["text"],"startMs":s,"endMs":s+max(1,d)})
    return captions

def process_voice(source:Path)->None:
    filters="highpass=f=52,acompressor=threshold=-15dB:ratio=1.25:attack=18:release=220:makeup=0.4dB,alimiter=limit=0.97:attack=5:release=80,loudnorm=I=-16:TP=-1.5:LRA=9"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(source),"-af",filters,"-codec:a","libmp3lame","-q:a","2",str(AUDIO_PATH)],check=True)

def render_espeak(text:str)->None:
    wav=PUBLIC_DIR/"voice-fallback.wav";subprocess.run(["espeak-ng","-s","190","-w",str(wav),text],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);process_voice(wav);wav.unlink(missing_ok=True)

async def main()->None:
    if len(sys.argv)!=2:raise SystemExit("usage: generate_narration.py <story.json>")
    text=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["narration"].strip();PUBLIC_DIR.mkdir(parents=True,exist_ok=True);AUDIO_PATH.unlink(missing_ok=True)
    captions=[]
    try:
        captions=render_kokoro(text);process_voice(RAW_WAV_PATH)
    except Exception as exc:
        print(f"Kokoro unavailable: {exc}")
        for voice in (os.getenv("ORBDEV_VOICE_FALLBACK","en-US-BrianMultilingualNeural"),os.getenv("ORBDEV_VOICE_TERTIARY","en-US-AndrewMultilingualNeural")):
            try:
                captions=await render_edge(text,voice);process_voice(RAW_AUDIO_PATH);print(f"Narration engine fallback: Edge / {voice}");break
            except Exception as e:print(f"Edge voice unavailable ({voice}): {e}");captions=[]
    if not AUDIO_PATH.exists():render_espeak(text)
    duration=audio_duration_seconds(AUDIO_PATH); expected=len(re.findall(r"\S+",text))
    if not captions or abs(len(captions)-expected)>max(4,expected*.08):captions=weighted_word_timings(text,0,duration)
    if CAPTION_LEAD_MS>0:
        captions=[{**c,"startMs":max(0,int(c["startMs"])-CAPTION_LEAD_MS),"endMs":max(1,int(c["endMs"])-CAPTION_LEAD_MS)} for c in captions]
    CAPTIONS_PATH.write_text(json.dumps({"durationSeconds":duration,"words":captions},indent=2),encoding="utf-8")
    RAW_AUDIO_PATH.unlink(missing_ok=True);RAW_WAV_PATH.unlink(missing_ok=True);print(f"Narration ready: {duration:.2f}s, {len(captions)} timed words")

if __name__=="__main__":asyncio.run(main())
