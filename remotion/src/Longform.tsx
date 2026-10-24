import { Audio, Video } from "@remotion/media";
import { loadFont } from "@remotion/fonts";
import React from "react";
import {
  AbsoluteFill,
  Composition,
  Easing,
  Img,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";
import raw from "./longform.json";

// 16:9 longform built by scripts/longform.py (images + motion, narration,
// Omni clips, chat / letter / title cards). Screen text is Japanese only.

const FPS = 30;
// "aspect": "9:16" in story.json → the same timeline as a vertical short
const VERTICAL = (raw as { aspect?: string }).aspect === "9:16";
const W = VERTICAL ? 1080 : 1920;
const H = VERTICAL ? 1920 : 1080;
const CAPTION_BOTTOM = VERTICAL ? 420 : 80; // above the Shorts buttons and title
const FONT = "M PLUS Rounded 1c";
const FONT_STACK = `"${FONT}", "Noto Sans CJK JP", "Noto Sans JP", sans-serif`;
const HAND = "Klee One";

loadFont({ family: FONT, url: staticFile("MPLUSRounded1c-ExtraBold.ttf"), weight: "800" });
loadFont({ family: HAND, url: staticFile("KleeOne-SemiBold.ttf"), weight: "600" });

type Caption = { text: string; start: number; end: number; speaker?: string; color?: string };
type ClipPart = {
  file: string | null;
  id: string;
  from: number;
  seconds: number;
  zoom?: number;
  rate?: number;
  muted?: boolean;
  captions: Caption[];
};
type Message = { name: string; text: string; at: number; color: string };
type Scene = {
  id: string;
  type: "narration" | "line" | "clip" | "image" | "title" | "card" | "chat" | "letter" | "end";
  start: number;
  frames: number;
  transition: "cut" | "fade" | "flash" | "whip";
  sfx: string[];
  captions: Caption[];
  speech: number[][];
  image?: string | null;
  imageId?: string;
  imagePrompt?: string;
  motion?: string;
  strong?: boolean;
  focus?: [number, number] | null;
  filter?: string | null;
  audio?: string;
  speaker?: string;
  color?: string;
  clips?: ClipPart[];
  group?: string;
  messages?: Message[];
  letterLines?: Caption[];
  text?: string;
  disclaimer?: string;
  talk?: boolean; // Vrew narration: an actor speaks this line, so the narration is silent here
};
type Timeline = {
  total: number;
  scenes: Scene[];
  bgm: { file: string; volume: number; duck: number; seconds: number } | null;
  narration?: { file: string } | null; // one recorded narration (Vrew) for the whole video
};

const data = raw as unknown as Timeline;
const TOTAL = Math.max(1, data.total);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const easeInOut = Easing.inOut(Easing.cubic);
const FADE = 15; // frames of crossfade
const WHIP = 8; // frames of whip slide

const outline = (r: number) =>
  Array.from({ length: 16 }, (_, i) => {
    const a = (i / 16) * Math.PI * 2;
    return `${(Math.cos(a) * r).toFixed(1)}px ${(Math.sin(a) * r).toFixed(1)}px 0 #000`;
  }).join(", ") + ", 0 6px 12px rgba(0,0,0,0.6)";

// ───────────── image motion ─────────────

// Returns the CSS transform for one frame of a motion. Moves are big on
// purpose (small moves looked like still pictures), start on the first frame
// and keep going until the last one, and long scenes travel further.
const motionStyle = (
  motion: string,
  frame: number,
  frames: number,
  focus: [number, number],
  strong: boolean,
): React.CSSProperties => {
  const t = frame / FPS;
  const lin = Math.min(1, frame / Math.max(1, frames - 1));
  const p = 0.75 * lin + 0.25 * easeInOut(lin); // mostly steady speed: no slow start, no stop at the end
  const long = interpolate(frames / FPS, [5, 10], [1, 1.35], clamp); // longer scene = bigger move
  const zoom = Math.min(0.8, 0.6 * long); // 1.0 -> 1.6x (up to 1.8x on long scenes)
  const origin = `${focus[0] * 100}% ${focus[1] * 100}%`;
  const after = (sec: number) => {
    const k = interpolate(t, [sec, frames / FPS], [0, 1], clamp);
    return 0.75 * k + 0.25 * easeInOut(k);
  };
  switch (motion) {
    case "zoom_out_big":
      return { transform: `scale(${1 + zoom * (1 - p)})`, transformOrigin: origin };
    case "pan_left":
    case "pan_right": {
      const dir = motion === "pan_right" ? -1 : 1; // camera right = picture moves left
      return { transform: `translateX(${dir * (0.44 * p - 0.22) * W}px) scale(${1.5 + 0.12 * p})` };
    }
    case "pan_up":
    case "pan_down": {
      const dir = motion === "pan_down" ? -1 : 1;
      return { transform: `translateY(${dir * (0.5 * p - 0.25) * H}px) scale(${1.6 + 0.12 * p})` };
    }
    case "slide_in_left":
    case "slide_in_right": {
      // smooth glide in (no bounce)
      const k = interpolate(t, [0, 0.45], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
      const from = motion === "slide_in_left" ? -W : W;
      return {
        transform: `translateX(${(1 - k) * from}px) scale(${1 + 0.4 * after(0.4)})`,
        transformOrigin: origin,
      };
    }
    case "punch_zoom": {
      const hit = interpolate(t, [0, 0.2], [1, 1.65], { ...clamp, easing: Easing.out(Easing.cubic) });
      const s = t < 0.5 ? hit : 1.65 + 0.2 * after(0.5);
      const shake = strong && t > 0.2 && t < 0.5 ? (1 - (t - 0.2) / 0.3) * 30 : 0;
      return {
        transform: `translate(${Math.sin(frame * 2.7) * shake}px, ${Math.cos(frame * 3.1) * shake}px) scale(${s})`,
        transformOrigin: origin,
      };
    }
    case "shake": {
      const amp = t < 0.8 ? (strong ? 40 : 14) * (1 - t / 0.8) : 0;
      return {
        transform: `translate(${Math.sin(frame * 2.9) * amp}px, ${Math.cos(frame * 3.7) * amp}px) scale(${1.25 + 0.35 * after(0.8)})`,
        transformOrigin: origin,
      };
    }
    case "push_slow":
      return { transform: `scale(${1 + 0.35 * lin})`, transformOrigin: origin };
    case "zoom_in_big":
    default:
      return { transform: `scale(${1 + zoom * p})`, transformOrigin: origin };
  }
};

const Picture: React.FC<{ scene: Scene; dim?: boolean }> = ({ scene, dim }) => {
  const frame = useCurrentFrame();
  const focus = scene.focus ?? [0.5, 0.33];
  const sepia = scene.filter === "sepia";
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#111" }}>
      <AbsoluteFill style={motionStyle(scene.motion ?? "zoom_in_big", frame, scene.frames, focus, scene.strong ?? false)}>
        {scene.image ? (
          <Img
            src={staticFile(scene.image)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              filter: [sepia ? "sepia(0.85) contrast(1.05) brightness(0.95)" : "", dim ? "blur(14px) brightness(0.45)" : ""].join(" "),
            }}
          />
        ) : (
          <Placeholder scene={scene} />
        )}
      </AbsoluteFill>
      {sepia ? (
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(30,15,0,0.55) 100%)" }} />
      ) : null}
    </AbsoluteFill>
  );
};

