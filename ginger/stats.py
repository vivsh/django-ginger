from __future__ import division
import math


__all__ = ["divide", "mean", "sum"]


def divide(num, denom):
    return num/denom if denom != 0 else 0


def mean(iterable):
    result = 0
    total = 0
    for value in iterable:
        if value is None:
            continue
        result += value
        total += 1
    return divide(result, total)


def sum(iterable):
    result = 0
    for value in iterable:
        if value is None:
            continue
        result += value
    return result