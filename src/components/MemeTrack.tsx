import React from 'react';
import {Audio} from '@remotion/media';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {Beat, Cutaway, SelectedMeme} from '../types';

const OverlayMeme: React.FC<{meme: SelectedMeme}> = ({meme}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const age = frame / fps;
  const enter = Math.min(1, age / 0.08);
  const exitStart = Math.max(0, meme.durationSeconds - 0.10);
  const exit = age > exitStart ? Math.max(0, 1 - (age - exitStart) / 0.10) : 1;
  const opacity = enter * exit;

  if (meme.mediaType === 'audio') {
    return <Audio src={staticFile(meme.src)} volume={meme.volume ?? 0.60} />;
  }

  return (
    <AbsoluteFill
      style={{
        zIndex: 30,
        pointerEvents: 'none',
        alignItems: 'center',
        justifyContent: 'center',
        opacity
      }}
    >
      <div
        style={{
          width: 820,
          height: 820,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {meme.mediaType === 'image' ? (
          <Img src={staticFile(meme.src)} style={{maxWidth: '100%', maxHeight: '100%', objectFit: 'contain'}} />
        ) : (
          <OffthreadVideo
            src={staticFile(meme.src)}
            volume={meme.volume ?? 0.44}
            style={{maxWidth: '100%', maxHeight: '100%', objectFit: 'contain'}}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};

const CutawayMeme: React.FC<{meme: SelectedMeme}> = ({meme}) => {
  if (meme.mediaType === 'audio') {
    return (
      <AbsoluteFill style={{zIndex: 80, backgroundColor: '#000000'}}>
        <Audio src={staticFile(meme.src)} volume={meme.volume ?? 0.72} />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        zIndex: 80,
        backgroundColor: '#000000',
        alignItems: 'center',
        justifyContent: 'center'
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
          volume={meme.volume ?? 0.78}
          style={{width: '100%', height: '100%', objectFit: 'contain'}}
        />
      )}
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
            <OverlayMeme meme={meme} />
          </Sequence>
        );
      })}

      {cutaways.map((cutaway, index) => (
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