const Placeholder: React.FC<{ scene: Scene }> = ({ scene }) => (
  <AbsoluteFill
    style={{
      background: "linear-gradient(135deg, #2b2f3a, #14161c)",
      alignItems: "center",
      justifyContent: "center",
      color: "#cfd6e4",
      fontFamily: FONT_STACK,
      textAlign: "center",
      padding: 120,
    }}
  >
    <div style={{ fontSize: 120, fontWeight: 800 }}>{scene.imageId ?? scene.id}</div>
    <div style={{ fontSize: 34, marginTop: 24, opacity: 0.7, maxWidth: 1500, overflowWrap: "anywhere" }}>{scene.imagePrompt}</div>
  </AbsoluteFill>
);

// ───────────── captions ─────────────

const useCaption = (captions: Caption[], offsetSec = 0) => {
  const frame = useCurrentFrame();
  const t = frame / FPS - offsetSec;
  const c = captions.find((x) => t >= x.start && t < x.end);
  const k = c ? frame - Math.round((c.start + offsetSec) * FPS) : 0;
  return { c, p: interpolate(k, [0, 5], [0, 1], clamp) };
};

// Narration: big white text with a black outline at the bottom.
const Subtitle: React.FC<{ captions: Caption[]; left?: number; right?: number }> = ({ captions, left = 80, right = 80 }) => {
  const { c, p } = useCaption(captions);
  if (!c) return null;
  return (
    <div
      lang="ja"
      style={{
        position: "absolute",
        left,
        right,
        bottom: CAPTION_BOTTOM,
        textAlign: "center",
        fontFamily: FONT_STACK,
        fontWeight: 800,
        fontSize: 62,
        lineHeight: 1.3,
        color: "#fff",
        textShadow: outline(7),
        whiteSpace: "pre-line",
        opacity: p,
        transform: `translateY(${(1 - p) * 12}px)`,
      }}
    >
      {c.text}
    </div>
  );
};

