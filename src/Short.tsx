import React from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {CaptionStrip} from './components/CaptionStrip';
import {SceneCard} from './components/SceneCard';
import {SfxTrack} from './components/SfxTrack';
import {StoryProps} from './types';

export const OrbdevShort: React.FC<StoryProps> = ({scenes, captions}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const progress = Math.min(1, frame / Math.max(1, durationInFrames - 1));

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#000000',
        color: '#f7f7f7',
        overflow: 'hidden'
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 70,
          left: 72,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          fontFamily: 'Arial, Helvetica, sans-serif',
          fontSize: 27,
          fontWeight: 900,
          letterSpacing: -1,
          opacity: 0.88
        }}
      >
        <div
          style={{
            width: 24,
            height: 24,
            borderRadius: '50%',
            border: '5px solid #9fc1ff'
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
      <SfxTrack scenes={scenes} />
      <Audio src={staticFile('voice.mp3')} volume={1} />

      <div
        style={{
          position: 'absolute',
          left: 0,
          bottom: 0,
          width: `${progress * 100}%`,
          height: 4,
          background: '#9fc1ff'
        }}
      />
    </AbsoluteFill>
  );
};
