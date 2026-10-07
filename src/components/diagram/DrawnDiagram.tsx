import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {DrawnDiagramVisual} from '../../types';
import {DiagramCanvas} from './DiagramCanvas';
import {
  DrawArrow, DrawDot, DrawLabel, DrawPath, DrawRect, DrawRing,
  FAINT, INK, MUTED, clamp01, makeWave,
} from './Primitives';

type SceneProps = {visual: DrawnDiagramVisual; p: number};

const item = (v: DrawnDiagramVisual, i: number) => (v.labels || [])[i] || '';
const variant = (v: DrawnDiagramVisual) => ((v.variant || 0) % 4 + 4) % 4;

/** Each family has a different geometric structure, not a renamed fanout. */
const Branch: React.FC<SceneProps> = ({visual, p}) => {
  const count = Math.max(2, Math.min(4, (visual.labels || []).length || 3));
  const x = Array.from({length: count}, (_, i) =>
    300 + i * (480 / Math.max(1, count - 1))
  );
  const rootY = variant(visual) % 2 ? 680 : 750;
  const tipY = 1180;
  return <g>
    <DrawDot x={540} y={rootY} radius={25} hollow progress={p} delay={0.03} />
    {x.map((cx, i) => <g key={i}>
      <DrawPath
        d={`M 540 ${rootY + 26} Q ${540 + (cx - 540) * 0.20} 915 ${cx} ${tipY - 21}`}
        progress={p} delay={0.14 + i * 0.07} span={0.44} />
      <DrawDot x={cx} y={tipY} radius={17} progress={p}
        delay={0.43 + i * 0.07} />
      <DrawLabel x={cx} y={tipY + 65} text={item(visual, i)} progress={p}
        delay={0.51 + i * 0.06} size={24} color={MUTED} />
    </g>)}
  </g>;
};

const Orbit: React.FC<SceneProps> = ({visual, p}) => {
  const angles = [-Math.PI / 2, 0, Math.PI / 2, Math.PI];
  const rx = variant(visual) % 2 ? 316 : 290;
  const ry = variant(visual) % 2 ? 225 : 290;
  return <g>
    <DrawRing cx={540} cy={930} r={90} progress={p} delay={0.05} span={0.42} />
    <DrawRing cx={540} cy={930} r={235} stroke={FAINT}
      width={2.2} progress={p} delay={0.16} span={0.60} />
    <DrawDot x={540} y={930} radius={19} progress={p} delay={0.14} pulse />
    {angles.map((a, i) => {
      const px = 540 + Math.cos(a) * rx;
      const py = 930 + Math.sin(a) * ry;
      return <g key={i}>
        <DrawPath d={`M 540 930 L ${px} ${py}`}
          stroke={MUTED} width={2} opacity={0.55}
          progress={p} delay={0.22 + i * 0.06} span={0.37} />
        <DrawRing cx={px} cy={py} r={29} progress={p}
          delay={0.34 + i * 0.06} span={0.26} />
        <DrawDot x={px} y={py} radius={5} progress={p}
          delay={0.50 + i * 0.06} />
        <DrawLabel x={px} y={py + (i === 2 ? 74 : 69)}
          text={item(visual, i)} size={22} progress={p}
          delay={0.50 + i * 0.06} color={MUTED} />
      </g>;
    })}
  </g>;
};

const Flow: React.FC<SceneProps> = ({visual, p}) => {
  const count = Math.max(2, Math.min(4, (visual.labels || []).length || 3));
  const total = 780;
  const cell = 135;
  const step = (total - cell) / Math.max(1, count - 1);
  const x0 = 150;
  const y = variant(visual) % 2 ? 930 : 860;
  return <g>
    {Array.from({length: count}, (_, i) => {
      const x = x0 + i * step;
      return <g key={i}>
        <DrawRect x={x} y={y} width={cell} height={116} radius={28}
          progress={p} delay={0.07 + i * 0.15} span={0.33}
          stroke={i === count - 1 ? INK : MUTED} weight={2.6} />
        <DrawDot x={x + cell / 2} y={y + 58} radius={12}
          hollow={i > 0} progress={p} delay={0.18 + i * 0.15} />
        <DrawLabel x={x + cell / 2} y={y + 169}
          text={item(visual, i)} progress={p} delay={0.24 + i * 0.14} size={24} />
        {i < count - 1 && <DrawArrow
          from={{x:x + cell + 15, y:y + 58}}
          to={{x:x + step - 17, y:y + 58}}
          progress={p} delay={0.20 + i * 0.15} span={0.32}
          stroke={MUTED} width={2.6} head={10} />}
      </g>;
    })}
  </g>;
};

