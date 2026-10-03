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
import {Beat} from '../types';

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
          <div style={{fontSize: 86, fontWeight: 950, letterSpacing: -5}}>SOURCE</div>
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
            transform: `scale(${1 + progress * 0.035})`
          }}
        />
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'metric') {
    return (
      <AbsoluteFill style={shell}>
        <div
          style={{
            fontSize: beat.visual.value.length > 7 ? 170 : 260,
            lineHeight: 0.82,
            fontWeight: 950,
            letterSpacing: -14,
            transform: `scale(${scale})`,
            textAlign: 'center'
          }}
        >
          {beat.visual.value}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'diagram') {
    const symbols = beat.visual.symbols;
    return (
      <AbsoluteFill style={shell}>
        <div style={{display: 'flex', alignItems: 'center', gap: 26}}>
          {symbols.map((symbol, index) => (
            <React.Fragment key={`${symbol}-${index}`}>
              <div
                style={{
                  width: 210,
                  height: 210,
                  border: '3px solid rgba(255,255,255,0.78)',
                  borderRadius: 32,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: symbol.length > 5 ? 48 : 76,
                  fontWeight: 950,
                  transform: `scale(${0.9 + enter * 0.1})`
                }}
              >
                {symbol}
              </div>
              {index < symbols.length - 1 ? (
                <div style={{fontSize: 84, fontWeight: 900}}>→</div>
              ) : null}
            </React.Fragment>
          ))}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'comparison') {
    return (
      <AbsoluteFill style={shell}>
        <div style={{display: 'flex', alignItems: 'center', gap: 38}}>
          {[beat.visual.left, beat.visual.right].map((value, index) => (
            <React.Fragment key={value}>
              <div
                style={{
                  width: 360,
                  height: 360,
                  border: '3px solid rgba(255,255,255,0.78)',
                  borderRadius: 38,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: value.length > 8 ? 48 : 72,
                  fontWeight: 950,
                  textAlign: 'center',
                  padding: 28,
                  boxSizing: 'border-box',
                  transform: `translateY(${index === 0 ? -1 : 1} * ${(1 - enter) * 24}px)`
                }}
              >
                {value}
              </div>
              {index === 0 ? <div style={{fontSize: 90, fontWeight: 900}}>→</div> : null}
            </React.Fragment>
          ))}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'symbol') {
    return (
      <AbsoluteFill style={shell}>
        <div
          style={{
            fontSize: beat.visual.symbol.length > 4 ? 180 : 270,
            lineHeight: 0.9,
            fontWeight: 950,
            transform: `scale(${scale})`
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
          fontSize: 116,
          lineHeight: 0.9,
          fontWeight: 950,
          letterSpacing: -7,
          maxWidth: 900,
          textAlign: 'center',
          transform: `scale(${scale})`
        }}
      >
        {beat.visual.text}
      </div>
    </AbsoluteFill>
  );
};
