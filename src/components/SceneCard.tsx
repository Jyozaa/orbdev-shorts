import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Scene} from '../types';

type Props = {
  scene: Scene;
};

const cardStyle: React.CSSProperties = {
  border: '1px solid rgba(255,255,255,0.13)',
  background: 'rgba(255,255,255,0.055)',
  borderRadius: 34,
  padding: '36px 34px',
  minHeight: 230,
  boxShadow: '0 28px 80px rgba(0,0,0,0.23)'
};

export const SceneCard: React.FC<Props> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 105}});
  const opacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });
  const y = interpolate(enter, [0, 1], [42, 0]);

  const shell: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    padding: '240px 82px 360px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: scene.type === 'hook' ? 'center' : 'flex-start',
    opacity,
    transform: `translateY(${y}px)`,
    fontFamily: 'Arial, Helvetica, sans-serif'
  };

  const kicker = scene.kicker ? (
    <div
      style={{
        color: '#9dbef8',
        fontSize: 30,
        fontWeight: 800,
        letterSpacing: 5,
        marginBottom: 28
      }}
    >
      {scene.kicker.toUpperCase()}
    </div>
  ) : null;

  if (scene.type === 'comparison') {
    return (
      <div style={shell}>
        {kicker}
        <div style={{fontSize: 74, fontWeight: 900, letterSpacing: -4, marginBottom: 52}}>
          {scene.title}
        </div>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 26}}>
          <div style={cardStyle}>
            <div style={{fontSize: 28, opacity: 0.58, marginBottom: 24}}>{scene.leftTitle ?? 'BEFORE'}</div>
            <div style={{fontSize: 43, fontWeight: 800, lineHeight: 1.08}}>{scene.leftBody}</div>
          </div>
          <div style={{...cardStyle, borderColor: 'rgba(157,190,248,0.45)'}}>
            <div style={{fontSize: 28, color: '#9dbef8', marginBottom: 24}}>{scene.rightTitle ?? 'NOW'}</div>
            <div style={{fontSize: 43, fontWeight: 800, lineHeight: 1.08}}>{scene.rightBody}</div>
          </div>
        </div>
      </div>
    );
  }

  if (scene.type === 'outro') {
    return (
      <div style={{...shell, alignItems: 'center', textAlign: 'center', justifyContent: 'center'}}>
        <div style={{fontSize: 118, fontWeight: 900, letterSpacing: -7}}>orbdev</div>
        <div style={{fontSize: 34, marginTop: 24, opacity: 0.62}}>{scene.body ?? 'Technology, explained quickly.'}</div>
      </div>
    );
  }

  const titleSize = scene.type === 'hook' ? 94 : 76;
  const badge = scene.type === 'impact' ? 'WHY IT MATTERS' : scene.type === 'caveat' ? 'ONE THING TO KNOW' : undefined;

  return (
    <div style={shell}>
      {kicker}
      {badge ? (
        <div
          style={{
            alignSelf: 'flex-start',
            border: '1px solid rgba(157,190,248,0.4)',
            borderRadius: 999,
            padding: '12px 18px',
            color: '#b7cff8',
            fontSize: 24,
            fontWeight: 800,
            letterSpacing: 2.5,
            marginBottom: 28
          }}
        >
          {badge}
        </div>
      ) : null}
      <div
        style={{
          maxWidth: 910,
          fontSize: titleSize,
          lineHeight: 0.98,
          fontWeight: 900,
          letterSpacing: scene.type === 'hook' ? -5 : -3.5
        }}
      >
        {scene.title}
      </div>
      {scene.body ? (
        <div
          style={{
            maxWidth: 900,
            fontSize: 42,
            lineHeight: 1.23,
            marginTop: 42,
            color: 'rgba(244,247,251,0.72)',
            fontWeight: 500
          }}
        >
          {scene.body}
        </div>
      ) : null}
    </div>
  );
};
