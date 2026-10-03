import React from 'react';
import {Audio} from '@remotion/media';
import {Sequence, staticFile, useVideoConfig} from 'remotion';
import {Scene} from '../types';

type Props = {
  scenes: Scene[];
};

const soundFor = (type: Scene['type']) => {
  if (type === 'hook' || type === 'impact') return 'sfx/whoosh.wav';
  if (type === 'metric' || type === 'comparison') return 'sfx/drop.wav';
  return 'sfx/tick.wav';
};

const volumeFor = (type: Scene['type']) => {
  if (type === 'hook') return 0.09;
  if (type === 'metric') return 0.075;
  return 0.055;
};

export const SfxTrack: React.FC<Props> = ({scenes}) => {
  const {fps} = useVideoConfig();

  return (
    <>
      {scenes.map((scene, index) => {
        if (index === 0) return null;
        const from = Math.max(0, Math.round(scene.start * fps));
        return (
          <Sequence key={`sfx-${index}`} from={from} durationInFrames={Math.round(fps * 0.4)}>
            <Audio src={staticFile(soundFor(scene.type))} volume={volumeFor(scene.type)} />
          </Sequence>
        );
      })}
    </>
  );
};
