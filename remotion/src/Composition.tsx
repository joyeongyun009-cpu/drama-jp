import { Audio, Video } from "@remotion/media";
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
type Shot = { id: string; file: string; duration: number; captions: Caption[]; heard?: string };
type Bgm = { file: string; volume: number } | null;

const shots = data.shots as Shot[];
const bgm = ((data as { bgm?: Bgm }).bgm ?? null) as Bgm;
const shotFrames = shots.map((s) => Math.floor(s.duration * FPS));
const shotStarts = shotFrames.map((_, i) => shotFrames.slice(0, i).reduce((a, b) => a + b, 0));
const TOTAL = shotFrames.reduce((a, b) => a + b, 0) + Math.round(ENDING_SECONDS * FPS);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Spans (in frames) where someone is speaking, so the music can step aside.
const speech = shots.flatMap((s, i) =>
  s.heard && s.captions.length
    ? [[shotStarts[i] + s.captions[0].start * FPS, shotStarts[i] + s.captions[s.captions.length - 1].end * FPS]]
    : [],
);
const DUCK = 0.35; // music level while someone speaks
const RAMP = 9; // frames to fade between levels

const bgmVolume = (f: number) => {
  if (!bgm) return 0;
  const near = Math.min(
    ...speech.map(([a, b]) => (f < a ? a - f : f > b ? f - b : 0)),
    RAMP,
  );
  const duck = interpolate(near, [0, RAMP], [DUCK, 1], clamp);
  const fadeIn = interpolate(f, [0, 15], [0, 1], clamp);
  const fadeOut = interpolate(f, [TOTAL - 2 * FPS, TOTAL - 1], [1, 0], clamp);
  return bgm.volume * duck * fadeIn * fadeOut;
};

// Thick outline from stacked shadows (works even where -webkit-text-stroke does not).
const outline = (r: number) =>
  Array.from({ length: 16 }, (_, i) => {
    const a = (i / 16) * Math.PI * 2;
    return `${(Math.cos(a) * r).toFixed(1)}px ${(Math.sin(a) * r).toFixed(1)}px 0 #000`;
  }).join(", ") + ", 0 8px 14px rgba(0,0,0,0.6)";

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
        // Shrink long chunks so they stay on one line (about 940px of usable width).
        fontSize: Math.min(loud ? 112 : 100, Math.floor(940 / Math.max(1, c.text.length))),
        lineHeight: 1.2,
        color: loud ? "#ffe14d" : "#ffffff",
        textShadow: outline(8),
        scale: String(0.6 + 0.4 * p),
        opacity: Math.min(1, p * 2),
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
          textShadow: outline(7),
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
    {bgm ? <Audio src={staticFile(bgm.file)} loop loopVolumeCurveBehavior="extend" volume={bgmVolume} /> : null}
  </AbsoluteFill>
);

export const MyComposition = () => (
  <Composition id="Drama" component={Drama} durationInFrames={TOTAL} fps={FPS} width={1080} height={1920} />
);
