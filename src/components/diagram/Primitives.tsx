import React from 'react';

/**
 * Deterministic SVG drawing primitives for Remotion.
 * Frame-based only: no CSS keyframe timelines, random values, network requests,
 * external LLMs, SVG morph packages, or rasterised motion templates.
 */
export const INK = '#f4f4f3';
export const MUTED = '#777777';
export const FAINT = '#343434';
export const CANVAS = '#050505';
export const STROKE = 3.2;

export const clamp01 = (n: number): number =>
  Math.max(0, Math.min(1, Number.isFinite(n) ? n : 0));

export const ease = (n: number): number => {
  const t = clamp01(n);
  return 1 - Math.pow(1 - t, 3);
};

/** Reveal position on the whole scene's normalized [0,1] timeline. */
export const drawAt = (p: number, delay = 0, span = 0.52): number =>
  ease((clamp01(p) - delay) / Math.max(0.001, span));

type Timed = {progress: number; delay?: number; span?: number};

export type Point = {x: number; y: number};

type PathProps = Timed & {
  d: string;
  stroke?: string;
  width?: number;
  opacity?: number;
  dash?: string;
};

/** SVG pathLength=100 makes draw-on timing independent of path geometry. */
export const DrawPath: React.FC<PathProps> = ({
  d, progress, delay = 0, span = 0.52, stroke = INK,
  width = STROKE, opacity = 1, dash,
}) => {
  const v = drawAt(progress, delay, span);
  return (
    <path
      d={d}
      pathLength={100}
      fill="none"
      stroke={stroke}
      strokeWidth={width}
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray={dash || '100'}
      strokeDashoffset={dash ? 0 : 100 * (1 - v)}
      opacity={opacity * v}
    />
  );
};

type RingProps = Timed & {
  cx: number; cy: number; r: number; stroke?: string; width?: number;
  opacity?: number; startAngle?: number;
};

export const DrawRing: React.FC<RingProps> = ({
  cx, cy, r, progress, delay = 0, span = 0.55,
  stroke = INK, width = STROKE, opacity = 1, startAngle = -90,
}) => {
  const v = drawAt(progress, delay, span);
  return (
    <circle
      cx={cx} cy={cy} r={r}
      pathLength={100}
      fill="none"
      stroke={stroke}
      strokeWidth={width}
      strokeDasharray="100"
      strokeDashoffset={100 * (1 - v)}
      strokeLinecap="round"
      opacity={opacity * v}
      transform={`rotate(${startAngle} ${cx} ${cy})`}
    />
  );
};

type RectProps = Timed & {
  x: number; y: number; width: number; height: number;
  radius?: number; stroke?: string; weight?: number; opacity?: number;
};

export const DrawRect: React.FC<RectProps> = ({
  x, y, width, height, progress, delay = 0, span = 0.46,
  radius = 22, stroke = INK, weight = STROKE, opacity = 1,
}) => {
  const v = drawAt(progress, delay, span);
  return (
    <rect
      x={x} y={y} width={width} height={height} rx={radius}
      fill="none"
      pathLength={100}
      stroke={stroke}
      strokeWidth={weight}
      strokeDasharray="100"
      strokeDashoffset={100 * (1 - v)}
      strokeLinecap="round"
      opacity={opacity * v}
    />
  );
};

type DotProps = Timed & {
  x: number; y: number; radius?: number; color?: string;
  hollow?: boolean; pulse?: boolean; opacity?: number;
};

export const DrawDot: React.FC<DotProps> = ({
  x, y, radius = 11, progress, delay = 0, span = 0.22,
  color = INK, hollow = false, pulse = false, opacity = 1,
}) => {
  const v = drawAt(progress, delay, span);
  const breathing = pulse ? 1 + 0.055 * Math.sin(progress * 12) : 1;
  const scale = (0.65 + 0.35 * v) * breathing;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`} opacity={v * opacity}>
      <circle cx={0} cy={0} r={radius}
        fill={hollow ? CANVAS : color}
        stroke={color} strokeWidth={hollow ? STROKE : 0}
      />
    </g>
  );
};

type LabelProps = Timed & {
  x: number; y: number; text?: string;
  size?: number; color?: string;
  anchor?: 'start' | 'middle' | 'end'; opacity?: number;
};

/** Tiny editorial annotation, never a narration transcription. */
export const DrawLabel: React.FC<LabelProps> = ({
  x, y, text, progress, delay = 0, span = 0.28,
  size = 26, color = INK, anchor = 'middle', opacity = 1,
}) => {
  if (!text) return null;
  const v = drawAt(progress, delay, span);
  return (
    <text
      x={x} y={y - (1 - v) * 11}
      textAnchor={anchor}
      fill={color}
      opacity={v * opacity}
      fontFamily="Arial, Helvetica, sans-serif"
      fontSize={size}
      fontWeight={500}
      letterSpacing={0.15}
    >
      {text}
    </text>
  );
};

type ArrowProps = Timed & {
  from: Point; to: Point;
  stroke?: string; width?: number; opacity?: number; head?: number;
  curve?: number;
};

export const DrawArrow: React.FC<ArrowProps> = ({
  from, to, progress, delay = 0, span = 0.48,
  stroke = INK, width = STROKE, opacity = 1,
  head = 13, curve = 0,
}) => {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const theta = Math.atan2(dy, dx);
  const offx = Math.cos(theta);
  const offy = Math.sin(theta);
  const tip = {x: to.x - offx * 4, y: to.y - offy * 4};
  const center = {
    x: (from.x + tip.x) / 2 - offy * curve,
    y: (from.y + tip.y) / 2 + offx * curve,
  };
  const left = {
    x: tip.x - Math.cos(theta - Math.PI / 5) * head,
    y: tip.y - Math.sin(theta - Math.PI / 5) * head,
  };
  const right = {
    x: tip.x - Math.cos(theta + Math.PI / 5) * head,
    y: tip.y - Math.sin(theta + Math.PI / 5) * head,
  };
  const d = `M ${from.x} ${from.y} Q ${center.x} ${center.y} ${tip.x} ${tip.y}`;
  return (
    <g>
      <DrawPath d={d} progress={progress} delay={delay} span={span}
        stroke={stroke} width={width} opacity={opacity} />
      <DrawPath
        d={`M ${left.x} ${left.y} L ${tip.x} ${tip.y} L ${right.x} ${right.y}`}
        progress={progress}
        delay={delay + span * 0.8}
        span={span * 0.25}
        stroke={stroke} width={width} opacity={opacity}
      />
    </g>
  );
};

export const makeWave = (
  x: number, y: number, width: number, amplitude: number, cycles: number,
  count = 68,
): string => Array.from({length: count + 1}, (_, i) => {
  const t = i / count;
  const px = x + t * width;
  const py = y + Math.sin(t * Math.PI * 2 * cycles) * amplitude;
  return `${i === 0 ? 'M' : 'L'} ${px.toFixed(2)} ${py.toFixed(2)}`;
}).join(' ');
