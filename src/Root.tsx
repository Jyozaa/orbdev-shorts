import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {OrbdevShort} from './Short';
import {StoryProps} from './types';

const defaultProps: StoryProps = {
  slug: 'preview',
  title: 'orbdev preview',
  narration: 'A compact technology update from orbdev.',
  plannedDurationSeconds: 10,
  durationSeconds: 10,
  scenes: [
    {
      type: 'hook',
      start: 0,
      end: 7,
      kicker: 'QUICK UPDATE',
      title: 'A compact technology update'
    },
    {
      type: 'outro',
      start: 7,
      end: 10,
      title: 'orbdev'
    }
  ],
  captions: []
};

const calculateMetadata: CalculateMetadataFunction<StoryProps> = ({props}) => ({
  durationInFrames: Math.max(1, Math.ceil(props.durationSeconds * 30))
});

export const Root: React.FC = () => (
  <Composition
    id="OrbdevShort"
    component={OrbdevShort}
    durationInFrames={300}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={defaultProps}
    calculateMetadata={calculateMetadata}
  />
);
