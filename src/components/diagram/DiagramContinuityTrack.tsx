import React from 'react';
import {Sequence, useVideoConfig} from 'remotion';
import {Beat, DrawnDiagramVisual} from '../../types';
import {DiagramTransitionBridge} from './DiagramTransitionBridge';

const isDrawn=(beat:Beat):beat is Beat&{visual:DrawnDiagramVisual} =>
  beat.visual.type==='drawn-diagram';

export const DiagramContinuityTrack:React.FC<{visualBeats:Beat[]}>=({visualBeats})=>{
  const {fps}=useVideoConfig();
  const bridges:React.ReactNode[]=[];

  for(let i=0;i<visualBeats.length-1;i++){
    const current=visualBeats[i],next=visualBeats[i+1];
    if(!isDrawn(current)||!isDrawn(next))continue;
    if(!current.visual.continuityKey||current.visual.continuityKey!==next.visual.continuityKey)continue;
    if(current.visual.transition==='cut'||next.visual.transition==='cut')continue;
    if(current.start===undefined||current.end===undefined||next.start===undefined||next.end===undefined)continue;
    const gap=Math.abs(next.start-current.end);
    if(gap>0.12)continue;

    const prevFrames=Math.max(1,Math.round((current.end-current.start)*fps));
    const nextFrames=Math.max(1,Math.round((next.end-next.start)*fps));
    // Give the bridge enough time to complete the anchor movement and let the
    // incoming diagram visibly draw after the boundary. Slightly more of the
    // transition lives on the incoming side than the outgoing side.
    const duration=Math.max(22,Math.min(32,Math.floor(Math.min(prevFrames,nextFrames)*0.55)));
    const boundary=Math.round(next.start*fps);
    const start=Math.max(0,boundary-Math.floor(duration*0.42));

    bridges.push(
      <Sequence key={`diagram-bridge-${i}`} from={start} durationInFrames={duration}>
        <DiagramTransitionBridge from={current.visual} to={next.visual}/>
      </Sequence>
    );
  }
  return <>{bridges}</>;
};
