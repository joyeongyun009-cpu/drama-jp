import { Video } from "@remotion/media";
import { loadFont } from "@remotion/fonts";
import React from "react";
import {
  AbsoluteFill,
  Composition,
  Easing,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";
import data from "./shots.json";

const FPS = 30;
const ENDING_SECONDS = 3.5;
const FONT = "M PLUS Rounded 1c";
const FONT_STACK = `"${FONT}", "Noto Sans CJK JP", "Noto Sans JP", sans-serif`;

loadFont({ family: FONT, url: staticFile("MPLUSRounded1c-ExtraBold.ttf"), weight: "800" });

type Caption = { text: string; start: number; end: number };
type Shot = { id: string; file: string; duration: number; captions: Caption[] };

const shots = data.shots as Shot[];
const shotFrames = shots.map((s) => Math.floor(s.duration * FPS));
const shotStarts = shotFrames.map((_, i) => shotFrames.slice(0, i).reduce((a, b) => a + b, 0));
const TOTAL = shotFrames.reduce((a, b) => a + b, 0) + Math.round(ENDING_SECONDS * FPS);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Big centered caption: one chunk at a time, popping in with a slight overshoot.
const Captions: React.FC<{ captions: Caption[] }> = ({ captions }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const c = captions.find((x) => t >= x.start && t < x.end);
  if (!c) return null;
  const k = frame - Math.round(c.start * FPS);
  const p = interpolate(k, [0, 6], [0, 1], { ...clamp, easing: Easing.bezier(0.34, 1.6, 0.64, 1) });
  const loud = /[！？!?]/.test(c.text);
  return (
    <div
      lang="ja"
      style={{
        position: "absolute",
        left: 50,
        right: 50,
        top: 1080,
        textAlign: "center",
        fontFamily: FONT_STACK,
        fontWeight: 800,
        fontSize: loud ? 112 : 100,
        lineHeight: 1.2,
        color: loud ? "#ffe14d" : "#ffffff",
        WebkitTextStroke: "16px #000000",
        paintOrder: "stroke fill",
        scale: String(0.6 + 0.4 * p),
        opacity: Math.min(1, p * 2),
        filter: "drop-shadow(0 6px 10px rgba(0,0,0,0.5))",
      }}
    >
      {c.text}
    </div>
  );
};

const Ending: React.FC = () => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 12], [0, 1], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) });
  return (
    <AbsoluteFill style={{ background: "#120c08", alignItems: "center", justifyContent: "center" }}>
      <div
        lang="ja"
        style={{
          fontFamily: FONT_STACK,
          fontWeight: 800,
          fontSize: 104,
          color: "#ffe14d",
          textAlign: "center",
          WebkitTextStroke: "14px #000",
          paintOrder: "stroke fill",
          opacity: p,
          scale: String(0.8 + 0.2 * p),
          padding: "0 60px",
          whiteSpace: "pre-line",
        }}
      >
        {data.ending.question}
      </div>
      <div
        lang="ja"
        style={{
          position: "absolute",
          bottom: 360,
          fontFamily: FONT_STACK,
          fontWeight: 800,
          fontSize: 30,
          color: "rgba(255,255,255,0.7)",
          opacity: p,
        }}
      >
        {data.ending.note}
      </div>
    </AbsoluteFill>
  );
};

export const Drama: React.FC = () => (
  <AbsoluteFill style={{ background: "black" }}>
    {shots.map((s, i) => (
      <Sequence key={s.id} name={s.id} from={shotStarts[i]} durationInFrames={shotFrames[i]}>
        <Video src={staticFile(s.file)} objectFit="cover" style={{ width: "100%", height: "100%" }} />
        <Captions captions={s.captions} />
      </Sequence>
    ))}
    <Sequence name="ending" from={TOTAL - Math.round(ENDING_SECONDS * FPS)}>
      <Ending />
    </Sequence>
  </AbsoluteFill>
);

export const MyComposition = () => (
  <Composition id="Drama" component={Drama} durationInFrames={TOTAL} fps={FPS} width={1080} height={1920} />
);
