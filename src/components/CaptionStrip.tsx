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

  if (captions.length === 0) return null;

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

  if (activeIndex < 0) return null;

  const groupStart = Math.floor(activeIndex / 4) * 4;
  const group = captions.slice(groupStart, groupStart + 4);
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
        left: 76,
        right: 76,
        bottom: 142,
        display: 'flex',
        justifyContent: 'center',
        flexWrap: 'wrap',
        gap: '9px 15px',
        fontFamily: 'Arial, Helvetica, sans-serif',
        fontSize: 53,
        lineHeight: 1.04,
        fontWeight: 800,
        letterSpacing: -1.6,
        textAlign: 'center',
        color: '#ffffff',
        textShadow: '0 4px 18px rgba(0,0,0,0.95)'
      }}
    >
      {group.map((caption, index) => {
        const absoluteIndex = groupStart + index;
        const isActive = absoluteIndex === activeIndex;
        return (
          <span
            key={`${caption.startMs}-${caption.text}`}
            style={{
              color: '#ffffff',
              opacity: isActive ? 1 : 0.82,
              fontWeight: isActive ? 950 : 800,
              transform: isActive ? `scale(${1.045 + progress * 0.01})` : 'scale(1)',
              display: 'inline-block',
              borderBottom: isActive ? '5px solid #ffffff' : '5px solid transparent',
              paddingBottom: 4
            }}
          >
            {caption.text}
          </span>
        );
      })}
    </div>
  );
};
