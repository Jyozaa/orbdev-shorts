import React, {useMemo} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {CaptionWord} from '../types';

type Phrase = {
  text: string;
  startMs: number;
  endMs: number;
};

const buildPhrases = (words: CaptionWord[]): Phrase[] => {
  const phrases: Phrase[] = [];
  let group: CaptionWord[] = [];

  const flush = () => {
    if (group.length === 0) return;
    phrases.push({
      text: group.map((word) => word.text).join(' '),
      startMs: group[0].startMs,
      endMs: group[group.length - 1].endMs
    });
    group = [];
  };

  for (const word of words) {
    group.push(word);
    const punctuationBreak = /[.!?,:;]$/.test(word.text);
    if (group.length >= 5 || (group.length >= 3 && punctuationBreak)) {
      flush();
    }
  }
  flush();
  return phrases;
};

export const CaptionStrip: React.FC<{captions: CaptionWord[]}> = ({captions}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const nowMs = (frame / fps) * 1000;
  const phrases = useMemo(() => buildPhrases(captions), [captions]);

  const phrase =
    phrases.find((item) => nowMs >= item.startMs && nowMs <= item.endMs + 140) ??
    phrases.find((item) => nowMs < item.startMs);

  if (!phrase || nowMs + 220 < phrase.startMs) return null;

  return (
    <div
      style={{
        position: 'absolute',
        zIndex: 50,
        left: 82,
        right: 82,
        bottom: 128,
        display: 'flex',
        justifyContent: 'center',
        fontFamily: 'Arial, Helvetica, sans-serif',
        fontSize: 49,
        lineHeight: 1.08,
        fontWeight: 900,
        letterSpacing: -1.7,
        textAlign: 'center',
        color: '#ffffff',
        textShadow: '0 5px 20px rgba(0,0,0,1)'
      }}
    >
      {phrase.text}
    </div>
  );
};