// Dialogue: a speech bubble with the speaker's color as the border (no name on screen).
const Bubble: React.FC<{ captions: Caption[]; color?: string; offsetSec?: number }> = ({
  captions,
  color,
  offsetSec = 0,
}) => {
  const { c, p } = useCaption(captions, offsetSec);
  if (!c) return null;
  const tag = c.color ?? color ?? "#888";
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: CAPTION_BOTTOM - 10,
        display: "flex",
        justifyContent: "center",
        opacity: p,
        transform: `scale(${0.92 + 0.08 * p})`,
      }}
    >
      <div
        lang="ja"
        style={{
          position: "relative",
          background: "rgba(255,255,255,0.96)",
          color: "#1d1d1d",
          borderRadius: 36,
          padding: "34px 56px 30px",
          maxWidth: Math.min(1500, W - 120),
          fontFamily: FONT_STACK,
          fontWeight: 800,
          fontSize: 56,
          lineHeight: 1.35,
          whiteSpace: "pre-line",
          textAlign: "center",
          border: `6px solid ${tag}`,
          boxShadow: "0 10px 30px rgba(0,0,0,0.45)",
        }}
      >
        {c.text}
      </div>
    </div>
  );
};

// ───────────── scene types ─────────────

const ClipScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  let at = 0;
  return (
    <AbsoluteFill style={{ background: "black" }}>
      {(scene.clips ?? []).map((part) => {
        const from = Math.round(at * FPS);
        const dur = Math.max(1, Math.round(part.seconds * FPS));
        at += part.seconds;
        return (
          <Sequence key={part.id + from} from={from} durationInFrames={dur} name={part.id}>
            {part.file ? (
              <Video
                src={staticFile(part.file)}
                trimBefore={Math.round(part.from * FPS)}
                playbackRate={part.rate ?? 1}
                muted={part.muted ?? false}
                objectFit="cover"
                style={{ width: "100%", height: "100%", transform: `scale(${part.zoom ?? 1})` }}
              />
            ) : (
              <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", color: "#888", fontSize: 90, fontFamily: FONT_STACK }}>
                {part.id}.mp4
              </AbsoluteFill>
            )}
            <Bubble captions={part.captions} />
          </Sequence>
        );
      })}
      {/* Vrew narration: the scene's own captions (a bubble when the actor speaks) */}
      {scene.talk ? <Bubble captions={scene.captions} color={scene.color} /> : <Subtitle captions={scene.captions} />}
    </AbsoluteFill>
  );
};

