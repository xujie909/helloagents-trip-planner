import React from 'react';
import { useCurrentFrame, spring } from 'remotion';

interface TitleBarProps {
  scenicName: string;
  city: string;
}

export const TitleBar: React.FC<TitleBarProps> = ({ scenicName, city }) => {
  const frame = useCurrentFrame();

  const fadeIn = spring({
    frame,
    fps: 30,
    config: { damping: 200 },
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        padding: '32px 40px',
        opacity: fadeIn,
        zIndex: 10,
      }}
    >
      {/* Left: scenic name */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <div
            style={{
              width: '4px',
              height: '28px',
              background: 'linear-gradient(180deg, #c9a0dc, #a078c8)',
              borderRadius: '2px',
            }}
          />
          <span
            style={{
              color: '#fff',
              fontSize: '36px',
              fontWeight: 700,
              letterSpacing: '0.08em',
              textShadow: '0 2px 8px rgba(0,0,0,0.5)',
            }}
          >
            {scenicName}
          </span>
        </div>
        <span
          style={{
            color: 'rgba(255,255,255,0.55)',
            fontSize: '18px',
            marginTop: '4px',
            marginLeft: '16px',
            letterSpacing: '0.05em',
          }}
        >
          {city}
        </span>
      </div>

      {/* Right: guide label */}
      <div
        style={{
          background: 'rgba(0,0,0,0.5)',
          border: '1px solid rgba(201, 160, 220, 0.3)',
          borderRadius: '24px',
          padding: '10px 20px',
          backdropFilter: 'blur(6px)',
        }}
      >
        <span
          style={{
            color: '#e8e0f0',
            fontSize: '18px',
            letterSpacing: '0.04em',
          }}
        >
          🎀 导游：红美铃
        </span>
      </div>
    </div>
  );
};
