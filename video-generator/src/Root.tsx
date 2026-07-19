import { Composition } from 'remotion';
import { ScenicVideo } from './ScenicVideo';
import { VideoPropsSchema, DEFAULT_PROPS } from './config';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ScenicVideo"
        component={ScenicVideo}
        durationInFrames={DEFAULT_PROPS.totalFrames}
        fps={24}
        width={1920}
        height={1080}
        schema={VideoPropsSchema}
        defaultProps={DEFAULT_PROPS}
        calculateMetadata={({ props }) => {
          // 根据实际脚本的 totalFrames 动态设置视频时长
          return {
            durationInFrames: props.totalFrames,
          };
        }}
      />
    </>
  );
};
