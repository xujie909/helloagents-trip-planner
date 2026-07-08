import React, { useMemo } from 'react';
import { useCurrentFrame, spring, interpolate } from 'remotion';
import type { SceneSegment } from '../config';

interface SubtitlesProps {
  scenes: SceneSegment[];
  sceneStarts: number[];
  fps: number;
}

export const Subtitles: React.FC<SubtitlesProps> = ({ scenes, sceneStarts, fps }) => {
  const frame = useCurrentFrame();

  // Determine current scene
  const currentSceneIndex = useMemo(() => {
    let idx = 0;
    for (let i = scenes.length - 1; i >= 0; i--) {
      if (frame >= sceneStarts[i]) {
        idx = i;
        break;
      }
    }
    return idx;
  }, [frame, scenes, sceneStarts]);

  const currentScene = scenes[currentSceneIndex];
  const localFrame = frame - sceneStarts[currentSceneIndex];
  const fullText = currentScene.text;

  // Typewriter effect: reveal characters over time
  const charsPerFrame = 0.45; // ~13 chars/sec at 30fps
  const revealedChars = Math.min(
    Math.floor(localFrame * charsPerFrame),
    fullText.length
  );
  const displayText = fullText.slice(0, revealedChars);

  // Cursor blink
  const cursorVisible = Math.floor(frame / 15) % 2 === 0;

  // Entrance/exit animation
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 200 },
  });

  // Fade out at end of scene
  const exitFrames = 20;
  const exitStart = currentScene.durationInFrames - exitFrames;
  const exit = interpolate(localFrame, [exitStart, currentScene.durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const opacity = entrance * exit;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '6%',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '85%',
        maxWidth: '1400px',
        opacity,
        zIndex: 10,
      }}
    >
      {/* Name tag */}
      <div
        style={{
          display: 'inline-block',
          background: 'linear-gradient(135deg, #c9a0dc, #a078c8)',
          color: '#fff',
          padding: '6px 24px 6px 18px',
          borderRadius: '16px 16px 0 0',
          fontSize: '22px',
          fontWeight: 600,
          letterSpacing: '0.06em',
          marginBottom: '-1px',
          boxShadow: '0 -2px 12px rgba(201, 160, 220, 0.3)',
        }}
      >
        🎀 导游红美铃
      </div>

      {/* Dialog box */}
      <div
        style={{
          background: 'rgba(10, 10, 30, 0.88)',
          border: '1px solid rgba(201, 160, 220, 0.25)',
          borderRadius: '0 14px 14px 14px',
          padding: '18px 28px',
          minHeight: '80px',
          backdropFilter: 'blur(8px)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <span
          style={{
            color: '#e8e0f0',
            fontSize: '30px',
            lineHeight: 1.5,
            letterSpacing: '0.03em',
          }}
        >
          {displayText}
        </span>

        {/* Blinking cursor */}
        {revealedChars < fullText.length && cursorVisible && (
          <span
            style={{
              display: 'inline-block',
              width: '3px',
              height: '32px',
              background: '#c9a0dc',
              verticalAlign: 'middle',
            }}
          />
        )}
      </div>
    </div>
  );
};
