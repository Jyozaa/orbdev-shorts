import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {CaptionWord} from '../types';

type Props = {
  captions: CaptionWord[];
};

export const CaptionStrip: React.FC<Props> = ({captions}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  if (captions.length === 0) {
    return null;
  }

  let activeIndex = captions.findIndex(
    (caption) => nowMs >= caption.startMs && nowMs < caption.endMs
  );

  if (activeIndex < 0) {
    for (let index = captions.length - 1; index >= 0; index -= 1) {
      if (captions[index].startMs <= nowMs) {
        activeIndex = index;
        break;
      }
    }
  }

  if (activeIndex < 0) {
    return null;
  }

  const groupStart = Math.floor(activeIndex / 5) * 5;
  const group = captions.slice(groupStart, groupStart + 5);
  const active = captions[activeIndex];
  const progress = interpolate(
    nowMs,
    [active.startMs, Math.max(active.endMs, active.startMs + 1)],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <div
      style={{
        position: 'absolute',
        left: 70,
        right: 70,
        bottom: 150,
        display: 'flex',
        justifyContent: 'center',
        flexWrap: 'wrap',
        gap: '12px 16px',
        fontFamily: 'Arial, Helvetica, sans-serif',
        fontSize: 54,
        lineHeight: 1.05,
        fontWeight: 800,
        letterSpacing: -1.5,
        textAlign: 'center',
        textShadow: '0 6px 28px rgba(0,0,0,0.55)'
      }}
    >
      {group.map((caption, index) => {
        const absoluteIndex = groupStart + index;
        const isActive = absoluteIndex === activeIndex;
        return (
          <span
            key={`${caption.startMs}-${caption.text}`}
            style={{
              color: isActive ? '#a9c7ff' : '#f4f7fb',
              opacity: isActive ? 1 : 0.78,
              transform: isActive ? `scale(${1.03 + progress * 0.015})` : 'scale(1)',
              display: 'inline-block'
            }}
          >
            {caption.text}
          </span>
        );
      })}
    </div>
  );
};
