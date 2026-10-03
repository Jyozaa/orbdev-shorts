import React from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {BeatVisual} from './components/BeatVisual';
import {CaptionStrip} from './components/CaptionStrip';
import {MemeTrack} from './components/MemeTrack';
import {SfxTrack} from './components/SfxTrack';
import {StoryProps} from './types';

export const OrbdevShort: React.FC<StoryProps> = ({beats, captions}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const progress = Math.min(1, frame / Math.max(1, durationInFrames - 1));

  return (
    <AbsoluteFill style={{backgroundColor: '#000000', color: '#ffffff', overflow: 'hidden'}}>
      {beats.map((beat, index) => {
        if (beat.start === undefined || beat.end === undefined) return null;
        const from = Math.max(0, Math.round(beat.start * fps));
        const duration = Math.max(1, Math.round((beat.end - beat.start) * fps));
        return (
          <Sequence key={`beat-${index}`} from={from} durationInFrames={duration}>
            <BeatVisual beat={beat} />
          </Sequence>
        );
      })}

      <MemeTrack beats={beats} />
      <CaptionStrip captions={captions} />
      <SfxTrack beats={beats} />
      <Audio src={staticFile('voice.mp3')} volume={1} />

      <div
        style={{
          position: 'absolute',
          zIndex: 60,
          left: 0,
          bottom: 0,
          width: `${progress * 100}%`,
          height: 3,
          background: '#ffffff',
          opacity: 0.55
        }}
      />
    </AbsoluteFill>
  );
};
