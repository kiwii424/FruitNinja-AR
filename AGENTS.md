# Rockfall Riot: HCI AR Game Handoff

## Mission

Build a desktop AR rhythm game for an ML project using webcam hand tracking.

Current concept:
- Static background from `assets/background`
- Webcam only for hand detection and preview
- Index finger slices falling rocks
- Fist catches escaping Pikmin-style runners
- Open palm triggers Fever in gameplay
- Music can drive spawn timing
- Leaderboard stores only each player's best score

## What Exists Now

Game flow:
- `START` -> player name, difficulty, music select, leaderboard, `Start` button
- `CALIBRATION` -> hand check and movement test
- `TUTORIAL` -> required onboarding
- `PLAYING` -> rhythm gameplay
- `PAUSED` -> manual pause or hand-loss pause
- `GALLERY` -> caught Pikmin summary
- `RESULTS` -> score + leaderboard

Tutorial flow:
1. `Cut`: user must slash a tutorial rock with index finger
2. `Catch`: user must grab a tutorial Pikmin with a fist
3. Game auto-starts after both steps succeed

Input model:
- `INDEX_SWORD`: cursor + slicing
- `OPEN_PALM`: Fever trigger in gameplay, pointer in menus
- `FIST`: Pikmin catching
- Start-menu hand selection uses a dwell circle above the hovered button and needs about 1.5 seconds to confirm

Speed model:
- Rock drop speed is scaled down to `0.1` of the previous baseline
- Difficulty still matters for rock falling speed
- Pikmin spawns are random from `0` to `3` per shattered rock
- Pikmin movement stays at normal speed and each runner may be normal-speed or very fast
- Countdown starts immediately when gameplay begins and runs `Get Ready 3 2 1`

## Key Files

- [main.py](/Users/meredithhuang/code/Python/Rockfall-Riot-HCI-AR-Game/main.py): app entrypoint
- [game/app.py](/Users/meredithhuang/code/Python/Rockfall-Riot-HCI-AR-Game/game/app.py): main loop, state machine, tutorial, UI flow, gameplay
- [game/camera.py](/Users/meredithhuang/code/Python/Rockfall-Riot-HCI-AR-Game/game/camera.py): camera selection, built-in camera preference on macOS
- [game/gestures.py](/Users/meredithhuang/code/Python/Rockfall-Riot-HCI-AR-Game/game/gestures.py): hand tracking and gesture classification
- [game/rhythm.py](/Users/meredithhuang/code/Python/Rockfall-Riot-HCI-AR-Game/game/rhythm.py): beat analysis and rock spawning
- [game/entities.py](/Users/meredithhuang/code/Python/Rockfall-Riot-HCI-AR-Game/game/entities.py): rocks, runners, spark effects
- [game/scoring.py](/Users/meredithhuang/code/Python/Rockfall-Riot-HCI-AR-Game/game/scoring.py): score, combo, judgement windows, fever gauge
- [game/leaderboard.py](/Users/meredithhuang/code/Python/Rockfall-Riot-HCI-AR-Game/game/leaderboard.py): persistent leaderboard logic
- [README.md](/Users/meredithhuang/code/Python/Rockfall-Riot-HCI-AR-Game/README.md): setup and troubleshooting

## How To Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

If camera routing is wrong on macOS:

```bash
python3 scripts/check_camera.py
ARFN_CAMERA_INDEX=1 python3 main.py
```

## Verification

Useful checks:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -f main.py game tests scripts
python3 scripts/check_camera.py
```

## Handoff Notes

When continuing work, check these areas first:
- `game/app.py`: most product logic is concentrated here
- tutorial and menu dwell behavior: tied to state-machine flow, easy to regress
- rhythm speed changes: tied to preroll timing and music start
- camera issues on macOS: usually permission or device-selection problems, not game logic

Current likely next steps:
- tune slow-speed feel after real user testing
- improve tutorial visuals and add more explicit arrows/highlights
- polish result/gallery UI text and layout
- add more assets and SFX if the presentation needs stronger feedback

## Known Constraints

- MediaPipe support can vary by Python/macOS build; fallback color tracking exists but is less accurate
- `assets/models/hand_landmarker.task` is expected locally for newer MediaPipe task builds
- Slow gameplay now creates a longer preroll before music starts
- The repo may be uncommitted and partially local; avoid destructive git cleanup
