import React, { useMemo } from 'react';
import { Img, staticFile, useCurrentFrame, spring } from 'remotion';
import type { SceneSegment } from '../config';

// 表情文件名映射（与数字人 app 的 EXPRESSION_MAP 一致）
const EXPRESSION_FILES: Record<string, string> = {
  default: '开心2.PNG',
  happy_confident: '开心1（自信）.PNG',
  happy2: '开心2.PNG',
  happy3: '开心3.PNG',
  happy5: '开心5.PNG',
  excited: '开心6（兴奋）.PNG',
  happy6: '开心6.PNG',
  thinking: '思考1.PNG',
  surprised: '惊讶.PNG',
  confused: '疑惑.PNG',
  upset: '委屈.PNG',
  confident: '自信.PNG',
};

interface DigitalHumanProps {
  scenes: SceneSegment[];
  sceneStarts: number[];
  fps: number;
}

export const DigitalHuman: React.FC<DigitalHumanProps> = ({
  scenes,
  sceneStarts,
  fps,
}) => {
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

  const currentExpression = scenes[currentSceneIndex].expression;
  const imageFile = EXPRESSION_FILES[currentExpression] || EXPRESSION_FILES.default;
  const localFrame = frame - sceneStarts[currentSceneIndex];

  // Gentle breathing animation
  const breathe = spring({
    frame: frame,
    fps,
    config: { damping: 200, mass: 2, stiffness: 40 },
  });
  const breatheScale = 1 + Math.sin(frame * 0.05) * 0.008;

  // Entrance animation for new expression
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 20, mass: 0.8, stiffness: 200 },
  });

  return (
    <div
      style={{
        position: 'absolute',
        right: '4%',
        bottom: '8%',
        width: '32%',
        height: '75%',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        opacity: entrance,
        transform: `scale(${breatheScale * entrance}) translateY(${(1 - entrance) * 50}px)`,
        transformOrigin: 'bottom center',
        filter: 'drop-shadow(0 0 30px rgba(201, 160, 220, 0.25))',
      }}
    >
      <Img
        src={staticFile(`digital-human/${imageFile}`)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          objectPosition: 'bottom',
        }}
      />
    </div>
  );
};
