"""Set the Steam Workshop tags on Imperial Fragmentation.

steamcmd's workshop_build_item cannot set tags, so this calls ISteamUGC::SetItemTags directly
through Valve's original steam_api64 from the CK3 install (SDK 1.44/1.45 flat API,
STEAMUGC_INTERFACE_VERSION012). The Steam client must be running and logged in as the item owner.

Only tags change. Files, description, and preview are left alone.
Tag names must match CK3's Workshop tags exactly ("Balance " has a trailing space on Steam).
"""
import ctypes as C
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

APP_ID = 1158310
ROOT = Path(__file__).resolve().parent.parent
FILE_ID = int((ROOT / "publishedfileid.txt").read_text().split()[0])
TAGS = ["Gameplay", "Balance ", "Decisions", "Events", "Warfare", "1.21 'Florin'"]
CHANGENOTE = "Added Workshop tags."
VALVE_DLL = Path(r"E:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\steam_api64_o.dll")
UGC_VERSION = b"STEAMUGC_INTERFACE_VERSION012"
UTILS_VERSION = b"SteamUtils009"
SUBMIT_RESULT_CALLBACK = 3400 + 4


class StringArray(C.Structure):
    _fields_ = [("strings", C.POINTER(C.c_char_p)), ("count", C.c_int32)]


class SubmitResult(C.Structure):
    _fields_ = [("result", C.c_int32), ("needs_legal_agreement", C.c_bool), ("file_id", C.c_uint64)]


def die(msg):
    print("STOPPED:", msg)
    sys.exit(1)


def main():
    work = Path(tempfile.mkdtemp(prefix="ifrag_tags_"))
    shutil.copy2(VALVE_DLL, work / "steam_api64.dll")
    (work / "steam_appid.txt").write_text(str(APP_ID))
    os.chdir(work)
    api = C.CDLL(str(work / "steam_api64.dll"))

    api.SteamAPI_Init.restype = C.c_bool
    if not api.SteamAPI_Init():
        die("SteamAPI_Init failed. Is the Steam client running and logged in?")
    try:
        api.SteamClient.restype = C.c_void_p
        api.SteamAPI_GetHSteamUser.restype = C.c_int32
        api.SteamAPI_GetHSteamPipe.restype = C.c_int32
        client = api.SteamClient()
        user, pipe = api.SteamAPI_GetHSteamUser(), api.SteamAPI_GetHSteamPipe()
        if not client or not user or not pipe:
            die("no Steam client handles")

        # The flat GetISteamUGC wrapper returns NULL here; the internal accessor the SDK headers use works.
        f = api.SteamInternal_FindOrCreateUserInterface
        f.restype, f.argtypes = C.c_void_p, [C.c_int32, C.c_char_p]
        ugc = f(user, UGC_VERSION)
        f = api.SteamAPI_ISteamClient_GetISteamUtils
        f.restype, f.argtypes = C.c_void_p, [C.c_void_p, C.c_int32, C.c_char_p]
        utils = f(client, pipe, UTILS_VERSION)
        if not ugc or not utils:
            die("could not get ISteamUGC / ISteamUtils")

        start = api.SteamAPI_ISteamUGC_StartItemUpdate
        start.restype, start.argtypes = C.c_uint64, [C.c_void_p, C.c_uint32, C.c_uint64]
        handle = start(ugc, APP_ID, FILE_ID)
        if handle in (0, 0xFFFFFFFFFFFFFFFF):
            die(f"StartItemUpdate returned an invalid handle ({handle:#x})")

        arr = (C.c_char_p * len(TAGS))(*[t.encode("utf-8") for t in TAGS])
        tags = StringArray(arr, len(TAGS))
        set_tags = api.SteamAPI_ISteamUGC_SetItemTags
        set_tags.restype, set_tags.argtypes = C.c_bool, [C.c_void_p, C.c_uint64, C.POINTER(StringArray)]
        if not set_tags(ugc, handle, C.byref(tags)):
            die("SetItemTags was rejected")

        submit = api.SteamAPI_ISteamUGC_SubmitItemUpdate
        submit.restype, submit.argtypes = C.c_uint64, [C.c_void_p, C.c_uint64, C.c_char_p]
        call = submit(ugc, handle, CHANGENOTE.encode("utf-8"))
        if call == 0:
            die("SubmitItemUpdate did not start")

        done = api.SteamAPI_ISteamUtils_IsAPICallCompleted
        done.restype, done.argtypes = C.c_bool, [C.c_void_p, C.c_uint64, C.POINTER(C.c_bool)]
        get = api.SteamAPI_ISteamUtils_GetAPICallResult
        get.restype = C.c_bool
        get.argtypes = [C.c_void_p, C.c_uint64, C.c_void_p, C.c_int, C.c_int, C.POINTER(C.c_bool)]
        failed = C.c_bool(False)
        for _ in range(240):
            api.SteamAPI_RunCallbacks()
            if done(utils, call, C.byref(failed)):
                break
            time.sleep(0.25)
        else:
            die("timed out waiting for Steam")
        res = SubmitResult()
        if not get(utils, call, C.byref(res), C.sizeof(res), SUBMIT_RESULT_CALLBACK, C.byref(failed)) or failed.value:
            die("could not read the submit result")
        print("EResult", res.result, "(1 = OK)", "file", res.file_id, "needs legal agreement:", res.needs_legal_agreement)
        if res.result != 1:
            sys.exit(1)
        print("tags set:", TAGS)
    finally:
        api.SteamAPI_Shutdown()


if __name__ == "__main__":
    main()
