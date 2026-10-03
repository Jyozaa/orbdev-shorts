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
import {ExplainVisual} from './ExplainVisual';

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

  if (beat.visual.type === 'explain') {
    return <ExplainVisual visual={beat.visual} />;
  }

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
            width: beat.visual.fit === 'cover' ? 1080 : 980,
            height: beat.visual.fit === 'cover' ? 1500 : 1280,
            objectFit: beat.visual.fit ?? 'contain',
            objectPosition: 'center',
            transform: `translateX(${(1 - enter) * 42}px) translateY(${progress * -18}px) scale(${0.98 + progress * 0.06})`,
            opacity: enter
          }}
        />
        {(beat.visual.annotations ?? []).map((annotation, index) => {
          const reveal = spring({frame, fps, delay: 7 + index * 5, config: {damping: 18, stiffness: 180}});
          return (
            <React.Fragment key={`annotation-${index}`}>
              <div style={{
                position: 'absolute',
                left: `${annotation.x}%`,
                top: `${annotation.y}%`,
                width: 18,
                height: 18,
                borderRadius: '50%',
                background: '#ffffff',
                transform: `translate(-50%,-50%) scale(${reveal})`,
                boxShadow: '0 0 0 8px rgba(255,255,255,.15)'
              }} />
              <div style={{
                position: 'absolute',
                left: `calc(${annotation.x}% + 18px)`,
                top: `calc(${annotation.y}% - 42px)`,
                padding: '10px 14px',
                background: 'rgba(0,0,0,.76)',
                fontSize: 28,
                fontWeight: 900,
                opacity: reveal,
                transform: `translateY(${(1-reveal)*12}px)`
              }}>{annotation.label}</div>
            </React.Fragment>
          );
        })}
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


  if (beat.visual.type === 'chart') {
    const bars = beat.visual.bars;
    const maxBarHeight = 520;
    return (
      <AbsoluteFill style={shell}>
        <div
          style={{
            width: 900,
            height: 720,
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'center',
            gap: 42,
            paddingBottom: 80,
            boxSizing: 'border-box',
            borderBottom: '3px solid rgba(255,255,255,0.32)'
          }}
        >
          {bars.map((bar, index) => {
            const reveal = spring({
              frame,
              fps,
              delay: index * 5,
              config: {damping: 18, stiffness: 170, mass: 0.65}
            });
            const height = Math.max(34, (Math.max(0, Math.min(100, bar.amount)) / 100) * maxBarHeight * reveal);
            return (
              <div
                key={`${bar.label}-${index}`}
                style={{
                  width: Math.max(120, Math.floor(700 / Math.max(1, bars.length))),
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  height: 620
                }}
              >
                <div
                  style={{
                    marginBottom: 14,
                    fontSize: 36,
                    fontWeight: 950,
                    opacity: reveal
                  }}
                >
                  {bar.value}
                </div>
                <div
                  style={{
                    width: '100%',
                    height,
                    minHeight: 34,
                    background: '#ffffff',
                    borderRadius: '22px 22px 6px 6px',
                    transformOrigin: 'bottom center'
                  }}
                />
                <div
                  style={{
                    marginTop: 18,
                    fontSize: fittedFontSize(bar.label, 180, 30, 18),
                    fontWeight: 850,
                    textAlign: 'center',
                    whiteSpace: 'nowrap',
                    opacity: reveal
                  }}
                >
                  {bar.label}
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'timeline') {
    const points = beat.visual.points;
    return (
      <AbsoluteFill style={shell}>
        <div style={{width: 900, height: 460, position: 'relative'}}>
          <div
            style={{
              position: 'absolute',
              left: 40,
              right: 40,
              top: 214,
              height: 6,
              background: 'rgba(255,255,255,0.22)',
              borderRadius: 999
            }}
          />
          <div
            style={{
              position: 'absolute',
              left: 40,
              top: 214,
              height: 6,
              width: `${Math.max(0, Math.min(100, progress * 115))}%`,
              maxWidth: 820,
              background: '#ffffff',
              borderRadius: 999,
              transformOrigin: 'left center'
            }}
          />
          {points.map((point, index) => {
            const reveal = spring({
              frame,
              fps,
              delay: index * 5,
              config: {damping: 18, stiffness: 175}
            });
            const left = 40 + (Math.max(0, Math.min(100, point.position)) / 100) * 820;
            const above = index % 2 === 0;
            return (
              <div
                key={`${point.label}-${index}`}
                style={{
                  position: 'absolute',
                  left,
                  top: 217,
                  transform: `translate(-50%, -50%) scale(${0.7 + reveal * 0.3})`,
                  opacity: reveal
                }}
              >
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: '50%',
                    background: '#ffffff',
                    boxShadow: '0 0 0 10px rgba(255,255,255,0.08)'
                  }}
                />
                <div
                  style={{
                    position: 'absolute',
                    width: 190,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    top: above ? -86 : 58,
                    fontSize: fittedFontSize(point.label, 170, 30, 18),
                    fontWeight: 900,
                    textAlign: 'center'
                  }}
                >
                  {point.label}
                </div>
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'network') {
    const nodes = beat.visual.nodes.slice(0, 6);
    const radius = 300;
    return (
      <AbsoluteFill style={shell}>
        <div style={{position: 'relative', width: 820, height: 820}}>
          {nodes.map((node, index) => {
            const angle = (-Math.PI / 2) + (Math.PI * 2 * index) / Math.max(1, nodes.length);
            const x = 410 + Math.cos(angle) * radius;
            const y = 410 + Math.sin(angle) * radius;
            const reveal = spring({
              frame,
              fps,
              delay: 6 + index * 4,
              config: {damping: 17, stiffness: 180}
            });
            const dx = x - 410;
            const dy = y - 410;
            const length = Math.sqrt(dx * dx + dy * dy);
            const angleDeg = (Math.atan2(dy, dx) * 180) / Math.PI;
            return (
              <React.Fragment key={`${node}-${index}`}>
                <div
                  style={{
                    position: 'absolute',
                    left: 410,
                    top: 410,
                    width: length * reveal,
                    height: 4,
                    background: 'rgba(255,255,255,0.72)',
                    transformOrigin: 'left center',
                    transform: `rotate(${angleDeg}deg)`
                  }}
                />
                <div
                  style={{
                    position: 'absolute',
                    left: x,
                    top: y,
                    width: 170,
                    height: 170,
                    marginLeft: -85,
                    marginTop: -85,
                    borderRadius: '50%',
                    border: '3px solid rgba(255,255,255,0.72)',
                    background: '#000000',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 18,
                    boxSizing: 'border-box',
                    fontSize: fittedFontSize(node, 136, 46, 24),
                    fontWeight: 950,
                    textAlign: 'center',
                    opacity: reveal,
                    transform: `scale(${0.72 + reveal * 0.28})`
                  }}
                >
                  {node}
                </div>
              </React.Fragment>
            );
          })}
          <div
            style={{
              position: 'absolute',
              left: 410,
              top: 410,
              width: 230,
              height: 230,
              marginLeft: -115,
              marginTop: -115,
              borderRadius: '50%',
              background: '#ffffff',
              color: '#000000',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 24,
              boxSizing: 'border-box',
              fontSize: fittedFontSize(beat.visual.center, 180, 52, 28),
              fontWeight: 950,
              textAlign: 'center',
              transform: `scale(${0.72 + enter * 0.28})`
            }}
          >
            {beat.visual.center}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'kinetic') {
    const words = beat.visual.text.trim().split(/\s+/).slice(0, 6);
    const emphasis = (beat.visual.emphasis ?? words[words.length - 1] ?? '').toLowerCase();
    return (
      <AbsoluteFill style={shell}>
        <div style={{width: 960, minHeight: 760, display: 'flex', flexWrap: 'wrap', alignContent: 'center', justifyContent: 'center', gap: '14px 22px', transform: `scale(${0.94 + progress * 0.06}) translateY(${-18 * progress}px)`}}>
          {words.map((word, index) => {
            const reveal = spring({frame, fps, delay: index * 3, config: {damping: 17, stiffness: 210, mass: 0.48}});
            const clean = word.replace(/[^A-Za-z0-9'’.-]/g, '').toLowerCase();
            const target = emphasis.replace(/[^a-z0-9'’.-]/g, '');
            const isEmphasis = clean === target;
            return (
              <div key={`${word}-${index}`} style={{fontSize: isEmphasis ? 132 : 82, lineHeight: 0.88, fontWeight: 950, letterSpacing: isEmphasis ? -7 : -4, textTransform: 'uppercase', opacity: reveal, transform: `translateY(${(1 - reveal) * (index % 2 === 0 ? 50 : -45)}px) scale(${0.82 + reveal * 0.18}) rotate(${(1 - reveal) * (index % 2 === 0 ? -4 : 4)}deg)`, borderBottom: isEmphasis ? '8px solid #ffffff' : undefined, paddingBottom: isEmphasis ? 8 : 0}}>
                {word}
              </div>
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
