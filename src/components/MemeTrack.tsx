import React from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  staticFile,
  spring,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {Beat, Cutaway, SelectedMeme} from '../types';

const OverlayMeme: React.FC<{meme: SelectedMeme; side: 'left' | 'right'}> = ({meme, side}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({
    frame,
    fps,
    config: {damping: 16, stiffness: 210, mass: 0.45}
  });
  const age = frame / fps;
  const exitStart = Math.max(0, meme.durationSeconds - 0.10);
  const exit = age > exitStart ? Math.max(0, 1 - (age - exitStart) / 0.10) : 1;
  const opacity = enter * exit;

  if (meme.mediaType === 'audio') {
    return <Audio src={staticFile(meme.src)} volume={meme.volume ?? 0.60} />;
  }

  const x = (1 - enter) * (side === 'right' ? 120 : -120);

  return (
    <AbsoluteFill style={{zIndex: 35, pointerEvents: 'none', opacity}}>
      <div
        style={{
          position: 'absolute',
          top: 430,
          [side]: 54,
          width: 430,
          height: 430,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#000000',
          border: '3px solid rgba(255,255,255,0.65)',
          borderRadius: 28,
          overflow: 'hidden',
          transform: `translateX(${x}px) rotate(${side === 'right' ? -2 : 2}deg) scale(${0.84 + enter * 0.16})`,
          boxShadow: '0 18px 70px rgba(0,0,0,0.7)'
        }}
      >
        {meme.mediaType === 'image' ? (
          <Img
            src={staticFile(meme.src)}
            style={{width: '100%', height: '100%', objectFit: 'contain'}}
          />
        ) : (
          <OffthreadVideo
            src={staticFile(meme.src)}
            volume={meme.hasAudio ? (meme.volume ?? 0.44) : 0}
            style={{width: '100%', height: '100%', objectFit: 'contain'}}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};

const CutawayMeme: React.FC<{meme: SelectedMeme}> = ({meme}) => {
  if (meme.mediaType !== 'video' || !meme.hasAudio) return null;

  return (
    <AbsoluteFill
      style={{
        zIndex: 80,
        backgroundColor: '#000000',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      <OffthreadVideo
        src={staticFile(meme.src)}
        volume={meme.volume ?? 0.78}
        style={{width: '100%', height: '100%', objectFit: 'contain'}}
      />
    </AbsoluteFill>
  );
};

export const MemeTrack: React.FC<{beats: Beat[]; cutaways: Cutaway[]}> = ({beats, cutaways}) => {
  const {fps} = useVideoConfig();

  return (
    <>
      {beats.map((beat, index) => {
        if (!beat.meme || beat.start === undefined || beat.meme.presentation !== 'overlay') return null;
        const meme = beat.meme;
        const from = Math.max(0, Math.round((beat.start + meme.offsetSeconds) * fps));
        const durationInFrames = Math.max(1, Math.round(meme.durationSeconds * fps));
        return (
          <Sequence key={`overlay-${index}-${meme.id}`} from={from} durationInFrames={durationInFrames}>
            <OverlayMeme meme={meme} side={index % 2 === 0 ? 'right' : 'left'} />
          </Sequence>
        );
      })}

      {cutaways
        .filter((cutaway) => cutaway.meme.mediaType === 'video' && cutaway.meme.hasAudio)
        .map((cutaway, index) => (
          <Sequence
            key={`cutaway-${index}-${cutaway.meme.id}`}
            from={Math.max(0, Math.round(cutaway.start * fps))}
            durationInFrames={Math.max(1, Math.round((cutaway.end - cutaway.start) * fps))}
          >
            <CutawayMeme meme={cutaway.meme} />
          </Sequence>
        ))}
    </>
  );
};
