import React from 'react';
import {AbsoluteFill} from 'remotion';
import {CANVAS} from './Primitives';

export const DIAGRAM_BASE_ZOOM = 1.1;

type CanvasProps = {
  children: React.ReactNode;
  progress: number;
  panX?: number;
  panY?: number;
  zoom?: number;
};

/** 1080x1920 coordinate system shared by every new diagram family. */
export const DiagramCanvas: React.FC<CanvasProps> = ({
  children, progress, panX = 0, panY = 0, zoom = DIAGRAM_BASE_ZOOM,
}) => {
  const shiftX = panX * Math.min(1, progress);
  const shiftY = panY * Math.min(1, progress);
  const scale = zoom + Math.min(1, progress) * 0.007;
  return (
    <AbsoluteFill style={{background: CANVAS, overflow: 'hidden'}}>
      <svg
        viewBox="0 0 1080 1920"
        width="100%"
        height="100%"
        preserveAspectRatio="xMidYMid meet"
        aria-label="Animated Orbdev line diagram"
        style={{display: 'block', overflow: 'hidden'}}
      >
        <g transform={`translate(540 940) scale(${scale}) translate(-540 -940) translate(${shiftX} ${shiftY})`}>
          {children}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
