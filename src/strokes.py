#!/usr/bin/env python3
"""Draw strokes with the real pointer via XTEST. usage: strokes.py strokes.json winx winy window_id
strokes.json: [[[x,y],...],...] in window-local pixels."""
import ctypes, json, sys, time
X = ctypes.CDLL("libX11.so.6"); T = ctypes.CDLL("libXtst.so.6")
X.XOpenDisplay.restype = ctypes.c_void_p
d = ctypes.c_void_p(X.XOpenDisplay(None))
if not d: sys.exit("no display")
ox, oy = (int(sys.argv[2]), int(sys.argv[3])) 
WIN = int(sys.argv[4])
class CM(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("serial", ctypes.c_ulong), ("send_event", ctypes.c_int),
                ("display", ctypes.c_void_p), ("window", ctypes.c_ulong), ("message_type", ctypes.c_ulong),
                ("format", ctypes.c_int), ("data", ctypes.c_long * 5), ("pad", ctypes.c_long * 12)]
X.XInternAtom.restype = ctypes.c_ulong; X.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
X.XDefaultRootWindow.restype = ctypes.c_ulong; X.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
X.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long, ctypes.c_void_p]
ev = CM(); ev.type = 33; ev.send_event = 1; ev.window = WIN
ev.message_type = X.XInternAtom(d, b"_NET_ACTIVE_WINDOW", 0); ev.format = 32
ev.data[0] = 2; ev.data[1] = 0; ev.data[2] = 0
X.XSendEvent(d, X.XDefaultRootWindow(d), 0, (1 << 20) | (1 << 19), ctypes.byref(ev)); X.XFlush(d); time.sleep(0.5)
def mv(x, y):
    T.XTestFakeMotionEvent(d, -1, int(round(x + ox)), int(round(y + oy)), 0); X.XFlush(d)
def btn(p):
    T.XTestFakeButtonEvent(d, 1, 1 if p else 0, 0); X.XFlush(d)
X.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
KC = [X.XKeysymToKeycode(d, k) for k in (0xffe3, 0xffe1, 0x61)]
def deselect():
    for kc in KC: T.XTestFakeKeyEvent(d, kc, 1, 0); X.XFlush(d); time.sleep(0.02)
    for kc in reversed(KC): T.XTestFakeKeyEvent(d, kc, 0, 0); X.XFlush(d); time.sleep(0.02)
for s in json.load(open(sys.argv[1])):
    mv(*s[0]); time.sleep(0.08)
    btn(True); time.sleep(0.06)
    for p in s[1:]:
        mv(*p); time.sleep(0.012)
    time.sleep(0.06); btn(False); time.sleep(0.2); deselect(); time.sleep(0.08)
X.XCloseDisplay(d)
