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

const fittedFontSize = (value: string, boxWidth: number, max: number, min: number) => {
  const normalized = Math.max(1, value.trim().length);
  const estimated = Math.floor((boxWidth * 1.45) / normalized);
  return Math.max(min, Math.min(max, estimated));
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
              maxWidth: 900
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
            transform: `scale(${1 + progress * 0.035})`
          }}
        />
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'metric') {
    const fontSize = fittedFontSize(beat.visual.value, 860, 260, 132);
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
            transform: `scale(${scale})`,
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
    const arrowWidth = count > 1 ? 58 * (count - 1) : 0;
    const gapWidth = 20 * (count * 2 - 2);
    const nodeWidth = Math.max(150, Math.min(230, Math.floor((920 - arrowWidth - gapWidth) / count)));

    return (
      <AbsoluteFill style={shell}>
        <div
          style={{
            width: 940,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 20
          }}
        >
          {symbols.map((symbol, index) => {
            const fontSize = fittedFontSize(symbol, nodeWidth - 34, 72, 34);
            return (
              <React.Fragment key={`${symbol}-${index}`}>
                <div
                  style={{
                    width: nodeWidth,
                    minWidth: nodeWidth,
                    height: 200,
                    border: '3px solid rgba(255,255,255,0.78)',
                    borderRadius: 30,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '18px 14px',
                    boxSizing: 'border-box',
                    overflow: 'hidden',
                    fontSize,
                    lineHeight: 0.95,
                    fontWeight: 950,
                    textAlign: 'center',
                    whiteSpace: 'nowrap',
                    transform: `scale(${0.9 + enter * 0.1})`
                  }}
                >
                  {symbol}
                </div>
                {index < symbols.length - 1 ? (
                  <div
                    style={{
                      width: 58,
                      minWidth: 58,
                      textAlign: 'center',
                      fontSize: 66,
                      lineHeight: 1,
                      fontWeight: 900
                    }}
                  >
                    →
                  </div>
                ) : null}
              </React.Fragment>
            );
          })}
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
            const y = (index === 0 ? -1 : 1) * (1 - enter) * 24;
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
                    transform: `translateY(${y}px)`
                  }}
                >
                  {value}
                </div>
                {index === 0 ? <div style={{fontSize: 82, fontWeight: 900}}>→</div> : null}
              </React.Fragment>
            );
          })}
        </div>
      </AbsoluteFill>
    );
  }

  if (beat.visual.type === 'symbol') {
    const fontSize = fittedFontSize(beat.visual.symbol, 840, 270, 100);
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
            transform: `scale(${scale})`,
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
          transform: `scale(${scale})`
        }}
      >
        {beat.visual.text}
      </div>
    </AbsoluteFill>
  );
};
