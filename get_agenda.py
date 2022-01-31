import math
import json
from collections import OrderedDict

def hour2floatTime(param1: int, param2: int) -> float:
    hour = param1
    _, tmin = divmod(param2, 60)
    minute = tmin / 60.0
    return hour + minute

def p2(l):
    if type(l) == type(0):
        l = str(l)
    # rajoute des zeros au debut d'une chaine jusqu'a ce qu'il y ait 2 caracteres
    return l.ljust(2, '0')


def lettre2bit(l):
    # retourne les 4 bits correspondant a une lettre
    corr = OrderedDict(
        [('a', '0000'), ('b', '0001'), ('c', '0010'), ('d', '0011'), ('e', '0100'), ('f', '0101'), ('g', '0110'),
         ('h', '0111'), ('i', '1000'), ('j', '1001'), ('k', '1010'), ('l', '1011'), ('m', '1100'), ('n', '1101'),
         ('o', '1110'), ('p', '1111')]);
    return corr[l];


def chaine2bits(c):
    # retourne une serie de bits correspondant a une chaine
    p = '';
    l = len(c);
    i = 0;
    while (i < l):
        p += lettre2bit(c[i]);
        i += 1;

    return p;


def agenda2form(agenda):
    # depuis un agenda, prepare le remplissage d'un formulaire
    # on met $h à zero. structure : $h[jour][matin ou aprem][debut ou fin][heure ou minute]
    i = 0
    h = []
    while (i < 7):
        h.append(i)
        h[i] = []
        j = 0
        while (j < 2):
            h[i].append(j)
            h[i][j] = []
            k = 0
            while (k < 2):
                h[i][j].append(k)
                h[i][j][k] = []
                l = 0
                while (l < 2):
                    h[i][j][k].append(l)
                    h[i][j][k][l] = 0
                    l += 1

                k += 1

            j += 1

        i += 1

    a = chaine2bits(agenda)
    p = [0] * 7
    l = len(a)
    i = 0
    while (i < l):
        if bool(int(a[i])) and i > 1 and not bool(int(a[i - 1])):
            h[math.floor(i / 96)][p[math.floor(i / 96)]][0][0] = math.floor(i % 96 / 4);
            # heure debut
            h[math.floor(i / 96)][p[math.floor(i / 96)]][0][1] = i % 4;
            # minute debut

        if not bool(int(a[i])) and i > 1 and bool(int(a[i - 1])):
            h[math.floor(i / 96)][p[math.floor(i / 96)]][1][0] = math.floor(i % 96 / 4);
            # heure fin
            h[math.floor(i / 96)][p[math.floor(i / 96)]][1][1] = i % 4;
            # minute fin
            p[math.floor(i / 96)] += 1;

        i += 1;

    return h;


def agenda2texteperline(agenda) -> list[tuple[int, tuple[float, float]]]:
    # depuis un agenda, genere textuellement la desc des horaires par jour ds un tab
    result = []
    i = 0
    t0 = []
    while (i < 2):
        j = 0
        t0.append(i)
        t0[i] = []
        while (j < 2):
            k = 0
            t0[i].append(j)
            t0[i][j] = []
            while (k < 2):
                t0[i][j].append(k)
                t0[i][j][k] = 0
                k += 1
            j += 1
        i += 1
    j = 0
    t1 = []
    while (j < 2):
        t1.append(j)
        t1[j] = []
        k = 0
        while (k < 2):
            t1[j].append(k)
            t1[j][k] = 0
            k += 1
        j += 1

    if (',' not in agenda):
        # format aaaaaaaaaaaaaa
        h = agenda2form(agenda)
        cd = 15
    else:
        # format json
        agenda = json.loads(agenda)
        h = agenda[0]
        cd = 5

    i = 0
    while (i < 7):
        if (h[i] != t0):
            s = (hour2floatTime(int(h[i][0][0][0]), int(p2(h[i][0][0][1] * cd))),
                hour2floatTime(int(h[i][0][1][0]), int(p2(h[i][0][1][1] * cd))))
            result.append((i, s))
            if (h[i][1] != t1):
                s = (hour2floatTime(int(h[i][1][0][0]), int(p2(h[i][1][0][1] * cd))),
                    hour2floatTime(int(h[i][1][1][0]), int(p2(h[i][1][1][1] * cd))))
                result.append((i, s))
        i += 1

    return result


#print(agenda2texteperline(
#    '[[[[[7,0],[16,0]],[[20,0],[23,9]]],[[[18,0],[23,9]],[[0,0],[0,0]]],[[[7,0],[9,0]],[[20,0],[23,9]]],[[[20,0],[23,9]],[[0,0],[0,0]]],[[[7,0],[23,9]],[[0,0],[0,0]]],[[[7,0],[23,9]],[[0,0],[0,0]]],[[[7,0],[23,9]],[[0,0],[0,0]]]],[[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]]],[[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]]],[[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]],[[[0,0],[0,0]],[[0,0],[0,0]]]]]'));