const Growth: React.FC<SceneProps> = ({visual, p}) => {
  const rise = variant(visual) % 2 ? 80 : 0;
  const d = `M 275 1130 C 370 1155 412 995 480 1030 S 650 900 692 833 S 755 765 ${815} ${700 + rise}`;
  return <g>
    <DrawArrow from={{x:230,y:1200}} to={{x:855,y:1200}}
      progress={p} stroke={MUTED} delay={0.01} span={0.35} />
    <DrawArrow from={{x:230,y:1200}} to={{x:230,y:670}}
      progress={p} stroke={MUTED} delay={0.07} span={0.35} />
    <DrawPath d={d} progress={p} delay={0.22} span={0.56} width={4.5} />
    <DrawRing cx={815} cy={700 + rise} r={23} progress={p}
      delay={0.71} span={0.19} />
    <DrawDot x={815} y={700 + rise} radius={7} progress={p}
      delay={0.76} pulse />
    <DrawLabel x={282} y={1260} text={item(visual, 0)} progress={p}
      delay={0.37} color={MUTED} anchor="start" />
    <DrawLabel x={798} y={655 + rise} text={item(visual, 1)} progress={p}
      delay={0.78} color={INK} size={27} />
  </g>;
};

const Stack: React.FC<SceneProps> = ({visual, p}) => {
  const count = Math.max(3, Math.min(5, (visual.labels || []).length || 4));
  const offset = variant(visual) % 2 ? 36 : 0;
  return <g>
    {Array.from({length: count}, (_, i) => {
      const y = 720 + i * 137;
      const x = 286 + (i % 2) * offset;
      return <g key={i}>
        <DrawRect x={x} y={y} width={500} height={94}
          radius={19} stroke={i === count - 1 ? INK : MUTED}
          weight={2.9} progress={p} delay={0.07 + i * 0.13} span={0.30} />
        <DrawDot x={x + 37} y={y + 47} radius={8} progress={p}
          delay={0.16 + i * 0.13} hollow={i < count - 1} />
        <DrawLabel x={x + 80} y={y + 55} text={item(visual, i)}
          anchor="start" size={27} progress={p}
          delay={0.23 + i * 0.12} />
        {i < count - 1 && <DrawPath
          d={`M ${x + 250} ${y + 95} L ${x + 250} ${y + 136}`}
          progress={p} delay={0.27 + i * 0.13}
          span={0.24} stroke={MUTED} width={2} />}
      </g>;
    })}
  </g>;
};

const Comparison: React.FC<SceneProps> = ({visual, p}) => {
  const left = variant(visual) % 2 ? 310 : 333;
  const right = 1080 - left;
  return <g>
    <DrawPath d="M 540 650 L 540 1235" progress={p}
      stroke={FAINT} width={3} delay={0.03} span={0.35} />
    <DrawRing cx={left} cy={930} r={116} progress={p} delay={0.11} span={0.45}
      stroke={MUTED} width={3.1} />
    <DrawDot x={left} y={930} radius={13} progress={p} delay={0.27} hollow />
    <DrawRing cx={right} cy={930} r={116} progress={p} delay={0.28} span={0.43} />
    <DrawRing cx={right} cy={930} r={78} progress={p} delay={0.36}
      span={0.38} stroke={MUTED} width={2.4} />
    <DrawDot x={right} y={930} radius={22} progress={p} delay={0.54} pulse />
    <DrawLabel x={left} y={1147} text={item(visual, 0)}
      progress={p} delay={0.56} size={28} color={MUTED} />
    <DrawLabel x={right} y={1147} text={item(visual, 1)}
      progress={p} delay={0.63} size={28} />
  </g>;
};

const Timeline: React.FC<SceneProps> = ({visual, p}) => {
  const y = variant(visual) % 2 ? 1020 : 940;
  const xs = [280, 540, 800];
  return <g>
    <DrawArrow from={{x:210,y}} to={{x:880,y}} progress={p}
      delay={0.06} span={0.53} stroke={MUTED} width={2.8} head={15} />
    {xs.map((x, i) => <g key={i}>
      <DrawRing cx={x} cy={y} r={31} progress={p}
        delay={0.21 + i * 0.18} span={0.30} />
      <DrawDot x={x} y={y} radius={8} progress={p}
        delay={0.31 + i * 0.18} />
      <DrawPath
        d={`M ${x} ${y + 35} L ${x} ${y + 91 + (i % 2) * 32}`}
        progress={p} delay={0.35 + i * 0.16} span={0.20}
        stroke={FAINT} width={2} />
      <DrawLabel x={x} y={y + 143 + (i % 2) * 32}
        text={item(visual, i)} progress={p} delay={0.48 + i * 0.16}
        color={i === 2 ? INK : MUTED} size={25} />
    </g>)}
  </g>;
};

const Wave: React.FC<SceneProps> = ({visual, p}) => {
  const amplitude = variant(visual) % 2 ? 67 : 96;
  return <g>
    <DrawRing cx={225} cy={930} r={33} progress={p} delay={0.04} span={0.34} />
    <DrawDot x={225} y={930} radius={6} progress={p} delay={0.17} />
    <DrawPath d={makeWave(279,930,555,amplitude,3.25)}
      progress={p} delay={0.19} span={0.59} width={3.4} />
    <DrawRing cx={856} cy={930} r={30} progress={p}
      delay={0.68} span={0.25} />
    <DrawDot x={856} y={930} radius={7} progress={p}
      delay={0.75} pulse />
    <DrawLabel x={230} y={1055} text={item(visual, 0)}
      progress={p} delay={0.34} size={25} color={MUTED} />
    <DrawLabel x={845} y={1055} text={item(visual, 1)}
      progress={p} delay={0.76} size={25} />
  </g>;
};

