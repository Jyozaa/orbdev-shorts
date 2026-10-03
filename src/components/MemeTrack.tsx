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
import {Beat, SelectedMeme} from '../types';

const VisualMeme: React.FC<{meme: SelectedMeme}> = ({meme}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const age = frame / fps;
  const enter = Math.min(1, age / 0.08);
  const exitStart = Math.max(0, meme.durationSeconds - 0.10);
  const exit = age > exitStart ? Math.max(0, 1 - (age - exitStart) / 0.10) : 1;
  const opacity = enter * exit;

  if (meme.mediaType === 'audio') {
    return <Audio src={staticFile(meme.src)} volume={meme.volume ?? 0.58} />;
  }

  return (
    <AbsoluteFill
      style={{
        zIndex: 30,
        background: '#000000',
        alignItems: 'center',
        justifyContent: 'center',
        opacity
      }}
    >
      {meme.mediaType === 'image' ? (
        <Img
          src={staticFile(meme.src)}
          style={{width: 940, height: 1180, objectFit: 'contain'}}
        />
      ) : (
        <OffthreadVideo
          src={staticFile(meme.src)}
          volume={meme.volume ?? 0.44}
          style={{width: 940, height: 1180, objectFit: 'contain'}}
        />
      )}
    </AbsoluteFill>
  );
};

export const MemeTrack: React.FC<{beats: Beat[]}> = ({beats}) => {
  const {fps} = useVideoConfig();

  return (
    <>
      {beats.map((beat, index) => {
        if (!beat.meme || beat.start === undefined) return null;
        const meme = beat.meme;
        const from = Math.max(0, Math.round((beat.start + meme.offsetSeconds) * fps));
        const durationInFrames = Math.max(1, Math.round(meme.durationSeconds * fps));

        return (
          <Sequence
            key={`meme-${index}-${meme.id}`}
            from={from}
            durationInFrames={durationInFrames}
          >
            <VisualMeme meme={meme} />
          </Sequence>
        );
      })}
    </>
  );
};
