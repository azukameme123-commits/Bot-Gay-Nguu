# -*- coding: utf-8 -*-
import os, sys, time, shutil

_NC = os.environ.get('NO_COLOR') or not sys.stdout.isatty()

def _c(code):
    return '' if _NC else code

R  = _c('\033[0m');   B  = _c('\033[1m')
CY = _c('\033[36m');  GR = _c('\033[32m')
YL = _c('\033[33m');  RD = _c('\033[31m')
MG = _c('\033[35m');  DIM = _c('\033[2m')


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def width(default=76):
    try:
        return max(50, min(shutil.get_terminal_size().columns, 100))
    except Exception:
        return default


def banner():
    w = width()
    art = [
        "  __ __ _  _   __   __ _    ____  _  _  ____  ____  __   __ _ ",
        " (  |  ) )( ) / _\\ (  ( \\  (  _ \\/ )( \\(_  _)(_  _)/  \\ (  ( \\",
        "  )(/ (/ \\/ \\/    \\/    /   ) _ () \\/ (  )(    )( (  O )/    /",
        " (__)\\_)\\_)(_/\\_/\\_)\\_)__) (____/\\____/ (__)  (__) \\__/ \\_)__)",
    ]
    print(CY + B + '=' * w + R)
    for l in art:
        print(CY + l[:w] + R)
    print(MG + B + '   AOV  BUTTON  &  BANNER  MODDER'.center(w) + R)
    print(DIM + '   battleotherui graft engine  ·  FX + Joystick'.center(w) + R)
    print(CY + B + '=' * w + R)


def rule(ch='-'):
    print(DIM + ch * width() + R)


def bar(cur, total, label='', w=34):
    if total <= 0:
        total = 1
    cur = max(0, min(cur, total))
    fill = int(w * cur / total)
    pct = int(100 * cur / total)
    s = '%s[%s%s%s] %3d%% %s' % (GR, '#' * fill, DIM + '.' * (w - fill) + GR, R + GR, pct, label)
    sys.stdout.write('\r' + s + R + ' ' * 8)
    sys.stdout.flush()
    if cur >= total:
        sys.stdout.write('\n')
        sys.stdout.flush()


def clear_line():
    sys.stdout.write('\r' + ' ' * width() + '\r')
    sys.stdout.flush()


def done_line(text):
    clear_line()
    print(GR + B + text + R)


def ok(msg):
    print(GR + B + msg + R)


def err(msg):
    print(RD + B + msg + R)


def warn(msg):
    print(YL + msg + R)


def info(msg):
    print(DIM + msg + R)
