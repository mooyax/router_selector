#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
raspberry piのGPIOのダミープログラム。
raspberry pi以外でも動作するように、必要な関数をダミーで用意。
"""


BOARD = 1
OUT = 0
IN = 1
BCM = 2
RISING = 31
FALLING = 32
BOTH = 33

callbacks = {}


def setmode(a):
    """
    Set up numbering mode to use for channels.

    :param a: str
    :return:
    """
    print(a)


def setup(a, b):
    """
    Set up a GPIO channel or list of channels with a direction and (optional) pull/up down control.

    :param a: str
    :param b: str
    :return:
    """
    print(a, b)


def output(a, b):
    """
    Output to a GPIO channel or list of channels.

    :param a: str
    :param b: str
    :return:
    """
    print(a, b)


def input(a):
    """
    Input from a GPIO channel.  Returns HIGH=1=True or LOW=0=False.

    :param a: str
    :return:
    """
    print(a)
    return True


def cleanup():
    """
    Clean up by resetting all GPIO channels that have been used by this program to INPUT
    with no pullup/pulldown and no event detection.

    :return:
    """
    print('a')


def setwarnings(flag):
    """
    Enable or disable warning messages.

    :param flag: bool
    :return:
    """
    print(flag)


def add_event_detect(a, b, callback=None, bouncetime=300):
    """
    Enable edge detection events for a particular GPIO channel.

    :param a:
    :param b:
    :param callback:
    :param bouncetime:
    :return:
    """

    callbacks[a] = callback
    print(a, b, callback, bouncetime)
    return True


def event_detect(a):
    """
    test dummy event detect method.
    :param a:
    :return:
    """
    try:
        callback = callbacks[a]
        callback(a)
        print(callback)
    except:
        pass



