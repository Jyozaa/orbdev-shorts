import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Scene} from '../types';

type Props = {
  scene: Scene;
};

const accent = '#9fc1ff';
const white = '#f7f7f7';
const muted = 'rgba(247,247,247,0.62)';

const labelStyle: React.CSSProperties = {
  fontSize: 25,
  fontWeight: 850,
  letterSpacing: 4,
  color: accent
};

export const SceneCard: React.FC<Props> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 17, stiffness: 135, mass: 0.75}});
  const opacity = interpolate(frame, [0, 5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });
  const y = interpolate(enter, [0, 1], [34, 0]);
  const scale = interpolate(enter, [0, 1], [0.965, 1]);
  const sceneProgress = interpolate(frame, [0, Math.max(1, durationInFrames - 1)], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  const shell: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    padding: '230px 78px 360px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: scene.type === 'hook' || scene.type === 'metric' ? 'center' : 'flex-start',
    opacity,
    transform: `translateY(${y}px) scale(${scale})`,
    fontFamily: 'Arial, Helvetica, sans-serif'
  };

  const kicker = scene.kicker ? (
    <div style={{...labelStyle, marginBottom: 26}}>{scene.kicker.toUpperCase()}</div>
  ) : null;

  if (scene.type === 'hook') {
    return (
      <div style={{...shell, justifyContent: 'center'}}>
        {kicker}
        <div
          style={{
            fontSize: 108,
            lineHeight: 0.9,
            fontWeight: 950,
            letterSpacing: -6,
            maxWidth: 920
          }}
        >
          {scene.title}
        </div>
        <div
          style={{
            marginTop: 54,
            width: `${20 + sceneProgress * 72}%`,
            height: 8,
            background: white
          }}
        />
      </div>
    );
  }

  if (scene.type === 'metric') {
    const metricScale = interpolate(enter, [0, 1], [0.78, 1]);
    return (
      <div style={{...shell, alignItems: 'center', textAlign: 'center', justifyContent: 'center'}}>
        {kicker}
        <div
          style={{
            fontSize: 210,
            lineHeight: 0.85,
            fontWeight: 950,
            letterSpacing: -12,
            color: accent,
            transform: `scale(${metricScale})`
          }}
        >
          {scene.title}
        </div>
        {scene.body ? (
          <div style={{fontSize: 42, lineHeight: 1.12, maxWidth: 820, marginTop: 38, color: white, fontWeight: 750}}>
            {scene.body}
          </div>
        ) : null}
        <div
          style={{
            position: 'absolute',
            width: 560 + sceneProgress * 90,
            height: 560 + sceneProgress * 90,
            border: '2px solid rgba(159,193,255,0.24)',
            borderRadius: '50%',
            zIndex: -1
          }}
        />
      </div>
    );
  }

  if (scene.type === 'comparison') {
    const left = spring({frame, fps, delay: 1, config: {damping: 18, stiffness: 150}});
    const right = spring({frame, fps, delay: 5, config: {damping: 18, stiffness: 150}});
    return (
      <div style={shell}>
        {kicker}
        <div style={{fontSize: 78, lineHeight: 0.95, fontWeight: 950, letterSpacing: -4.5, marginBottom: 50}}>
          {scene.title}
        </div>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20}}>
          <div
            style={{
              border: '2px solid rgba(247,247,247,0.2)',
              padding: '34px 30px',
              minHeight: 260,
              transform: `translateX(${interpolate(left, [0,1], [-55,0])}px)`
            }}
          >
            <div style={{fontSize: 25, color: muted, marginBottom: 24, fontWeight: 800, letterSpacing: 2}}>
              {scene.leftTitle ?? 'BEFORE'}
            </div>
            <div style={{fontSize: 46, fontWeight: 900, lineHeight: 1.02}}>{scene.leftBody}</div>
          </div>
          <div
            style={{
              border: `2px solid ${accent}`,
              padding: '34px 30px',
              minHeight: 260,
              transform: `translateX(${interpolate(right, [0,1], [55,0])}px)`
            }}
          >
            <div style={{fontSize: 25, color: accent, marginBottom: 24, fontWeight: 800, letterSpacing: 2}}>
              {scene.rightTitle ?? 'NOW'}
            </div>
            <div style={{fontSize: 46, fontWeight: 900, lineHeight: 1.02}}>{scene.rightBody}</div>
          </div>
        </div>
        <div
          style={{
            marginTop: 28,
            height: 4,
            width: `${sceneProgress * 100}%`,
            background: accent
          }}
        />
      </div>
    );
  }

  if (scene.type === 'outro') {
    return (
      <div style={{...shell, alignItems: 'center', textAlign: 'center', justifyContent: 'center'}}>
        <div style={{fontSize: 120, fontWeight: 950, letterSpacing: -8}}>orbdev</div>
        <div style={{fontSize: 32, marginTop: 20, color: muted}}>{scene.body ?? 'Technology, explained quickly.'}</div>
      </div>
    );
  }

  const badge =
    scene.type === 'impact'
      ? 'WHY IT MATTERS'
      : scene.type === 'caveat'
        ? 'THE CATCH'
        : scene.kicker?.toUpperCase();

  return (
    <div style={shell}>
      {badge ? <div style={{...labelStyle, marginBottom: 28}}>{badge}</div> : null}
      <div
        style={{
          maxWidth: 900,
          fontSize: 82,
          lineHeight: 0.95,
          fontWeight: 950,
          letterSpacing: -4.5
        }}
      >
        {scene.title}
      </div>
      {scene.body ? (
        <div
          style={{
            maxWidth: 880,
            fontSize: 41,
            lineHeight: 1.18,
            marginTop: 38,
            color: muted,
            fontWeight: 600
          }}
        >
          {scene.body}
        </div>
      ) : null}
      <div
        style={{
          marginTop: 52,
          display: 'flex',
          gap: 12,
          alignItems: 'center'
        }}
      >
        {[0, 1, 2, 3].map((item) => (
          <div
            key={item}
            style={{
              height: 9,
              width: item === 3 ? 140 * sceneProgress : 34,
              background: item === 3 ? accent : 'rgba(247,247,247,0.24)'
            }}
          />
        ))}
      </div>
    </div>
  );
};
