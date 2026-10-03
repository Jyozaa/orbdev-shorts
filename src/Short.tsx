import React from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {CaptionStrip} from './components/CaptionStrip';
import {SceneCard} from './components/SceneCard';
import {StoryProps} from './types';

export const OrbdevShort: React.FC<StoryProps> = ({scenes, captions}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const progress = Math.min(1, frame / Math.max(1, durationInFrames - 1));
  const glowX = interpolate(frame, [0, durationInFrames], [18, 82], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#080a0e',
        color: '#f4f7fb',
        overflow: 'hidden'
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(circle at ${glowX}% 18%, rgba(73,117,196,0.24), transparent 34%), radial-gradient(circle at 78% 78%, rgba(80,95,132,0.18), transparent 28%)`
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.13,
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)',
          backgroundSize: '72px 72px'
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 82,
          left: 76,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontSize: 31,
          fontWeight: 900,
          letterSpacing: -1
        }}
      >
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: '50%',
            border: '8px solid #a9c7ff',
            boxShadow: '0 0 34px rgba(169,199,255,0.3)'
          }}
        />
        orbdev
      </div>

      {scenes.map((scene, index) => {
        const from = Math.max(0, Math.round(scene.start * fps));
        const duration = Math.max(1, Math.round((scene.end - scene.start) * fps));
        return (
          <Sequence key={`${scene.type}-${index}`} from={from} durationInFrames={duration}>
            <SceneCard scene={scene} />
          </Sequence>
        );
      })}

      <CaptionStrip captions={captions} />
      <Audio src={staticFile('voice.mp3')} />

      <div
        style={{
          position: 'absolute',
          left: 0,
          bottom: 0,
          width: `${progress * 100}%`,
          height: 10,
          background: '#a9c7ff'
        }}
      />
    </AbsoluteFill>
  );
};
