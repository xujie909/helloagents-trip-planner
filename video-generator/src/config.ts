import { z } from 'zod';

// 单个场景片段
export const SceneSegmentSchema = z.object({
  text: z.string(),              // 旁白文本
  expression: z.string(),        // 表情 key
  audioFile: z.string(),         // 音频文件名 (如 "seg-00.mp3")
  durationInFrames: z.number(),  // 帧数
  imageFile: z.string(),         // 景区图片文件名
});

export type SceneSegment = z.infer<typeof SceneSegmentSchema>;

// 视频 Props
export const VideoPropsSchema = z.object({
  scenicName: z.string(),        // 景区名
  city: z.string(),              // 城市
  scenes: z.array(SceneSegmentSchema),
  totalFrames: z.number(),
});

export type VideoProps = z.infer<typeof VideoPropsSchema>;

// 默认 Props（用于开发预览）
export const DEFAULT_PROPS: VideoProps = {
  scenicName: '故宫',
  city: '北京',
  scenes: [
    {
      text: '大家好呀！我是红美铃，今天由我来带大家逛逛这宏伟壮丽的故宫～',
      expression: 'confident',
      audioFile: 'seg-00.mp3',
      durationInFrames: 150,
      imageFile: 'placeholder.svg',
    },
    {
      text: '故宫，也就是紫禁城，是明清两朝的皇家宫殿，有六百多年的历史呢！',
      expression: 'excited',
      audioFile: 'seg-01.mp3',
      durationInFrames: 150,
      imageFile: 'placeholder.svg',
    },
    {
      text: '你看这红墙黄瓦，金碧辉煌的样子，是不是特别震撼呀？',
      expression: 'happy3',
      audioFile: 'seg-02.mp3',
      durationInFrames: 120,
      imageFile: 'placeholder.svg',
    },
  ],
  totalFrames: 480,
};