const Phone: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 12], [0, 1], { ...clamp, easing: Easing.out(Easing.back(1.2)) });
  return (
    <div
      style={{
        position: "absolute",
        right: 170,
        top: 70,
        width: 480,
        height: 940,
        borderRadius: 64,
        background: "#111",
        padding: 16,
        boxShadow: "0 30px 80px rgba(0,0,0,0.6)",
        transform: `translateX(${(1 - enter) * 700}px) rotate(${(1 - enter) * 6}deg)`,
      }}
    >
      <div style={{ width: "100%", height: "100%", borderRadius: 50, overflow: "hidden", background: "#7d9ac4", position: "relative" }}>
        <div
          lang="ja"
          style={{
            background: "#253043",
            color: "#fff",
            height: 120,
            display: "flex",
            alignItems: "flex-end",
            padding: "0 28px 20px",
            fontFamily: FONT_STACK,
            fontWeight: 800,
            fontSize: 32,
          }}
        >
          ‹ {scene.group}
        </div>
        <div style={{ padding: "24px 20px", display: "flex", flexDirection: "column", gap: 22 }}>
          {(scene.messages ?? []).map((m) => {
            const k = frame - Math.round(m.at * FPS);
            if (k < 0) return null;
            const pop = interpolate(k, [0, 7], [0, 1], { ...clamp, easing: Easing.out(Easing.back(2)) });
            return (
              <div key={m.at} style={{ display: "flex", gap: 14, transform: `scale(${pop})`, transformOrigin: "left top", opacity: Math.min(1, pop * 2) }}>
                <div style={{ width: 62, height: 62, borderRadius: 31, background: m.color, flexShrink: 0, color: "#fff", fontFamily: FONT_STACK, fontWeight: 800, fontSize: 30, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {m.name.slice(0, 1)}
                </div>
                <div>
                  <div lang="ja" style={{ color: "#f4f7fb", fontFamily: FONT_STACK, fontWeight: 800, fontSize: 22, marginBottom: 6 }}>
                    {m.name}
                  </div>
                  <div
                    lang="ja"
                    style={{
                      background: "#fff",
                      color: "#1c1c1c",
                      borderRadius: 26,
                      padding: "14px 22px",
                      fontFamily: FONT_STACK,
                      fontWeight: 800,
                      fontSize: 29,
                      lineHeight: 1.35,
                      maxWidth: 310,
                    }}
                  >
                    {m.text}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const LetterScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", inset: 0, opacity: 0.3 }}>
        <Picture scene={scene} />
      </div>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 30% 20%, rgba(255,250,238,0.9), rgba(238,226,203,0.92) 70%, rgba(215,198,168,0.95))",
        }}
      />
      <svg width={W} height={H} style={{ position: "absolute", inset: 0, opacity: 0.25, mixBlendMode: "multiply" }}>
        <filter id="washi">
          <feTurbulence type="fractalNoise" baseFrequency="0.012 0.18" numOctaves={3} seed={7} />
          <feColorMatrix values="0 0 0 0 0.55  0 0 0 0 0.47  0 0 0 0 0.36  0 0 0 0.9 0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#washi)" />
      </svg>
      <div
        lang="ja"
        style={{
          position: "absolute",
          left: 160,
          right: 160,
          top: 120,
          fontFamily: `"${HAND}", ${FONT_STACK}`,
          fontWeight: 600,
          fontSize: 46,
          lineHeight: 1.8,
          color: "#3a2a1c",
        }}
      >
        {(scene.letterLines ?? []).map((l) => (
          <div key={l.start} style={{ opacity: interpolate(t, [l.start, l.start + 0.6], [0, 1], clamp) }}>
            {l.text.replace("\n", "")}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const TitleScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 14], [0, 1], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) });
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, #2a1d12, #0b0705)", alignItems: "center", justifyContent: "center" }}>
      <div
        lang="ja"
        style={{
          fontFamily: FONT_STACK,
          fontWeight: 800,
          fontSize: 82,
          lineHeight: 1.4,
          color: "#ffe14d",
          textAlign: "center",
          textShadow: outline(7),
          whiteSpace: "pre-line",
          opacity: p,
          transform: `scale(${0.85 + 0.15 * p + 0.04 * (frame / scene.frames)})`,
          padding: "0 120px",
        }}
      >
        {(scene.text ?? "").replace(/。(?=.)/g, "。\n")}
      </div>
    </AbsoluteFill>
  );
};

const CardScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const text = scene.text ?? "";
  const shown = Math.min(text.length, Math.floor(frame / 3) + 1);
  return (
    <AbsoluteFill style={{ background: "black", alignItems: "center", justifyContent: "center" }}>
      <div lang="ja" style={{ fontFamily: FONT_STACK, fontWeight: 800, fontSize: 96, color: "#fff", letterSpacing: 8 }}>
        {text.slice(0, shown)}
        <span style={{ opacity: Math.floor(frame / 8) % 2 ? 0 : 1 }}>▍</span>
      </div>
    </AbsoluteFill>
  );
};

const EndScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, 14], [0, 1], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) });
  return (
    <AbsoluteFill style={{ background: "#120c08", alignItems: "center", justifyContent: "center" }}>
      <div
        lang="ja"
        style={{
          fontFamily: FONT_STACK,
          fontWeight: 800,
          fontSize: 96,
          lineHeight: 1.4,
          color: "#ffe14d",
          textAlign: "center",
          textShadow: outline(7),
          opacity: p,
          transform: `scale(${0.85 + 0.15 * p})`,
          padding: "0 140px",
          whiteSpace: "pre-line",
        }}
      >
        {(scene.text ?? "").replace(/、/, "、\n")}
      </div>
      <div lang="ja" style={{ position: "absolute", bottom: 90, fontFamily: FONT_STACK, fontWeight: 800, fontSize: 30, color: "rgba(255,255,255,0.7)", opacity: p }}>
        {scene.disclaimer}
      </div>
    </AbsoluteFill>
  );
};

const SceneView: React.FC<{ scene: Scene }> = ({ scene }) => {
  switch (scene.type) {
    case "clip":
      return <ClipScene scene={scene} />;
    case "title":
      return <TitleScene scene={scene} />;
    case "card":
      return <CardScene scene={scene} />;
    case "end":
      return <EndScene scene={scene} />;
    case "letter":
      return <LetterScene scene={scene} />;
    case "chat":
      return (
        <AbsoluteFill>
          <Picture scene={scene} dim />
          <Phone scene={scene} />
          <Subtitle captions={scene.captions} left={60} right={760} />
        </AbsoluteFill>
      );
    case "line":
      return (
        <AbsoluteFill>
          <Picture scene={scene} />
          <Bubble captions={scene.captions} color={scene.color} />
        </AbsoluteFill>
      );
    default:
      return (
        <AbsoluteFill>
          <Picture scene={scene} />
          {scene.type === "narration" ? <Subtitle captions={scene.captions} /> : null}
        </AbsoluteFill>
      );
  }
};

