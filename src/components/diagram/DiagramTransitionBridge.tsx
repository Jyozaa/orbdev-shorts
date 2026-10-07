import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {DrawnDiagramVisual} from '../../types';
import {CANVAS, FAINT, INK, MUTED, Point, clamp01} from './Primitives';
import {diagramLayout, sampleAnchor} from './layout';
import {DIAGRAM_BASE_ZOOM} from './DiagramCanvas';

const smooth = (n:number) => {
  const t=clamp01(n);
  return t*t*(3-2*t);
};
const mix = (a:number,b:number,t:number)=>a+(b-a)*t;
const pointMix=(a:Point,b:Point,t:number):Point=>({x:mix(a.x,b.x,t),y:mix(a.y,b.y,t)});

const Edge:React.FC<{
  a:Point;b:Point;amount:number;opacity:number;reverse?:boolean;
}>=({a,b,amount,opacity,reverse=false})=>{
  const shown=clamp01(amount);
  return <line
    x1={a.x} y1={a.y} x2={b.x} y2={b.y}
    pathLength={100}
    stroke={reverse?FAINT:MUTED}
    strokeWidth={2.7}
    strokeLinecap="round"
    strokeDasharray="100"
    strokeDashoffset={100*(1-shown)}
    opacity={opacity}
  />;
};

/**
 * A short takeover around a scene boundary. Old geometry erases while the same
 * anchor particles physically travel to the next diagram positions; incoming
 * topology then draws around those persisted particles.
 */
export const DiagramTransitionBridge:React.FC<{
  from:DrawnDiagramVisual;
  to:DrawnDiagramVisual;
}>=({from,to})=>{
  const frame=useCurrentFrame();
  const {durationInFrames}=useVideoConfig();
  const raw=clamp01(frame/Math.max(1,durationInFrames-1));

  // Phase 1: erase the outgoing topology.
  // Phase 2: move persistent anchors.
  // Phase 3: draw the incoming skeleton while the real incoming diagram starts
  // drawing underneath. The opaque bridge background then dissolves rather
  // than disappearing in a single frame.
  const motion=smooth((raw-0.06)/0.70);
  const a=diagramLayout(from),b=diagramLayout(to);
  const count=Math.max(a.anchors.length,b.anchors.length);
  const moving=Array.from({length:count},(_,i)=>
    pointMix(sampleAnchor(a.anchors,i),sampleAnchor(b.anchors,i),motion));
  const oldEdgeAmount=1-smooth(raw/0.46);
  const newEdgeAmount=smooth((raw-0.42)/0.58);
  const bridgeGeometryOpacity=1-smooth((raw-0.78)/0.22);
  const backdropOpacity=1-smooth((raw-0.56)/0.44);
  const center=pointMix(a.center,b.center,motion);
  const halo=interpolate(Math.sin(raw*Math.PI),[0,1],[0,0.16])*bridgeGeometryOpacity;

  return <AbsoluteFill style={{
    background:`rgba(5,5,5,${backdropOpacity})`,
    zIndex:4,
    pointerEvents:'none',
  }}>
    <svg viewBox="0 0 1080 1920" width="100%" height="100%"
      style={{opacity:bridgeGeometryOpacity}}>
      <g transform={`translate(540 940) scale(${DIAGRAM_BASE_ZOOM}) translate(-540 -940)`}>
      <circle cx={center.x} cy={center.y} r={250+45*Math.sin(raw*Math.PI)}
        fill="none" stroke={INK} strokeWidth={1.2} opacity={halo}/>
      {a.edges.map(([i,j],index)=><Edge key={`old-${index}`}
        a={moving[Math.min(i,count-1)]} b={moving[Math.min(j,count-1)]}
        amount={oldEdgeAmount} opacity={(1-motion)*0.62} reverse />)}
      {b.edges.map(([i,j],index)=><Edge key={`new-${index}`}
        a={moving[Math.min(i,count-1)]} b={moving[Math.min(j,count-1)]}
        amount={newEdgeAmount} opacity={motion*0.82}/>)}
      {moving.map((p,i)=>{
        const ar=a.radii[Math.min(i,a.radii.length-1)]??10;
        const br=b.radii[Math.min(i,b.radii.length-1)]??10;
        const radius=mix(ar,br,motion);
        const focus=i===0?1:0.72;
        return <g key={i}>
          <circle cx={p.x} cy={p.y} r={radius+9*Math.sin(raw*Math.PI)}
            fill={CANVAS} stroke={INK} strokeWidth={2.6}
            opacity={0.82*focus+0.18}/>
          <circle cx={p.x} cy={p.y} r={Math.max(4,radius*0.30)}
            fill={INK} opacity={0.74+0.26*Math.sin(raw*Math.PI)}/>
        </g>;
      })}
      </g>
    </svg>
  </AbsoluteFill>;
};
