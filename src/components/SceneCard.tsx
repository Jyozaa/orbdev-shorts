import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {DiagramNode, Scene} from '../types';

type Props = {
  scene: Scene;
};

const white = '#ffffff';
const muted = 'rgba(255,255,255,0.58)';
const faint = 'rgba(255,255,255,0.16)';

const nodeBox = (node: DiagramNode, index: number, enter: number) => (
  <div
    key={`${node.symbol}-${index}`}
    style={{
      minWidth: 190,
      minHeight: 190,
      border: '3px solid rgba(255,255,255,0.78)',
      borderRadius: 32,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24,
      transform: `scale(${0.88 + enter * 0.12})`,
      background: '#000000'
    }}
  >
    <div
      style={{
        color: white,
        fontSize: node.symbol.length > 5 ? 48 : 74,
        fontWeight: 950,
        letterSpacing: -3,
        lineHeight: 0.95,
        textAlign: 'center'
      }}
    >
      {node.symbol}
    </div>
    {node.label ? (
      <div
        style={{
          color: muted,
          fontSize: 22,
          fontWeight: 800,
          marginTop: 18,
          letterSpacing: 1,
          textTransform: 'uppercase',
          textAlign: 'center'
        }}
      >
        {node.label}
      </div>
    ) : null}
  </div>
);

export const SceneCard: React.FC<Props> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 17, stiffness: 155, mass: 0.7}});
  const opacity = interpolate(frame, [0, 5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });
  const y = interpolate(enter, [0, 1], [30, 0]);
  const sceneProgress = interpolate(frame, [0, Math.max(1, durationInFrames - 1)], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  const shell: React.CSSProperties = {
    position: 'absolute',
    inset: 0,
    padding: '220px 74px 350px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    opacity,
    transform: `translateY(${y}px)`,
    fontFamily: 'Arial, Helvetica, sans-serif',
    backgroundColor: '#000000'
  };

  if (scene.type === 'hook') {
    return (
      <div style={shell}>
        <div
          style={{
            fontSize: 112,
            lineHeight: 0.9,
            fontWeight: 950,
            letterSpacing: -7,
            textAlign: 'center',
            maxWidth: 900
          }}
        >
          {scene.title}
        </div>
        <div
          style={{
            marginTop: 60,
            width: 180 + sceneProgress * 520,
            height: 8,
            background: white
          }}
        />
      </div>
    );
  }

  if (scene.type === 'metric') {
    return (
      <div style={shell}>
        <div
          style={{
            fontSize: 236,
            lineHeight: 0.82,
            fontWeight: 950,
            letterSpacing: -14,
            color: white,
            transform: `scale(${0.78 + enter * 0.22})`
          }}
        >
          {scene.title}
        </div>
        {scene.body ? (
          <div
            style={{
              fontSize: 33,
              fontWeight: 850,
              textTransform: 'uppercase',
              letterSpacing: 2,
              marginTop: 34,
              color: white,
              textAlign: 'center'
            }}
          >
            {scene.body}
          </div>
        ) : null}
        <div
          style={{
            position: 'absolute',
            width: 580 + sceneProgress * 120,
            height: 580 + sceneProgress * 120,
            border: '3px solid rgba(255,255,255,0.16)',
            borderRadius: '50%',
            zIndex: -1
          }}
        />
      </div>
    );
  }

  if (scene.type === 'diagram') {
    const nodes = scene.nodes ?? [];
    return (
      <div style={shell}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 24,
            width: '100%'
          }}
        >
          {nodes.map((node, index) => {
            const nodeEnter = spring({
              frame,
              fps,
              delay: index * 4,
              config: {damping: 18, stiffness: 165}
            });
            return (
              <React.Fragment key={`diagram-${index}`}>
                {nodeBox(node, index, nodeEnter)}
                {index < nodes.length - 1 ? (
                  <div
                    style={{
                      fontSize: 86,
                      fontWeight: 900,
                      color: white,
                      opacity: interpolate(nodeEnter, [0,1], [0,1])
                    }}
                  >
                    →
                  </div>
                ) : null}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    );
  }

  if (scene.type === 'comparison') {
    const left = spring({frame, fps, delay: 1, config: {damping: 18, stiffness: 150}});
    const right = spring({frame, fps, delay: 5, config: {damping: 18, stiffness: 150}});

    const side = (
      symbol: string | undefined,
      label: string | undefined,
      value: string | undefined,
      enterValue: number
    ) => (
      <div
        style={{
          width: 390,
          height: 390,
          border: '3px solid rgba(255,255,255,0.72)',
          borderRadius: 36,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          transform: `scale(${0.88 + enterValue * 0.12})`
        }}
      >
        {symbol ? <div style={{fontSize: 74, marginBottom: 22}}>{symbol}</div> : null}
        <div style={{fontSize: 58, fontWeight: 950, textAlign: 'center'}}>{value}</div>
        {label ? (
          <div
            style={{
              marginTop: 22,
              fontSize: 23,
              color: muted,
              fontWeight: 850,
              textTransform: 'uppercase',
              letterSpacing: 1.5,
              textAlign: 'center'
            }}
          >
            {label}
          </div>
        ) : null}
      </div>
    );

    return (
      <div style={shell}>
        <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 32}}>
          {side(scene.leftSymbol, scene.leftTitle, scene.leftBody, left)}
          <div style={{fontSize: 92, fontWeight: 900}}>→</div>
          {side(scene.rightSymbol, scene.rightTitle, scene.rightBody, right)}
        </div>
      </div>
    );
  }

  if (scene.type === 'outro') {
    return (
      <div style={shell}>
        <div style={{fontSize: 128, fontWeight: 950, letterSpacing: -8}}>orbdev</div>
      </div>
    );
  }

  const icon =
    scene.type === 'impact'
      ? '⚡'
      : scene.type === 'caveat'
        ? '!'
        : '◉';

  return (
    <div style={shell}>
      <div
        style={{
          width: 210,
          height: 210,
          borderRadius: scene.type === 'caveat' ? 34 : '50%',
          border: '4px solid rgba(255,255,255,0.82)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 102,
          fontWeight: 950,
          marginBottom: 54
        }}
      >
        {icon}
      </div>
      <div
        style={{
          maxWidth: 800,
          fontSize: 70,
          lineHeight: 0.94,
          fontWeight: 950,
          letterSpacing: -4,
          textAlign: 'center'
        }}
      >
        {scene.title}
      </div>
      <div
        style={{
          marginTop: 52,
          display: 'flex',
          gap: 14,
          alignItems: 'center'
        }}
      >
        {[0,1,2].map((item) => (
          <div
            key={item}
            style={{
              height: 8,
              width: item === 2 ? 160 * sceneProgress : 42,
              background: item === 2 ? white : faint
            }}
          />
        ))}
      </div>
    </div>
  );
};
