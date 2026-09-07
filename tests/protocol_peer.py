"""Isolated fault-injection peer for transport tests; never launches the game."""
import json
import sys
import time

mode = sys.argv[1]
for line in sys.stdin:
    request = json.loads(line)
    if mode == "eof":
        break
    if mode == "timeout":
        time.sleep(10)
        break
    if mode == "malformed":
        print("not json", flush=True)
        continue
    if mode == "large":
        print("x" * (1024 * 1024 + 1), flush=True)
        continue
    response = {"protocol_version": 1, "request_id": request["request_id"], "ok": True, "result": {}}
    if mode == "wrong_id":
        response["request_id"] = 999
    if request["command"] == "bad":
        response.update(ok=False, error={"code": "unsupported", "message": "test rejection"})
    sys.stderr.write("diagnostic log must not contaminate stdout\n")
    print(json.dumps(response), flush=True)
    if request["command"] == "close":
        break
