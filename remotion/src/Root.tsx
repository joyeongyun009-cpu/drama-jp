import { MyComposition } from "./Composition";
import { LongformComposition } from "./Longform";
import { ThumbnailComposition } from "./Thumbnail";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <MyComposition />
      <LongformComposition />
      <ThumbnailComposition />
    </>
  );
};
