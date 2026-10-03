from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

CAPTIONS = Path("public/captions.json")
VOICE = Path("public/voice.mp3")
SELECTION = Path("build/meme-selection.json")
CUTAWAYS = Path("build/cutaways.json")
TEMP_VOICE = Path("public/voice-with-pauses.mp3")


def norm(token: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", token.lower())


def beat_tokens(text: str) -> list[str]:
    return [value for value in (norm(token) for token in re.findall(r"\S+", text)) if value]


def find_sequence(words: list[dict[str, object]], expected: list[str], cursor: int) -> tuple[int, int]:
    normalized = [norm(str(word["text"])) for word in words]
    for start in range(cursor, min(len(words), cursor + 10)):
        end = start + len(expected)
        if normalized[start:end] == expected:
            return start, end - 1
    end = min(len(words) - 1, cursor + max(1, len(expected)) - 1)
    return cursor, end


def audio_duration(path: Path) -> float:
    value = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path)
        ],
        text=True,
    ).strip()
    return float(value)


def insert_silence(insertions: list[tuple[float, float]]) -> None:
    if not insertions:
        return

    original_duration = audio_duration(VOICE)
    filters: list[str] = []
    concat_inputs: list[str] = []
    cursor = 0.0
    part = 0

    for insertion_at, pause_duration in insertions:
        insertion_at = max(cursor, min(original_duration, insertion_at))
        if insertion_at > cursor + 0.001:
            filters.append(
                f"[0:a]atrim=start={cursor:.6f}:end={insertion_at:.6f},"
                f"asetpts=PTS-STARTPTS,aresample=44100,"
                f"aformat=sample_fmts=fltp:channel_layouts=mono[a{part}]"
            )
            concat_inputs.append(f"[a{part}]")
            part += 1

        filters.append(
            f"anullsrc=r=44100:cl=mono,atrim=duration={pause_duration:.6f},"
            f"asetpts=PTS-STARTPTS[s{part}]"
        )
        concat_inputs.append(f"[s{part}]")
        part += 1
        cursor = insertion_at

    if cursor < original_duration:
        filters.append(
            f"[0:a]atrim=start={cursor:.6f}:end={original_duration:.6f},"
            f"asetpts=PTS-STARTPTS,aresample=44100,"
            f"aformat=sample_fmts=fltp:channel_layouts=mono[a{part}]"
        )
        concat_inputs.append(f"[a{part}]")

    filters.append(
        "".join(concat_inputs)
        + f"concat=n={len(concat_inputs)}:v=0:a=1[out]"
    )

    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(VOICE),
            "-filter_complex", ";".join(filters),
            "-map", "[out]", "-codec:a", "libmp3lame", "-q:a", "2", str(TEMP_VOICE)
        ],
        check=True,
    )
    TEMP_VOICE.replace(VOICE)


def main() -> None:
    story_path = Path(os.environ["STORY_FILE"])
    story = json.loads(story_path.read_text(encoding="utf-8"))
    timing = json.loads(CAPTIONS.read_text(encoding="utf-8"))
    words = timing["words"]
    selections = json.loads(SELECTION.read_text(encoding="utf-8")) if SELECTION.exists() else {}
    caption_lead_ms = int(os.getenv("ORBDEV_CAPTION_LEAD_MS", "90"))

    cursor = 0
    raw_insertions: list[dict[str, object]] = []
    for index, beat in enumerate(story["beats"]):
        expected = beat_tokens(beat["text"])
        start_index, end_index = find_sequence(words, expected, cursor)
        cursor = end_index + 1

        selected = selections.get(str(index))
        if not selected or selected.get("presentation") != "cutaway":
            continue

        raw_insert_ms = int(words[end_index]["endMs"]) + caption_lead_ms
        raw_insertions.append({
            "beatIndex": index,
            "rawInsertMs": raw_insert_ms,
            "durationMs": int(round(float(selected["durationSeconds"]) * 1000)),
            "meme": selected,
        })

    raw_insertions.sort(key=lambda item: int(item["rawInsertMs"]))
    insert_pairs = [
        (float(item["rawInsertMs"]) / 1000.0, float(item["durationMs"]) / 1000.0)
        for item in raw_insertions
    ]
    insert_silence(insert_pairs)

    def pause_before(ms: int) -> int:
        return sum(
            int(item["durationMs"])
            for item in raw_insertions
            if int(item["rawInsertMs"]) <= ms + caption_lead_ms
        )

    for word in words:
        original_start = int(word["startMs"])
        original_end = int(word["endMs"])
        word["startMs"] = original_start + pause_before(original_start)
        word["endMs"] = original_end + pause_before(original_end)

    cutaways = []
    cumulative = 0
    for item in raw_insertions:
        start_ms = int(item["rawInsertMs"]) + cumulative
        duration_ms = int(item["durationMs"])
        meme = dict(item["meme"])
        meme["offsetSeconds"] = 0
        cutaways.append({
            "beatIndex": int(item["beatIndex"]),
            "start": round(start_ms / 1000.0, 4),
            "end": round((start_ms + duration_ms) / 1000.0, 4),
            "meme": meme,
        })
        cumulative += duration_ms

    timing["durationSeconds"] = round(float(timing["durationSeconds"]) + cumulative / 1000.0, 4)
    timing["words"] = words
    CAPTIONS.write_text(json.dumps(timing, indent=2), encoding="utf-8")

    CUTAWAYS.parent.mkdir(parents=True, exist_ok=True)
    CUTAWAYS.write_text(json.dumps(cutaways, indent=2), encoding="utf-8")
    print(f"Inserted {len(cutaways)} narration-free meme cutaways")


if __name__ == "__main__":
    main()
