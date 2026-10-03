import React from 'react';
import {Audio} from '@remotion/media';
import {Sequence, staticFile, useVideoConfig} from 'remotion';
import {ReactionSfx, Scene} from '../types';

type Props = {
  scenes: Scene[];
};

const fallbackFor = (scene: Scene): ReactionSfx => {
  if (scene.type === 'metric') return 'impact';
  if (scene.type === 'comparison') return 'whoosh';
  if (scene.type === 'caveat') return 'scratch';
  if (scene.type === 'diagram') return 'tick';
  return 'none';
};

const fileFor: Record<Exclude<ReactionSfx, 'none'>, string> = {
  scratch: 'sfx/scratch.wav',
  impact: 'sfx/impact.wav',
  whoosh: 'sfx/whoosh.wav',
  tick: 'sfx/tick.wav'
};

const volumeFor: Record<Exclude<ReactionSfx, 'none'>, number> = {
  scratch: 0.42,
  impact: 0.44,
  whoosh: 0.34,
  tick: 0.28
};

export const SfxTrack: React.FC<Props> = ({scenes}) => {
  const {fps} = useVideoConfig();

  return (
    <>
      {scenes.map((scene, index) => {
        const selected = scene.sfx ?? fallbackFor(scene);
        if (selected === 'none') return null;

        const from = Math.max(0, Math.round(scene.start * fps));
        const duration = Math.max(1, Math.round(fps * 0.75));

        return (
          <Sequence key={`sfx-${index}-${selected}`} from={from} durationInFrames={duration}>
            <Audio src={staticFile(fileFor[selected])} volume={volumeFor[selected]} />
          </Sequence>
        );
      })}
    </>
  );
};
