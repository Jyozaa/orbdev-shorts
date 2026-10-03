import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig
} from 'remotion';
import {Beat, FlowNode} from '../types';

const fittedFontSize = (value: string, boxWidth: number, max: number, min: number) => {
  const normalized = Math.max(1, value.trim().length);
  const estimated = Math.floor((boxWidth * 1.45) / normalized);
  return Math.max(min, Math.min(max, estimated));
};

const AnimatedConnector: React.FC<{index: number; frame: number; fps: number}> = ({
  index,
  frame,
  fps
}) => {
  const reveal = spring({
    frame,
    fps,
    delay: 5 + index * 5,
    config: {damping: 18, stiffness: 180, mass: 0.5}
  });
  return (
    <div
      style={{
        width: 64,
        minWidth: 64,
        height: 56,
        position: 'relative',
        display: 'flex',
        alignItems: 'center'
      }}
    >
      <div
        style={{
          height: 4,
          width: 44,
          background: '#ffffff',
          transformOrigin: 'left center',
          transform: `scaleX(${reveal})`,
          opacity: 0.88
        }}
      />
      <div
        style={{
          position: 'absolute',
          right: 0,
          fontSize: 44,
          fontWeight: 900,
          opacity: reveal,
          transform: `translateX(${(1 - reveal) * -12}px)`
        }}
      >
        ›
      </div>
    </div>
  );
};

const LogoNode: React.FC<{
  src?: string;
  label?: string;
  width: number;
  index: number;
  frame: number;
  fps: number;
}> = ({src, label, width, index, frame, fps}) => {
  const reveal = spring({
    frame,
    fps,
    delay: index * 5,
    config: {damping: 17, stiffness: 180, mass: 0.58}
  });
  const spin = interpolate(reveal, [0, 1], [-8, 0]);
  const y = interpolate(reveal, [0, 1], [26, 0]);

  return (
    <div
      style={{
        width,
        minWidth: width,
        height: 220,
        border: '3px solid rgba(255,255,255,0.72)',
        borderRadius: 34,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
        boxSizing: 'border-box',
        overflow: 'hidden',
        transform: `translateY(${y}px) scale(${0.84 + reveal * 0.16}) rotate(${spin}deg)`,
        opacity: reveal
      }}
    >
      {src ? (
        <Img
          src={staticFile(src)}
          style={{
            width: 110,
            height: 110,
            objectFit: 'contain',
            filter: 'brightness(0) invert(1)'
          }}
        />
      ) : (
        <div style={{fontSize: 54, fontWeight: 950}}>◎</div>
      )}
      {label ? (
        <div
          style={{
            marginTop: 14,
            fontSize: fittedFontSize(label, width - 30, 28, 18),
            fontWeight: 850,
            textAlign: 'center',
            whiteSpace: 'nowrap'
          }}
        >
          {label}
        </div>
      ) : null}
    </div>
  );
};

const FlowNodeView: React.FC<{
  node: FlowNode;
  width: number;
  index: number;
  frame: number;
  fps: number;
}> = ({node, width, index, frame, fps}) => {
  if (node.kind === 'logo') {
    return (
      <LogoNode
        src={node.src}
        label={node.label}
        width={width}
        index={index}
        frame={frame}
        fps={fps}
      />
    );
  }

  const value = node.value;
  const reveal = spring({
    frame,
    fps,
    delay: index * 5,
    config: {damping: 17, stiffness: 185, mass: 0.58}
  });
  const fontSize = fittedFontSize(value, width - 34, node.kind === 'symbol' ? 76 : 52, 28);
  return (
    <div
      style={{
        width,
        minWidth: width,
        height: 220,
        border: '3px solid rgba(255,255,255,0.72)',
        borderRadius: 34,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
        boxSizing: 'border-box',
        overflow: 'hidden',
        fontSize,
        lineHeight: 0.95,
        fontWeight: 950,
        textAlign: 'center',
        whiteSpace: 'nowrap',
        opacity: reveal,
        transform: `translateY(${(1 - reveal) * 30}px) scale(${0.84 + reveal * 0.16})`
      }}
    >
      {value}
    </div>
  );
};

