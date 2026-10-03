import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {OrbdevShort} from './Short';
import {StoryProps} from './types';

const defaultProps: StoryProps = {
  slug: 'preview',
  title: 'orbdev preview',
  narration: 'A compact technology update.',
  durationSeconds: 6,
  beats: [
    {
      text: 'A compact technology update.',
      visual: {type: 'text', text: 'TECH UPDATE'},
      start: 0,
      end: 6
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
    durationInFrames={180}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={defaultProps}
    calculateMetadata={calculateMetadata}
  />
);
