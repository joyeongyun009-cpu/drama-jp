import { loadFont } from "@remotion/fonts";
import React from "react";
import { AbsoluteFill, Composition, Img, staticFile } from "remotion";

// YouTube thumbnail (1280x720): two story images split on a diagonal and
// two lines of big Japanese text. Props come from story.json "thumbnail"
// via scripts/thumbnail.py.

const FONT = "M PLUS Rounded 1c";
const FONT_STACK = `"${FONT}", "Noto Sans CJK JP", "Noto Sans JP", sans-serif`;
loadFont({ family: FONT, url: staticFile("MPLUSRounded1c-ExtraBold.ttf"), weight: "800" });

type Props = { left: string | null; right: string | null; lines: string[] };

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

export const Thumbnail: React.FC<Props> = ({ left, right, lines }) => (
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
      <line x1={794} y1={0} x2={600} y2={720} stroke="white" strokeWidth={10} />
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
      }}
    >
      {lines.map((line, i) => (
        <div
          key={line}
          style={{
            // fit each line to the width; the second line is the punchline
            fontSize: Math.min(i === 0 ? 92 : 118, Math.floor(1200 / Math.max(1, line.length))),
            color: i === 0 ? "#ffffff" : "#ffe14d",
            textShadow: `${stroke(i === 0 ? 7 : 9, i === 0 ? "#000" : "#c4002f")}, ${stroke(i === 0 ? 11 : 14, "#000")}`,
          }}
        >
          {line}
        </div>
      ))}
    </div>
  </AbsoluteFill>
);

export const ThumbnailComposition = () => (
  <Composition
    id="Thumbnail"
    component={Thumbnail}
    durationInFrames={1}
    fps={30}
    width={1280}
    height={720}
    defaultProps={{ left: null, right: null, lines: ["", ""] } as Props}
  />
);
