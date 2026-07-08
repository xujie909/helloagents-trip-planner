import React from 'react';
import { AbsoluteFill, Sequence, Audio, useVideoConfig, staticFile } from 'remotion';
import type { VideoProps } from './config';
import { Background } from './components/Background';
import { DigitalHuman } from './components/DigitalHuman';
import { Subtitles } from './components/Subtitles';
import { TitleBar } from './components/TitleBar';

export const ScenicVideo: React.FC<VideoProps> = ({
  scenicName,
  city,
  scenes,
  totalFrames,
}) => {
  const { fps } = useVideoConfig();

  // Calculate scene start frames
  let accumulated = 0;
  const sceneStarts = scenes.map((scene) => {
    const start = accumulated;
    accumulated += scene.durationInFrames;
    return start;
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0a0a14',
        fontFamily: '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
      }}
    >
      {/* Background with Ken Burns effect */}
      <Background scenes={scenes} sceneStarts={sceneStarts} />

      {/* Scene overlay - dark gradient at bottom for text readability */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '40%',
          background:
            'linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 50%, transparent 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Title bar */}
      <TitleBar scenicName={scenicName} city={city} />

      {/* Digital Human - expression changes per scene */}
      <DigitalHuman scenes={scenes} sceneStarts={sceneStarts} fps={fps} />

      {/* Subtitles */}
      <Subtitles scenes={scenes} sceneStarts={sceneStarts} fps={fps} />

      {/* Audio tracks in Sequences */}
      {scenes.map((scene, idx) => (
        <Sequence
          key={`audio-${idx}`}
          from={sceneStarts[idx]}
          durationInFrames={scene.durationInFrames}
        >
          <Audio src={staticFile(`audio/${scene.audioFile}`)} />
        </Sequence>
      ))}

      {/* Outro overlay */}
      <Sequence from={totalFrames - 90} durationInFrames={90}>
        <AbsoluteFill
          style={{
            backgroundColor: 'rgba(0,0,0,0)',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        />
      </Sequence>
    </AbsoluteFill>
  );
};
