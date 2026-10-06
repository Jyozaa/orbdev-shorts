import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {DrawnDiagramVisual} from '../../types';
import {DrawnDiagram} from './DrawnDiagram';

/**
 * Manual inspection-only gallery: no narration, network, media, or uploads.
 * npx remotion render src/index.ts OrbdevDiagramGallery out/diagram-gallery.mp4
 */
const DEMOS: DrawnDiagramVisual[] = [
  {type:'drawn-diagram',kind:'branch',labels:['CPU','GPU','NPU'],variant:0},
  {type:'drawn-diagram',kind:'orbit',labels:['TOOLS','MEMORY','FILES','WEB'],variant:1},
  {type:'drawn-diagram',kind:'flow',labels:['INPUT','MODEL','RESULT'],variant:0},
  {type:'drawn-diagram',kind:'growth',labels:['BEFORE','AFTER'],variant:1},
  {type:'drawn-diagram',kind:'stack',labels:['INPUT','CACHE','MEMORY','OUTPUT'],variant:0},
  {type:'drawn-diagram',kind:'comparison',labels:['OLD','NEW'],variant:0},
  {type:'drawn-diagram',kind:'timeline',labels:['START','CHANGE','NOW'],variant:1},
  {type:'drawn-diagram',kind:'wave',labels:['SIGNAL','OUTPUT'],variant:0},
  {type:'drawn-diagram',kind:'shield',labels:['PROTECTED'],variant:1},
  {type:'drawn-diagram',kind:'funnel',labels:['TEXT','IMAGE','AUDIO','MODEL'],variant:0},
  {type:'drawn-diagram',kind:'mesh',labels:['CONNECTED'],focus:3,variant:1},
];
const FRAMES_PER_SCENE = 90;

export const DiagramGallery: React.FC = () => (
  <AbsoluteFill style={{backgroundColor:'#050505'}}>
    {DEMOS.map((visual,i)=>(
      <Sequence key={visual.kind} from={i*FRAMES_PER_SCENE} durationInFrames={FRAMES_PER_SCENE}>
        <DrawnDiagram visual={visual} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