const Shield: React.FC<SceneProps> = ({visual, p}) => {
  const x = variant(visual) % 2 ? 560 : 540;
  const shield = `M ${x} 651 C ${x + 86} 716 ${x + 158} 721 ${x + 170} 721 L ${x + 159} 980 Q ${x + 127} 1101 ${x} 1194 Q ${x - 127} 1101 ${x - 159} 980 L ${x - 170} 721 C ${x - 155} 721 ${x - 86} 716 ${x} 651 Z`;
  return <g>
    <DrawPath d={shield} progress={p} delay={0.04} span={0.54} width={4} />
    <DrawRing cx={x} cy={897} r={61} progress={p} delay={0.43} span={0.32} />
    <DrawDot x={x} y={897} radius={15} progress={p} delay={0.56} pulse />
    {[-1, 0, 1].map((n, i) => <DrawArrow key={n}
      from={{x:240 + i * 300,y:515}}
      to={{x:x + n * 155,y:690}}
      progress={p} delay={0.15 + i * 0.09} span={0.40}
      stroke={MUTED} width={2.4} opacity={0.8} />)}
    <DrawLabel x={x} y={1278} text={item(visual, 0)}
      progress={p} delay={0.67} size={27} />
  </g>;
};

const Funnel: React.FC<SceneProps> = ({visual, p}) => {
  const xs = [320, 540, 760];
  const topY = variant(visual) % 2 ? 720 : 650;
  return <g>
    {xs.map((x, i) => <g key={i}>
      <DrawRing cx={x} cy={topY} r={38}
        progress={p} delay={0.05 + i * 0.11} span={0.31} />
      <DrawDot x={x} y={topY} radius={7} progress={p}
        delay={0.19 + i * 0.11} />
      <DrawPath d={`M ${x} ${topY + 40} Q ${x} 975 540 1061`}
        progress={p} delay={0.26 + i * 0.10} span={0.40}
        stroke={MUTED} width={2.6} />
      <DrawLabel x={x} y={topY - 77} text={item(visual, i)}
        progress={p} delay={0.19 + i * 0.12} size={23} color={MUTED} />
    </g>)}
    <DrawRing cx={540} cy={1120} r={65}
      progress={p} delay={0.66} span={0.27} width={3.8} />
    <DrawDot x={540} y={1120} radius={19}
      progress={p} delay={0.75} pulse />
    <DrawLabel x={540} y={1250} text={item(visual, 3)}
      progress={p} delay={0.78} size={28} />
  </g>;
};

const Mesh: React.FC<SceneProps> = ({visual, p}) => {
  const pts = [
    {x:340,y:730}, {x:705,y:765}, {x:260,y:998},
    {x:520,y:950}, {x:800,y:1040}, {x:470,y:1210},
  ];
  const edges = [[0,2],[0,3],[1,3],[1,4],[2,3],[3,4],[3,5],[4,5]];
  return <g>
    {edges.map(([a,b],i) => <DrawPath key={i}
      d={`M ${pts[a].x} ${pts[a].y} L ${pts[b].x} ${pts[b].y}`}
      progress={p} delay={0.12 + i * 0.052} span={0.35}
      stroke={i===3?INK:FAINT} width={i===3?3.4:2.5} />)}
    {pts.map((point,i) => <DrawDot key={i}
      x={point.x} y={point.y} radius={i === (visual.focus ?? 3) ? 20 : 12}
      hollow={i !== (visual.focus ?? 3)}
      progress={p} delay={0.18 + i * 0.09}
      pulse={i === (visual.focus ?? 3)} />)}
    <DrawLabel x={520} y={1320} text={item(visual,0)}
      progress={p} delay={0.64} size={27} />
  </g>;
};

const components = {
  branch: Branch,
  orbit: Orbit,
  flow: Flow,
  growth: Growth,
  stack: Stack,
  comparison: Comparison,
  timeline: Timeline,
  wave: Wave,
  shield: Shield,
  funnel: Funnel,
  mesh: Mesh,
};

/**
 * This is intentionally independent from legacy ExplainVisual. Phase 2 installs
 * the new diagram grammar without abruptly changing existing production edits.
 * Phase 3 will connect scenes/morph shared anchors. Phase 4 will make the
 * selection algorithm prefer diagrams over generic text.
 */
export const DrawnDiagram: React.FC<{visual: DrawnDiagramVisual}> = ({visual}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const rawP = clamp01(frame / Math.max(1, durationInFrames - 1));
  // Continuity scenes start near zero and keep drawing underneath the bridge.
  // The bridge fades away gradually, revealing the incoming geometry while it
  // is still being drawn instead of exposing a nearly-complete diagram at once.
  const p = visual.continuityIn ? clamp01(rawP * 1.45) : rawP;
  const Content = components[visual.kind];
  return <DiagramCanvas progress={p}>
    <Content visual={visual} p={p} />
  </DiagramCanvas>;
};