export const BeatVisual: React.FC<{beat: Beat}> = ({beat}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const enter = spring({
    frame,
    fps,
    config: {damping: 20, stiffness: 190, mass: 0.55}
  });
  const progress = interpolate(
    frame,
    [0, Math.max(1, durationInFrames - 1)],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );
  const opacity = interpolate(frame, [0, 3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });
  const scale = 0.96 + enter * 0.04;

  const shell: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    background: '#000000',
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: 'Arial, Helvetica, sans-serif',
    overflow: 'hidden',
    opacity
  };

  if (beat.visual.type === 'source') {
    if (!beat.visual.src) {
      return (
        <AbsoluteFill style={shell}>
          <div
            style={{
              fontSize: 128,
              fontWeight: 950,
              letterSpacing: -8,
              textTransform: 'uppercase',
              textAlign: 'center',
              maxWidth: 900,
              transform: `scale(${0.88 + enter * 0.12})`
            }}
          >
            {beat.visual.publisher ?? 'SOURCE'}
          </div>
        </AbsoluteFill>
      );
    }

    return (
      <AbsoluteFill style={shell}>
        <Img
          src={staticFile(beat.visual.src)}
          style={{
            width: 980,
            height: 1280,
            objectFit: 'contain',
            transform: `translateX(${(1 - enter) * 50}px) scale(${0.98 + progress * 0.055})`,
            opacity: enter
          }}
        />
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'logo') {
    const bob = Math.sin((frame / fps) * Math.PI * 2 * 0.8) * 8;
    const ring = interpolate(progress, [0, 0.55, 1], [0.7, 1.04, 1.18]);
    return (
      <AbsoluteFill style={shell}>
        <div
          style={{
            position: 'absolute',
            width: 420,
            height: 420,
            borderRadius: '50%',
            border: '3px solid rgba(255,255,255,0.16)',
            transform: `scale(${ring})`,
            opacity: 0.7 - progress * 0.35
          }}
        />
        <div
          style={{
            width: 360,
            height: 360,
            borderRadius: 56,
            border: '3px solid rgba(255,255,255,0.72)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `translateY(${bob}px) scale(${0.72 + enter * 0.28}) rotate(${(1 - enter) * -9}deg)`
          }}
        >
          {beat.visual.src ? (
            <Img
              src={staticFile(beat.visual.src)}
              style={{
                width: 190,
                height: 190,
                objectFit: 'contain',
                filter: 'brightness(0) invert(1)'
              }}
            />
          ) : (
            <div style={{fontSize: 110, fontWeight: 950}}>◎</div>
          )}
          {beat.visual.label ? (
            <div
              style={{
                marginTop: 20,
                fontSize: fittedFontSize(beat.visual.label, 300, 38, 22),
                fontWeight: 900,
                textAlign: 'center'
              }}
            >
              {beat.visual.label}
            </div>
          ) : null}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'flow') {
    const nodes = beat.visual.nodes;
    const count = Math.max(1, nodes.length);
    const connectorWidth = count > 1 ? 64 * (count - 1) : 0;
    const gapWidth = 18 * (count * 2 - 2);
    const nodeWidth = Math.max(150, Math.min(230, Math.floor((940 - connectorWidth - gapWidth) / count)));

    return (
      <AbsoluteFill style={shell}>
        <div
          style={{
            width: 960,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18
          }}
        >
          {nodes.map((node, index) => (
            <React.Fragment key={`flow-${index}`}>
              <FlowNodeView
                node={node}
                width={nodeWidth}
                index={index}
                frame={frame}
                fps={fps}
              />
              {index < nodes.length - 1 ? (
                <AnimatedConnector index={index} frame={frame} fps={fps} />
              ) : null}
            </React.Fragment>
          ))}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'metric') {
    const fontSize = fittedFontSize(beat.visual.value, 860, 260, 132);
    const pulse = 1 + Math.sin((frame / fps) * Math.PI * 2 * 1.6) * 0.012;
    return (
      <AbsoluteFill style={shell}>
        <div
          style={{
            maxWidth: 900,
            padding: '0 32px',
            boxSizing: 'border-box',
            fontSize,
            lineHeight: 0.86,
            fontWeight: 950,
            letterSpacing: -10,
            transform: `scale(${scale * pulse})`,
            textAlign: 'center',
            whiteSpace: 'nowrap'
          }}
        >
          {beat.visual.value}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'diagram') {
    const symbols = beat.visual.symbols.filter(
      (symbol) => !['→', '->', '=>', '←', '<-', '↔'].includes(symbol.trim())
    );
    const count = Math.max(1, symbols.length);
    const connectorWidth = count > 1 ? 64 * (count - 1) : 0;
    const gapWidth = 18 * (count * 2 - 2);
    const nodeWidth = Math.max(150, Math.min(230, Math.floor((940 - connectorWidth - gapWidth) / count)));

    return (
      <AbsoluteFill style={shell}>
        <div
          style={{
            width: 960,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 18
          }}
        >
          {symbols.map((symbol, index) => (
            <React.Fragment key={`${symbol}-${index}`}>
              <FlowNodeView
                node={{kind: 'symbol', value: symbol}}
                width={nodeWidth}
                index={index}
                frame={frame}
                fps={fps}
              />
              {index < symbols.length - 1 ? (
                <AnimatedConnector index={index} frame={frame} fps={fps} />
              ) : null}
            </React.Fragment>
          ))}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'comparison') {
    const values = [beat.visual.left, beat.visual.right];
    return (
      <AbsoluteFill style={shell}>
        <div style={{width: 940, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 28}}>
          {values.map((value, index) => {
            const boxWidth = 370;
            const fontSize = fittedFontSize(value, boxWidth - 56, 70, 34);
            const reveal = spring({
              frame,
              fps,
              delay: index * 4,
              config: {damping: 18, stiffness: 180}
            });
            const x = (index === 0 ? -1 : 1) * (1 - reveal) * 90;
            return (
              <React.Fragment key={`${value}-${index}`}>
                <div
                  style={{
                    width: boxWidth,
                    height: 330,
                    border: '3px solid rgba(255,255,255,0.78)',
                    borderRadius: 36,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize,
                    fontWeight: 950,
                    textAlign: 'center',
                    padding: 28,
                    boxSizing: 'border-box',
                    overflow: 'hidden',
                    whiteSpace: 'nowrap',
                    opacity: reveal,
                    transform: `translateX(${x}px) scale(${0.9 + reveal * 0.1})`
                  }}
                >
                  {value}
                </div>
                {index === 0 ? <AnimatedConnector index={0} frame={frame} fps={fps} /> : null}
              </React.Fragment>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'symbol') {
    const fontSize = fittedFontSize(beat.visual.symbol, 840, 270, 100);
    const rotate = interpolate(enter, [0, 1], [-7, 0]);
    return (
      <AbsoluteFill style={shell}>
        <div
          style={{
            maxWidth: 880,
            padding: '0 24px',
            boxSizing: 'border-box',
            fontSize,
            lineHeight: 0.9,
            fontWeight: 950,
            textAlign: 'center',
            transform: `scale(${scale}) rotate(${rotate}deg)`,
            whiteSpace: 'nowrap'
          }}
        >
          {beat.visual.symbol}
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={shell}>
      <div
        style={{
          fontSize: fittedFontSize(beat.visual.text, 820, 116, 58),
          lineHeight: 0.9,
          fontWeight: 950,
          letterSpacing: -5,
          maxWidth: 880,
          padding: '0 24px',
          boxSizing: 'border-box',
          textAlign: 'center',
          transform: `translateY(${(1 - enter) * 34}px) scale(${scale})`,
          opacity: enter
        }}
      >
        {beat.visual.text}
      </div>
    </AbsoluteFill>
  );
};
