// Copyright 2026 Chromium B.S.U. for RL contributors.
// Clarified Artistic License: see game/COPYING.
#include "SnapshotBridge.h"
#include "../Global.h"
#include "../HeroAircraft.h"
#include "../EnemyFleet.h"
#include <json-c/json.h>
#include <cerrno>
#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <fcntl.h>
#include <unistd.h>

namespace {
FILE *protocol = NULL;
std::string pending;
bool failed = false;
bool syncMode = false;
int64_t episodeTick = 0;
int64_t lastId = 0;
const size_t maxRequest = 8192;
const size_t maxResponse = 1024 * 1024;

void put(json_object *o, const char *key, json_object *value) {
    json_object_object_add(o, key, value);
}
json_object *vec(const float *v, int count) {
    json_object *a = json_object_new_array();
    for(int i = 0; i < count; ++i) json_object_array_add(a, json_object_new_double(v[i]));
    return a;
}
bool send(json_object *response) {
    const char *wire = json_object_to_json_string_ext(response, JSON_C_TO_STRING_PLAIN);
    bool ok = std::strlen(wire) <= maxResponse;
    if(ok) ok = std::fprintf(protocol, "%s\n", wire) >= 0 && std::fflush(protocol) == 0;
    json_object_put(response);
    failed = !ok;
    return ok;
}
json_object *envelope(int64_t id, bool ok) {
    json_object *o = json_object_new_object();
    put(o, "protocol_version", json_object_new_int(1));
    put(o, "request_id", id > 0 ? json_object_new_int64(id) : NULL);
    put(o, "ok", json_object_new_boolean(ok));
    return o;
}
void error(int64_t id, const char *code, const char *message) {
    json_object *o = envelope(id, false);
    json_object *e = json_object_new_object();
    put(e, "code", json_object_new_string(code));
    put(e, "message", json_object_new_string(message));
    put(o, "error", e);
    send(o);
}
json_object *snapshot(float keyboardX, float keyboardY) {
    Global *g = Global::getInstance();
    json_object *s = json_object_new_object();
    const char *modes[] = {"game", "menu", "level_over", "hero_dead"};
    put(s, "schema_version", json_object_new_int(1));
    put(s, "mode", json_object_new_string(modes[g->gameMode]));
    put(s, "paused", json_object_new_boolean(g->game_pause));
    put(s, "game_frame", json_object_new_int(g->gameFrame));
    put(s, "level", json_object_new_int(g->gameLevel));
    put(s, "speed_adjustment", json_object_new_double(g->speedAdj));
    json_object *h = json_object_new_object();
    put(h, "position", vec(g->hero->pos, 3));
    float keyboard[] = {keyboardX, keyboardY};
    put(h, "keyboard_motion", vec(keyboard, 2));
    put(h, "lives_counter", json_object_new_int(g->hero->getLives()));
    put(h, "score", json_object_new_double(g->hero->getScore()));
    put(h, "damage", json_object_new_double(g->hero->getDamage()));
    put(h, "shields", json_object_new_double(g->hero->getShields()));
    put(h, "visible", json_object_new_boolean(g->hero->isVisible()));
    json_object *ammo = json_object_new_array();
    for(int i = 0; i < NUM_HERO_AMMO_TYPES; ++i)
        json_object_array_add(ammo, json_object_new_double(g->hero->getAmmoStock(i)));
    put(h, "ammo_stock", ammo);
    put(s, "player", h);
    json_object *enemies = json_object_new_array();
    for(const EnemyAircraft *e = g->enemyFleet->firstForSnapshot(); e; e = e->nextForSnapshot()) {
        json_object *item = json_object_new_object();
        put(item, "type", json_object_new_int(e->type));
        put(item, "position", vec(e->pos, 3));
        put(item, "raw_velocity", vec(e->vel, 3));
        put(item, "size", vec(e->size, 2));
        put(item, "damage", json_object_new_double(e->damage));
        json_object_array_add(enemies, item);
    }
    put(s, "enemies", enemies);
    return s;
}
bool process(const std::string &line, float &x, float &y,
             SnapshotBridge::TickFunction tick, void *context) {
    json_tokener *parser = json_tokener_new_ex(16);
    json_tokener_set_flags(parser, JSON_TOKENER_STRICT | JSON_TOKENER_VALIDATE_UTF8);
    json_object *request = json_tokener_parse_ex(parser, line.c_str(), line.size());
    bool valid = json_tokener_get_error(parser) == json_tokener_success;
    size_t end = json_tokener_get_parse_end(parser);
    while(end < line.size() && (line[end] == ' ' || line[end] == '\r' || line[end] == '\t')) ++end;
    valid = valid && end == line.size() && json_object_is_type(request, json_type_object);
    json_tokener_free(parser);
    if(!valid) {
        if(request) json_object_put(request);
        error(0, "invalid_json", "Expected one complete JSON object per line.");
        return false;
    }
    json_object *idObject = NULL, *version = NULL, *command = NULL;
    json_object_object_get_ex(request, "request_id", &idObject);
    json_object_object_get_ex(request, "protocol_version", &version);
    json_object_object_get_ex(request, "command", &command);
    int64_t id = json_object_is_type(idObject, json_type_int) ? json_object_get_int64(idObject) : 0;
    if(id <= lastId || id > 2147483647 || !json_object_is_type(version, json_type_int)
        || json_object_get_int64(version) != 1 || !json_object_is_type(command, json_type_string)) {
        error(id, "invalid_request", "Need version 1, increasing positive int32 ID and string command.");
        json_object_put(request);
        return false;
    }
    lastId = id;
    const char *cmd = json_object_get_string(command);
    // Embedded NULs must not turn a different command into an accepted prefix.
    if(std::strlen(cmd) != static_cast<size_t>(json_object_get_string_len(command))) {
        error(id, "invalid_request", "Command contains NUL.");
        json_object_put(request);
        return false;
    }
    json_object *result = NULL;
    bool close = false;
    if(std::strcmp(cmd, "hello") == 0) {
        result = json_object_new_object();
        put(result, "implementation", json_object_new_string("chromium-bsu-rl/sync-gui-v1"));
        put(result, "upstream_version", json_object_new_string("0.9.16.1"));
        put(result, "schema_version", json_object_new_int(1));
        put(result, "live_snapshot", json_object_new_boolean(true));
        put(result, "step", json_object_new_boolean(syncMode));
        put(result, "reset", json_object_new_boolean(false));
        put(result, "headless", json_object_new_boolean(false));
        put(result, "deterministic", json_object_new_boolean(false));
    } else if(std::strcmp(cmd, "snapshot") == 0) {
        result = snapshot(x, y);
    } else if(std::strcmp(cmd, "step") == 0 && syncMode && tick) {
        json_object *actionObject = NULL, *ticksObject = NULL;
        json_object_object_get_ex(request, "action", &actionObject);
        json_object_object_get_ex(request, "ticks", &ticksObject);
        int64_t action = json_object_get_int64(actionObject);
        int64_t ticks = json_object_get_int64(ticksObject);
        if(!json_object_is_type(actionObject, json_type_int) || action < 0 || action > 17
            || !json_object_is_type(ticksObject, json_type_int) || ticks < 1 || ticks > 50) {
            error(id, "invalid_action", "action must be integer 0..17; ticks must be integer 1..50.");
        } else if(Global::gameMode != Global::Game) {
            error(id, "episode_ended", "Single-level episode ended; open a new synchronous client.");
        } else {
            // Screen coordinates: up is negative y. No OS key repeat events.
            const int directions[9][2] = {{0,0},{0,-1},{0,1},{-1,0},{1,0},
                                         {-1,-1},{1,-1},{-1,1},{1,1}};
            int actual = 0;
            for(; actual < ticks && Global::gameMode == Global::Game; ++actual) {
                if(!tick(directions[action % 9][0], directions[action % 9][1], action >= 9, context)) {
                    json_object_put(request);
                    return true;
                }
                ++episodeTick;
            }
            result = json_object_new_object();
            put(result, "snapshot", snapshot(x, y));
            put(result, "actual_ticks", json_object_new_int(actual));
            put(result, "episode_tick", json_object_new_int64(episodeTick));
            put(result, "simulated_seconds", json_object_new_double(episodeTick * 0.02));
            put(result, "terminated", json_object_new_boolean(Global::gameMode != Global::Game));
        }
    } else if(std::strcmp(cmd, "close") == 0) {
        result = json_object_new_object();
        close = true;
    } else {
        error(id, "unsupported_command", "Use hello/snapshot/close; step requires synchronous mode.");
    }
    if(result) {
        json_object *response = envelope(id, true);
        put(response, "result", result);
        send(response);
    }
    json_object_put(request);
    return close;
}
}

