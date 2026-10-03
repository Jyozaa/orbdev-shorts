import React from 'react';
import {Audio} from '@remotion/media';
import {Sequence, staticFile, useVideoConfig} from 'remotion';
import {Beat, ReactionSfx} from '../types';

const fileFor: Record<Exclude<ReactionSfx, 'none'>, string> = {
  scratch: 'sfx/scratch.wav',
  impact: 'sfx/impact.wav',
  whoosh: 'sfx/whoosh.wav',
  tick: 'sfx/tick.wav'
};

const volumeFor: Record<Exclude<ReactionSfx, 'none'>, number> = {
  scratch: 0.30,
  impact: 0.32,
  whoosh: 0.24,
  tick: 0.20
};

export const SfxTrack: React.FC<{beats: Beat[]}> = ({beats}) => {
  const {fps} = useVideoConfig();

  return (
    <>
      {beats.map((beat, index) => {
        const selected = beat.sfx ?? 'none';
        if (selected === 'none' || beat.start === undefined) return null;

        return (
          <Sequence
            key={`sfx-${index}-${selected}`}
            from={Math.max(0, Math.round(beat.start * fps))}
          >
            <Audio src={staticFile(fileFor[selected])} volume={volumeFor[selected]} />
          </Sequence>
        );
      })}
    </>
  );
};
