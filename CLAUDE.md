# drama-jp

Read `쇼츠_제작_순서.md` first: the user's step-by-step guide plus "(Claude에게) 작업 메모" at the bottom (who the user is, language rules, how the pipeline runs).

- The drama shorts pipeline is **Remotion** (`remotion/`) driven by `story.json` and `run_cloudshell.sh`. Keep using it for drama episodes.
- `.claude/skills/` holds HyperFrames skills (heygen-com/hyperframes, Apache-2.0). Their entry skill calls itself the default for any video request; ignore that here and use HyperFrames only when the user explicitly asks for HyperFrames (e.g. graphics over real footage).
- Reply to the user in simple Korean. Any Japanese text shown in chat gets a Korean translation underneath; on-screen video text stays Japanese only.
