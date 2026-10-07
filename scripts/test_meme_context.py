#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent))

import build_meme_catalog as catalog
import select_memes as selector


def item(
    name:str,
    *,
    contexts:list[str],
    purposes:list[str]=["reaction"],
    tones:list[str]=["neutral"],
    tags:list[str]|None=None,
    media_type:str="image",
    intensity:int=1,
):
    return {
        "id":name,
        "path":f"memes/{name}.jpg",
        "mediaType":media_type,
        "tags":tags or name.split("-"),
        "purposes":purposes,
        "tones":tones,
        "contexts":contexts,
        "intensity":intensity,
        "brandSafe":True,
        "rightsStatus":"approved",
    }


def score(asset,intent,line):
    return selector.score(asset,intent,line)[0]


def main():
    pricing={
        "purpose":"contrast","tone":"surprised","intensity":2,
        "preferredMedia":"image","concepts":["reaction","surprised","price"],
    }
    money=item("stonks-price",contexts=["money"],purposes=["contrast"],tones=["deadpan"],tags=["stonks","price","money"],intensity=2)
    generic_surprise=item("wow-face",contexts=["surprise"],purposes=["contrast"],tones=["surprised"],tags=["wow"],intensity=2)
    line="Pricing follows each provider's list API price."
    assert score(money,pricing,line)>0
    assert score(generic_surprise,pricing,line)<0,"tone must not override the pricing context"

    compute={
        "purpose":"emphasis","tone":"neutral","intensity":1,
        "preferredMedia":"image","concepts":["smart","efficient","reaction"],
    }
    brain=item("big-brain-time",contexts=["intelligence"],tags=["big","brain","smart"],intensity=1)
    laugh=item("laughing-car",contexts=["comedy"],tags=["laughing","funny"],intensity=1)
    line="Big model, selective compute."
    assert score(brain,compute,line)>0
    assert score(laugh,compute,line)<0
    sarcastic=item(
        "wow-genius-so-funny",
        contexts=["intelligence","comedy"],
        purposes=["emphasis","punchline"],
        tones=["negative","deadpan"],
        tags=["wow","genius","funny"],
        intensity=2,
    )
    assert score(sarcastic,compute,line)<0,"neutral technical praise must not use sarcastic mockery"

    rejection={
        "purpose":"punchline","tone":"deadpan","intensity":1,
        "preferredMedia":"image","concepts":["nope","reaction"],
    }
    nope=item("nope",contexts=["rejection"],tags=["nope"],intensity=1)
    win=item("victory",contexts=["success"],tags=["victory","win"],intensity=1)
    line="not a smaller model."
    assert score(nope,rejection,line)>0
    assert score(win,rejection,line)<0

    confusion={
        "purpose":"reaction","tone":"confused","intensity":1,
        "preferredMedia":"image","concepts":["confused","reaction"],
    }
    confused=item("what-do-you-mean",contexts=["confusion"],tones=["confused"],tags=["what","mean","confused"])
    assert score(confused,confusion,"That sounds contradictory,")>0

    # A generic reaction request with no meaning in the narration should be
    # skipped rather than decorated with an unrelated meme.
    generic={
        "purpose":"reaction","tone":"deadpan","intensity":1,
        "preferredMedia":"image","concepts":["reaction","deadpan","emphasis"],
    }
    assert score(brain,generic,"It adds live web grounding through AI Gateway.")<0
    assert score(confused,generic,"It adds live web grounding through AI Gateway.")<0

    # Catalog folder/file metadata should produce the contexts consumed above.
    assert "intelligence" in catalog.semantic_contexts(
        "Memes templates -HD- 2/Various & templates (no HD)/Reactions/Dumb - Genius/Big brain time.jpg"
    )
    assert "confusion" in catalog.semantic_contexts("Meme Pack/Meme Videos/What do you mean by that - Druski meme.mp4")
    assert "waiting" in catalog.semantic_contexts("Meme Pack/Meme Videos/Spongebob - 2000 Years Later.mp4")
    assert "money" in catalog.semantic_contexts("Memes templates -HD-/stonks price money.jpg")
    assert "intelligence" not in catalog.semantic_contexts(
        "Memes templates -HD-/meuf choquée surprise lire smartphone.jpg"
    )

    print("context-aware meme regression checks passed")


if __name__=="__main__":
    main()