bool SnapshotBridge::initialize() {
    const char *enabled = std::getenv("CHROMIUM_BSU_RL_PROTOCOL");
    if(!enabled || std::strcmp(enabled, "1") != 0) return true;
    const char *control = std::getenv("CHROMIUM_BSU_RL_SYNCHRONOUS");
    syncMode = control && std::strcmp(control, "1") == 0;
    const char *state = std::getenv("CHROMIUM_BSU_RL_STATE_DIR");
    if(!state || !*state || std::strlen(state) >= 180) {
        std::fprintf(stderr, "Protocol mode requires an isolated short state directory.\n");
        return false;
    }
    std::signal(SIGPIPE, SIG_IGN);
    int fd = dup(STDOUT_FILENO);
    if(fd < 0) return false;
    protocol = fdopen(fd, "w");
    if(!protocol) { close(fd); return false; }
    // Preserve a private response channel; all legacy stdout writes become logs.
    if(dup2(STDERR_FILENO, STDOUT_FILENO) < 0) return false;
    int flags = fcntl(STDIN_FILENO, F_GETFL);
    return flags >= 0 && fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK) >= 0;
}

bool SnapshotBridge::synchronous() { return syncMode; }

bool SnapshotBridge::pump(float &x, float &y, TickFunction tick, void *context) {
    if(!protocol) return false;
    char buffer[4096];
    ssize_t n = read(STDIN_FILENO, buffer, sizeof(buffer));
    if(n == 0) return true; // Parent pipe closed: do not leave an orphan window.
    if(n < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR) return true;
    if(n > 0) pending.append(buffer, n);
    for(int count = 0; count < 8; ++count) {
        size_t newline = pending.find('\n');
        if(newline == std::string::npos) break;
        if(newline > maxRequest) { error(0, "request_too_large", "Request exceeds 8192 bytes."); return true; }
        std::string line = pending.substr(0, newline);
        pending.erase(0, newline + 1);
        if(process(line, x, y, tick, context) || failed) return true;
    }
    if(pending.size() > maxRequest) { error(0, "request_too_large", "Request exceeds 8192 bytes."); return true; }
    return failed;
}