// Wraps a scene with its entry transition (fade / flash / whip).
const Enter: React.FC<{ scene: Scene; children: React.ReactNode }> = ({ scene, children }) => {
  const frame = useCurrentFrame();
  let style: React.CSSProperties = {};
  if (scene.transition === "fade") style = { opacity: interpolate(frame, [0, FADE], [0, 1], clamp) };
  if (scene.transition === "whip") {
    const k = interpolate(frame, [0, WHIP], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
    style = { transform: `translateX(${(1 - k) * W}px)`, filter: `blur(${(1 - k) * 40}px)` };
  }
  return (
    <AbsoluteFill style={style}>
      {children}
      {scene.transition === "flash" ? (
        <AbsoluteFill style={{ background: "white", opacity: interpolate(frame, [0, 3, 6], [1, 1, 0], clamp) }} />
      ) : null}
    </AbsoluteFill>
  );
};

// ───────────── sound ─────────────

const SFX: Record<string, string> = { whoosh: "sfx/whoosh.wav", impact: "sfx/impact.wav", pop: "sfx/pop.wav" };

// Global speech spans (frames), so the music can step aside.
const speech = data.scenes.flatMap((s) => s.speech.map(([a, b]) => [s.start + a * FPS, s.start + b * FPS]));
const DOWN = 6; // frames to duck
const UP = 12; // 0.4 s back up

const duckAt = (f: number) => {
  if (!data.bgm) return 0;
  let level = 1;
  for (const [a, b] of speech) {
    if (f >= a - DOWN && f <= b + UP) {
      const k = f < a ? (a - f) / DOWN : f > b ? (f - b) / UP : 0;
      level = Math.min(level, k);
    }
  }
  const quiet = data.bgm.duck / data.bgm.volume;
  const endScene = data.scenes[data.scenes.length - 1];
  const fadeOut = endScene?.type === "end" ? interpolate(f, [endScene.start, TOTAL - 1], [1, 0], clamp) : 1;
  return data.bgm.volume * (quiet + (1 - quiet) * level) * interpolate(f, [0, 15], [0, 1], clamp) * fadeOut;
};

// Vrew narration volume: silent while an actor speaks the line on screen.
const talks = data.scenes.filter((s) => s.talk).map((s) => [s.start, s.start + s.frames]);
const narrationAt = (f: number) => {
  for (const [a, b] of talks) {
    if (f >= a - 2 && f < b) return 0;
  }
  return 1;
};

// One song looped with a 2-second crossfade at every seam.
const Music: React.FC = () => {
  const bgm = data.bgm;
  if (!bgm || bgm.seconds < 6) return null;
  const len = Math.floor(bgm.seconds * FPS);
  const xf = 2 * FPS;
  const step = len - xf;
  const loops = Math.ceil(TOTAL / step);
  return (
    <>
      {Array.from({ length: loops }, (_, i) => (
        <Sequence key={i} from={i * step} durationInFrames={len} name={`bgm ${i + 1}`}>
          <Audio
            src={staticFile(bgm.file)}
            volume={(f) =>
              duckAt(i * step + f) *
              interpolate(f, [0, i === 0 ? 1 : xf], [i === 0 ? 1 : 0, 1], clamp) *
              interpolate(f, [len - xf, len - 1], [1, 0], clamp)
            }
          />
        </Sequence>
      ))}
    </>
  );
};

// ───────────── composition ─────────────

export const Longform: React.FC = () => {
  const scenes = data.scenes;
  return (
    <AbsoluteFill style={{ background: "black" }}>
      {scenes.map((s, i) => {
        const next = scenes[i + 1];
        const overlap = next?.transition === "fade" ? FADE : next?.transition === "whip" ? WHIP : 0;
        return (
          <Sequence key={s.id} name={`${s.id} ${s.type}`} from={s.start} durationInFrames={s.frames + overlap}>
            <Enter scene={s}>
              <SceneView scene={s} />
            </Enter>
          </Sequence>
        );
      })}
      {scenes.map((s) => (
        <Sequence key={`a${s.id}`} from={s.start} durationInFrames={s.frames} layout="none">
          {s.audio ? <Audio src={staticFile(s.audio)} /> : null}
          {s.sfx.filter((x) => SFX[x]).map((x) => (
            <Audio key={x} src={staticFile(SFX[x])} volume={0.5} />
          ))}
          {(s.messages ?? []).map((m) => (
            <Sequence key={m.at} from={Math.round(m.at * FPS)} layout="none">
              <Audio src={staticFile(SFX.pop)} volume={0.45} />
            </Sequence>
          ))}
        </Sequence>
      ))}
      {data.narration ? <Audio src={staticFile(data.narration.file)} volume={narrationAt} /> : null}
      <Music />
    </AbsoluteFill>
  );
};

export const LongformComposition = () => (
  <Composition id="Longform" component={Longform} durationInFrames={TOTAL} fps={FPS} width={W} height={H} />
);
