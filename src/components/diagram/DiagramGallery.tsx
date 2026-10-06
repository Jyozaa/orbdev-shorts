import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {Beat, DrawnDiagramVisual} from '../../types';
import {DrawnDiagram} from './DrawnDiagram';
import {DiagramContinuityTrack} from './DiagramContinuityTrack';

const DEMOS: DrawnDiagramVisual[] = [
  {type:'drawn-diagram',kind:'branch',labels:['CPU','GPU','NPU'],variant:0,transition:'morph'},
  {type:'drawn-diagram',kind:'orbit',labels:['TOOLS','MEMORY','FILES','WEB'],variant:1,transition:'morph'},
  {type:'drawn-diagram',kind:'flow',labels:['INPUT','MODEL','RESULT'],variant:0,transition:'morph'},
  {type:'drawn-diagram',kind:'growth',labels:['BEFORE','AFTER'],variant:1,transition:'morph'},
  {type:'drawn-diagram',kind:'stack',labels:['INPUT','CACHE','MEMORY','OUTPUT'],variant:0,transition:'morph'},
  {type:'drawn-diagram',kind:'comparison',labels:['OLD','NEW'],variant:0,transition:'morph'},
  {type:'drawn-diagram',kind:'timeline',labels:['START','CHANGE','NOW'],variant:1,transition:'morph'},
  {type:'drawn-diagram',kind:'wave',labels:['SIGNAL','OUTPUT'],variant:0,transition:'morph'},
  {type:'drawn-diagram',kind:'shield',labels:['PROTECTED'],variant:1,transition:'morph'},
  {type:'drawn-diagram',kind:'funnel',labels:['TEXT','IMAGE','AUDIO','MODEL'],variant:0,transition:'morph'},
  {type:'drawn-diagram',kind:'mesh',labels:['CONNECTED'],focus:3,variant:1,transition:'morph'},
];
const FPS=30, FRAMES_PER_SCENE=90;
const visualBeats:Beat[]=DEMOS.map((visual,i)=>({
  text:'',
  visual:{
    ...visual,
    continuityKey:'phase3-gallery',
    continuityIn:i>0,
    continuityOut:i<DEMOS.length-1,
  },
  start:i*FRAMES_PER_SCENE/FPS,
  end:(i+1)*FRAMES_PER_SCENE/FPS,
}));

export const DiagramGallery:React.FC=()=>(
  <AbsoluteFill style={{backgroundColor:'#050505'}}>
    {visualBeats.map((beat,i)=>(
      <Sequence key={(beat.visual as DrawnDiagramVisual).kind} from={i*FRAMES_PER_SCENE} durationInFrames={FRAMES_PER_SCENE}>
        <DrawnDiagram visual={beat.visual as DrawnDiagramVisual}/>
      </Sequence>
    ))}
    <DiagramContinuityTrack visualBeats={visualBeats}/>
  </AbsoluteFill>
);
