import { loadFont } from "@remotion/fonts";
import React from "react";
import { AbsoluteFill, Composition, Img, staticFile } from "remotion";

// YouTube thumbnail (1280x720): two story images split on a diagonal and
// two lines of big Japanese text. Props come from story.json "thumbnail"
// via scripts/thumbnail.py.

const FONT = "M PLUS Rounded 1c";
const FONT_STACK = `"${FONT}", "Noto Sans CJK JP", "Noto Sans JP", sans-serif`;
loadFont({ family: FONT, url: staticFile("MPLUSRounded1c-ExtraBold.ttf"), weight: "800" });

// Two channels must not look alike: 「ひたの人生ノート」 (hitano) keeps white + yellow on red,
// 「韓日 心の翻訳家」 (nichikan) gets white + mint on navy, a straight navy band and a mint seam.
type Brand = "hitano" | "nichikan";
type Props = { left: string | null; right: string | null; lines: string[]; brand?: Brand };
const LOOK = {
  hitano: { second: "#ffe14d", secondStroke: "#c4002f", firstStroke: "#000", seam: "white", band: null, tilt: -4 },
  nichikan: { second: "#8ef0d8", secondStroke: "#12305a", firstStroke: "#12305a", seam: "#8ef0d8", band: "rgba(10,30,60,0.72)", tilt: 0 },
} as const;

const stroke = (r: number, color: string) =>
  Array.from({ length: 24 }, (_, i) => {
    const a = (i / 24) * Math.PI * 2;
    return `${(Math.cos(a) * r).toFixed(1)}px ${(Math.sin(a) * r).toFixed(1)}px 0 ${color}`;
  }).join(", ");

const Photo: React.FC<{ src: string | null; clip: string; shade: string }> = ({ src, clip, shade }) => (
  <AbsoluteFill style={{ clipPath: clip, background: "#222" }}>
    {src ? <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
    <AbsoluteFill style={{ background: shade }} />
  </AbsoluteFill>
);

export const Thumbnail: React.FC<Props> = ({ left, right, lines, brand = "hitano" }) => {
  const look = LOOK[brand] ?? LOOK.hitano;
  return (
  <AbsoluteFill style={{ background: "black" }}>
    {/* left: the shocked relatives, a little cooler; right: calm 和子, warm */}
    <div style={{ position: "absolute", inset: 0, width: "62%" }}>
      <Photo src={left} clip="polygon(0 0, 100% 0, 75.6% 100%, 0 100%)" shade="linear-gradient(90deg, rgba(0,20,60,0.15), rgba(0,0,0,0))" />
    </div>
    <div style={{ position: "absolute", top: 0, bottom: 0, right: 0, width: "58%" }}>
      <Photo src={right} clip="polygon(34.6% 0, 100% 0, 100% 100%, 8.5% 100%)" shade="linear-gradient(270deg, rgba(60,30,0,0.1), rgba(0,0,0,0))" />
    </div>
    {/* white seam along the diagonal */}
    <svg width={1280} height={720} style={{ position: "absolute", inset: 0 }}>
      <line x1={794} y1={0} x2={600} y2={720} stroke={look.seam} strokeWidth={10} />
    </svg>
    {/* darken the bottom so the text always reads */}
    <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 40%, rgba(0,0,0,0.75) 100%)" }} />
    <div
      lang="ja"
      style={{
        position: "absolute",
        left: 30,
        right: 30,
        bottom: 26,
        textAlign: "center",
        fontFamily: FONT_STACK,
        fontWeight: 800,
        lineHeight: 1.12,
        background: look.band ?? undefined,
        borderRadius: 24,
        padding: look.band ? "10px 0 14px" : 0,
      }}
    >
      {lines.map((line, i) => (
        <div
          key={line}
          style={{
            // fit each line to the width; the second line is the punchline
            fontSize: Math.min(i === 0 ? 92 : 118, Math.floor(1200 / Math.max(1, line.length))),
            color: i === 0 ? "#ffffff" : look.second,
            textShadow: `${stroke(i === 0 ? 7 : 9, i === 0 ? look.firstStroke : look.secondStroke)}, ${stroke(i === 0 ? 11 : 14, "#000")}`,
          }}
        >
          {line}
        </div>
      ))}
    </div>
  </AbsoluteFill>
  );
};

// Shorts cover (1080x1920): shock image on top, calm image below, split on a
// slight diagonal, the two lines in the middle where the feed shows them best.
export const ThumbnailVertical: React.FC<Props> = ({ left, right, lines, brand = "hitano" }) => {
  const look = LOOK[brand] ?? LOOK.hitano;
  return (
  <AbsoluteFill style={{ background: "black" }}>
    <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: "58%" }}>
      <Photo src={left} clip="polygon(0 0, 100% 0, 100% 88%, 0 100%)" shade="linear-gradient(180deg, rgba(0,0,0,0) 60%, rgba(0,0,0,0.35))" />
    </div>
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: "50%" }}>
      <Photo src={right} clip="polygon(0 16%, 100% 0, 100% 100%, 0 100%)" shade="linear-gradient(0deg, rgba(0,0,0,0) 60%, rgba(0,0,0,0.35))" />
    </div>
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <line x1={0} y1={1114} x2={1080} y2={960} stroke={look.seam} strokeWidth={12} />
    </svg>
    <div
      lang="ja"
      style={{
        position: "absolute",
        left: 20,
        right: 20,
        top: 820,
        textAlign: "center",
        fontFamily: FONT_STACK,
        fontWeight: 800,
        lineHeight: 1.15,
        transform: `rotate(${look.tilt}deg)`,
        background: look.band ?? undefined,
        borderRadius: 32,
        padding: look.band ? "18px 0 24px" : 0,
      }}
    >
      {lines.map((line, i) => (
        <div
          key={line}
          style={{
            fontSize: Math.min(i === 0 ? 120 : 140, Math.floor(1020 / Math.max(1, line.length))),
            color: i === 0 ? "#ffffff" : look.second,
            textShadow: `${stroke(i === 0 ? 8 : 10, i === 0 ? look.firstStroke : look.secondStroke)}, ${stroke(i === 0 ? 13 : 16, "#000")}`,
          }}
        >
          {line}
        </div>
      ))}
    </div>
  </AbsoluteFill>
  );
};

export const ThumbnailComposition = () => (
  <>
  <Composition
    id="Thumbnail"
    component={Thumbnail}
    durationInFrames={1}
    fps={30}
    width={1280}
    height={720}
    defaultProps={{ left: null, right: null, lines: ["", ""] } as Props}
  />
  <Composition
    id="ThumbnailVertical"
    component={ThumbnailVertical}
    durationInFrames={1}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={{ left: null, right: null, lines: ["", ""] } as Props}
  />
  </>
);
