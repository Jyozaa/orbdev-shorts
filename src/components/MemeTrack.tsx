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
import {Scene, SelectedMeme} from '../types';

const VisualMeme: React.FC<{meme: SelectedMeme}> = ({meme}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const age = frame / fps;
  const enter = Math.min(1, age / 0.12);
  const exitStart = Math.max(0, meme.durationSeconds - 0.16);
  const exit = age > exitStart ? Math.max(0, 1 - (age - exitStart) / 0.16) : 1;
  const opacity = enter * exit;
  const scale = 0.92 + enter * 0.08;

  if (meme.mediaType === 'audio') {
    return <Audio src={staticFile(meme.src)} volume={meme.volume ?? 0.56} />;
  }

  return (
    <AbsoluteFill
      style={{
        alignItems: 'center',
        justifyContent: 'center',
        pointerEvents: 'none',
        zIndex: 20
      }}
    >
      <div
        style={{
          width: 820,
          height: 600,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity,
          transform: `scale(${scale})`
        }}
      >
        {meme.mediaType === 'image' ? (
          <Img
            src={staticFile(meme.src)}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain'
            }}
          />
        ) : (
          <OffthreadVideo
            src={staticFile(meme.src)}
            volume={meme.volume ?? 0.42}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain'
            }}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};

export const MemeTrack: React.FC<{scenes: Scene[]}> = ({scenes}) => {
  const {fps} = useVideoConfig();

  return (
    <>
      {scenes.map((scene, index) => {
        if (!scene.meme) return null;
        const meme = scene.meme;
        const from = Math.max(0, Math.round((scene.start + meme.offsetSeconds) * fps));
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
