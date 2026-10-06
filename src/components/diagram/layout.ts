import {DrawnDiagramVisual} from '../../types';
import {Point} from './Primitives';

export type DiagramLayoutState = {
  anchors: Point[];
  edges: Array<[number, number]>;
  radii: number[];
  center: Point;
};

const v = (visual: DrawnDiagramVisual) => ((visual.variant ?? 0) % 4 + 4) % 4;

/**
 * Canonical semantic anchors for every diagram family.
 * These coordinates intentionally match the Phase 2 drawings closely enough
 * that a continuity bridge can take over without a perceptible jump.
 */
export const diagramLayout = (visual: DrawnDiagramVisual): DiagramLayoutState => {
  const kind = visual.kind;
  const variant = v(visual);

  if (kind === 'branch') {
    const rootY = variant % 2 ? 680 : 750;
    const count = Math.max(2, Math.min(4, visual.labels?.length || 3));
    const xs = Array.from({length: count}, (_, i) =>
      300 + i * (480 / Math.max(1, count - 1)));
    return {
      anchors: [{x:540,y:rootY}, ...xs.map(x => ({x,y:1180}))],
      edges: xs.map((_, i) => [0, i + 1] as [number, number]),
      radii: [25, ...xs.map(() => 17)],
      center: {x:540,y:930},
    };
  }

  if (kind === 'orbit') {
    const rx = variant % 2 ? 316 : 290;
    const ry = variant % 2 ? 225 : 290;
    const angles = [-Math.PI / 2, 0, Math.PI / 2, Math.PI];
    const outer = angles.map(a => ({x:540 + Math.cos(a)*rx,y:930 + Math.sin(a)*ry}));
    return {
      anchors: [{x:540,y:930}, ...outer],
      edges: outer.map((_, i) => [0, i + 1] as [number, number]),
      radii: [24, ...outer.map(() => 16)],
      center: {x:540,y:930},
    };
  }

  if (kind === 'flow') {
    const count = Math.max(2, Math.min(4, visual.labels?.length || 3));
    const total=780, cell=135, step=(total-cell)/Math.max(1,count-1), x0=150;
    const y=variant%2?988:918;
    const anchors=Array.from({length:count},(_,i)=>({x:x0+i*step+cell/2,y}));
    return {
      anchors,
      edges: anchors.slice(0,-1).map((_,i)=>[i,i+1] as [number,number]),
      radii: anchors.map(()=>18),
      center:{x:540,y},
    };
  }

  if (kind === 'growth') {
    const rise=variant%2?80:0;
    const anchors=[
      {x:275,y:1130},{x:480,y:1030},{x:692,y:833},{x:815,y:700+rise},
    ];
    return {
      anchors,edges:[[0,1],[1,2],[2,3]],radii:[10,10,12,22],
      center:{x:545,y:930},
    };
  }

  if (kind === 'stack') {
    const count=Math.max(3,Math.min(5,visual.labels?.length||4));
    const offset=variant%2?36:0;
    const anchors=Array.from({length:count},(_,i)=>({
      x:286+(i%2)*offset+250,y:720+i*137+47,
    }));
    return {
      anchors,
      edges:anchors.slice(0,-1).map((_,i)=>[i,i+1] as [number,number]),
      radii:anchors.map((_,i)=>i===count-1?17:11),
      center:{x:540,y:960},
    };
  }

  if (kind === 'comparison') {
    const left=variant%2?310:333,right=1080-left;
    return {
      anchors:[{x:left,y:930},{x:540,y:930},{x:right,y:930}],
      edges:[[0,1],[1,2]],radii:[25,9,30],center:{x:540,y:930},
    };
  }

  if (kind === 'timeline') {
    const y=variant%2?1020:940;
    return {
      anchors:[{x:280,y},{x:540,y},{x:800,y}],
      edges:[[0,1],[1,2]],radii:[16,16,20],center:{x:540,y},
    };
  }

  if (kind === 'wave') {
    return {
      anchors:[{x:225,y:930},{x:430,y:930},{x:650,y:930},{x:856,y:930}],
      edges:[[0,1],[1,2],[2,3]],radii:[22,7,7,22],center:{x:540,y:930},
    };
  }

  if (kind === 'shield') {
    const x=variant%2?560:540;
    return {
      anchors:[{x:240,y:515},{x:540,y:515},{x:840,y:515},{x,y:897}],
      edges:[[0,3],[1,3],[2,3]],radii:[8,8,8,28],center:{x,y:897},
    };
  }

  if (kind === 'funnel') {
    const topY=variant%2?720:650;
    return {
      anchors:[{x:320,y:topY},{x:540,y:topY},{x:760,y:topY},{x:540,y:1120}],
      edges:[[0,3],[1,3],[2,3]],radii:[18,18,18,31],center:{x:540,y:940},
    };
  }

  const anchors=[
    {x:340,y:730},{x:705,y:765},{x:260,y:998},
    {x:520,y:950},{x:800,y:1040},{x:470,y:1210},
  ];
  return {
    anchors,
    edges:[[0,2],[0,3],[1,3],[1,4],[2,3],[3,4],[3,5],[4,5]],
    radii:anchors.map((_,i)=>i===(visual.focus??3)?20:12),
    center:{x:520,y:950},
  };
};

export const sampleAnchor = (anchors: Point[], index: number): Point =>
  anchors[Math.min(index, Math.max(0, anchors.length - 1))] ?? {x:540,y:930};
