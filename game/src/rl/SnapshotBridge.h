// Copyright 2026 Chromium B.S.U. for RL contributors.
// Clarified Artistic License: see game/COPYING.
#ifndef RL_SNAPSHOT_BRIDGE_H
#define RL_SNAPSHOT_BRIDGE_H
namespace SnapshotBridge {
// Opt-in via CHROMIUM_BSU_RL_PROTOCOL=1. Linux/POSIX only in this stage.
bool initialize();
bool synchronous();
bool headless();
void waitForInput();
bool automaticRendering();
typedef bool (*TickFunction)(int dx, int dy, bool fire, void *context);
typedef bool (*RenderFunction)(void *context);
typedef void (*ResetFunction)(unsigned int seed, void *context);
// Called only on the game thread between complete loop iterations.
// True means close requested, stdin ended, or transport failed.
bool pump(float &keyboardX, float &keyboardY, TickFunction tick = 0, void *context = 0,
          RenderFunction render = 0, ResetFunction reset = 0);
}
#endif
