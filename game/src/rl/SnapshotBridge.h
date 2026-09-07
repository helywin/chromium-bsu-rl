// Copyright 2026 Chromium B.S.U. for RL contributors.
// Clarified Artistic License: see game/COPYING.
#ifndef RL_SNAPSHOT_BRIDGE_H
#define RL_SNAPSHOT_BRIDGE_H
namespace SnapshotBridge {
// Opt-in via CHROMIUM_BSU_RL_PROTOCOL=1. Linux/POSIX only in this stage.
bool initialize();
// Called only on the game thread between complete loop iterations.
// True means close requested, stdin ended, or transport failed.
bool pump(float keyboardX, float keyboardY);
}
#endif
