import React, { useMemo } from 'react';
import { Img, staticFile, useCurrentFrame, interpolate } from 'remotion';
import type { SceneSegment } from '../config';

interface BackgroundProps {
  scenes: SceneSegment[];
  sceneStarts: number[];
}

export const Background: React.FC<BackgroundProps> = ({ scenes, sceneStarts }) => {
  const frame = useCurrentFrame();

  // Determine which scene we're in
  const { currentSceneIndex, localFrame, nextStart } = useMemo(() => {
    let idx = 0;
    for (let i = scenes.length - 1; i >= 0; i--) {
      if (frame >= sceneStarts[i]) {
        idx = i;
        break;
      }
    }
    const next =
      idx < scenes.length - 1 ? sceneStarts[idx + 1] : sceneStarts[idx] + scenes[idx].durationInFrames;
    return {
      currentSceneIndex: idx,
      localFrame: frame - sceneStarts[idx],
      nextStart: next,
    };
  }, [frame, scenes, sceneStarts]);

  const currentScene = scenes[currentSceneIndex];

  // Ken Burns effect: slow zoom in
  const scale = interpolate(
    localFrame,
    [0, currentScene.durationInFrames],
    [1, 1.08],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Fade out near scene transition
  const transitionFrames = 15;
  const fadeStart = nextStart - transitionFrames;
  const fadeOutOpacity = interpolate(
    frame,
    [fadeStart, nextStart],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
      }}
    >
      {scenes.map((scene, idx) => {
        // Only render current and next scene for crossfade
        if (idx < currentSceneIndex - 1 || idx > currentSceneIndex + 1) return null;

        const isActive = idx === currentSceneIndex;
        const localF = isActive ? localFrame : 0;
        const sceneScale = isActive
          ? scale
          : interpolate(localF, [0, scenes[idx].durationInFrames], [1, 1.08], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });

        const opacity =
          idx === currentSceneIndex
            ? fadeOutOpacity
            : idx === currentSceneIndex + 1
            ? 1 - fadeOutOpacity
            : 0;

        // Entrance fade for new scene
        const entranceFade =
          idx === currentSceneIndex
            ? interpolate(localFrame, [0, 10], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              })
            : 1;

        const finalOpacity = isActive ? fadeOutOpacity * entranceFade : 1 - fadeOutOpacity;

        if (finalOpacity <= 0) return null;

        return (
          <div
            key={idx}
            style={{
              position: 'absolute',
              inset: 0,
              opacity: finalOpacity,
              transform: `scale(${sceneScale})`,
              transformOrigin: 'center center',
              transition: 'none',
            }}
          >
            <Img
              src={staticFile(`images/${scene.imageFile}`)}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
            {/* Dark overlay for readability */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                background:
                  'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.5) 100%)',
              }}
            />
          </div>
        );
      })}
    </div>
  );
};
