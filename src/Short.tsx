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
        color: '#ffffff',
        overflow: 'hidden'
      }}
    >
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
          height: 3,
          background: '#ffffff',
          opacity: 0.72
        }}
      />
    </AbsoluteFill>
  );
};
