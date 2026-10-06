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
import {DiagramContinuityTrack} from './components/diagram/DiagramContinuityTrack';
import {StoryProps} from './types';

export const OrbdevShort: React.FC<StoryProps> = ({beats, visualBeats, captions, cutaways}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const progress = Math.min(1, frame / Math.max(1, durationInFrames - 1));
  const nowSeconds = frame / fps;
  const overlayReactionActive = beats.some((beat) => {
    const meme = beat.meme;
    if (!meme || beat.start === undefined || meme.presentation !== 'overlay' || !meme.hasAudio) return false;
    const start = beat.start + meme.offsetSeconds;
    return nowSeconds >= start && nowSeconds < start + meme.durationSeconds;
  });
  const cutawayActive = cutaways.some((cutaway) => nowSeconds >= cutaway.start && nowSeconds < cutaway.end);
  const voiceVolume = cutawayActive ? 0.02 : overlayReactionActive ? 0.52 : 1;

  return (
    <AbsoluteFill style={{backgroundColor: '#000000', color: '#ffffff', overflow: 'hidden'}}>
      {visualBeats.map((beat, index) => {
        if (beat.start === undefined || beat.end === undefined) return null;
        const from = Math.max(0, Math.round(beat.start * fps));
        const duration = Math.max(1, Math.round((beat.end - beat.start) * fps));
        return (
          <Sequence key={`beat-${index}`} from={from} durationInFrames={duration}>
            <BeatVisual beat={beat} />
          </Sequence>
        );
      })}
      <DiagramContinuityTrack visualBeats={visualBeats} />

      <MemeTrack beats={beats} cutaways={cutaways} />
      <CaptionStrip captions={captions} cutaways={cutaways} />
      <SfxTrack beats={beats} />
      <Audio src={staticFile('voice.mp3')} volume={voiceVolume} />

      <div
        style={{
          position: 'absolute',
          zIndex: 100,
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
