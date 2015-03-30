#! -*- coding: utf8 -*-

from colorama import Fore


def _print(color, txt):
    print color + txt, Fore.RESET


def red(txt):
    _print(Fore.RED, txt)


def green(txt):
    _print(Fore.GREEN, txt)


def confirm(txt):
    ok = raw_input('==> ' + Fore.GREEN + '%s?[y/Y] :' % txt + Fore.RESET)
    if ok.lower() in ('y', 'yes'):
        return True

    return False


def alert(txt):
    red(txt)
