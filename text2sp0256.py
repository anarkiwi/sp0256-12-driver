#!/usr/bin/env python

import re
import sys
from functools import cache

# Based on rules extracted from https://github.com/GmEsoft/CTS256A-AL2

ALLOPHONES = {
    "PA1": 0,
    "PA2": 1,
    "PA3": 2,
    "PA4": 3,
    "PA5": 4,
    "OY": 5,
    "AY": 6,
    "EH": 7,
    "KK3": 8,
    "PP": 9,
    "JH": 10,
    "NN1": 11,
    "IH": 12,
    "TT2": 13,
    "RR1": 14,
    "AX": 15,
    "MM": 16,
    "TT1": 17,
    "DH1": 18,
    "IY": 19,
    "EY": 20,
    "DD1": 21,
    "UW1": 22,
    "AO": 23,
    "AA": 24,
    "YY2": 25,
    "AE": 26,
    "HH1": 27,
    "BB1": 28,
    "TH": 29,
    "UH": 30,
    "UW2": 31,
    "AW": 32,
    "DD2": 33,
    "GG3": 34,
    "VV": 35,
    "GG1": 36,
    "SH": 37,
    "ZH": 38,
    "RR2": 39,
    "FF": 40,
    "KK2": 41,
    "KK1": 42,
    "ZZ": 43,
    "NG": 44,
    "LL": 45,
    "WW": 46,
    "XR": 47,
    "WH": 48,
    "YY1": 49,
    "CH": 50,
    "ER1": 51,
    "ER2": 52,
    "OW": 53,
    "DH2": 54,
    "SS": 55,
    "NN2": 56,
    "HH2": 57,
    "OR": 58,
    "AR": 59,
    "YR": 60,
    "GG2": 61,
    "EL": 62,
    "BB2": 63,
}

META_RULE_TABLE = {
    "#": r"[AEIOU]+",  # 09  one or more vowels
    ".": r"[BDGJLMNRVWX]+",  # . 0A  voiced consonant: B D G J L M N R V W X
    "%": r"(ER|E|ES|ED|ING|ELY)",  # % 0B  suffix: ER E ES ED ING ELY (FUL?)
    "&": r"(S|C|G|Z|X|J|CH|SH)",  # & 0C  sibilant: S C G Z X J CH SH
    "@": r"(T|S|R|D|L|Z|N|J|TH|CH|SH)",  # @ 0D  T S R D L Z N J TH CH SH preceding long U
    "^": r"(B|C|D|F|G|H|J|K|L|M|N|P|Q|R|S|T|V|W|X|Y|Z)",  # ^ 0E  one consonant
    "+": r"(E|I|Y)",  # + 0F  front vowel: E I Y
    ":": r"(B|C|D|F|G|H|J|K|L|M|N|P|Q|R|S|T|V|W|X|Y|Z)*",  # : 10  zero or more consonants
    "*": r"(B|C|D|F|G|H|J|K|L|M|N|P|Q|R|S|T|V|W|X|Y|Z)+",  # * 11  one or more consonants
    ">": r"(O|U)",  # > 12  back vowel: O U
    "<": r"[^A-Z]",  # < 13  anything other than a letter
    "?": r"[AEIOU]{2,}",  # ? 14  two or more vowels
    # $ 1F  Not a pattern symbol, ignored by the ROM
    # Should probably be a D: [I]D% = [AY] instead of [I]$% = [AY]
}

RULE_TABLE = {
    "-": [("", "-", "", ["PA1"])],
    "'": [
        (".", "'S", "", ["ZZ"]),
        ("#:.E", "'S", "", ["ZZ"]),
        ("#", "'S", "", ["ZZ"]),
        ("", "'S", "", ["SS"]),
        ("", "'", "", []),
    ],
    ",": [("", ",", "", ["PA4"])],
    ";": [("", ";", "", ["PA4"])],
    " ": [("", " ", "", ["PA2"])],
    ".": [("", ".", "", ["PA5", "PA5"])],
    "!": [("", "!", "", ["PA5", "PA5"])],
    "?": [("", "?", "", ["PA5", "PA5"])],
    ":": [("", ":", "", ["PA5"])],
    "%": [("", "%", "", ["PP", "ER2", "SS", "SS", "EH", "NN1", "TT2", "PA1"])],
    "$": [("", "$", "", ["DD2", "AA", "LL", "ER1", "ZZ", "PA1"])],
    "#": [("", "#", "", ["NN2", "AX", "MM", "BB1", "ER1", "PA1"])],
    "A": [
        ("<", "A", "<", ["EY"]),
        ("", "ACHE", "", ["EY", "PA3", "KK2"]),
        ("", "A", "<", ["AX"]),
        ("<", "ARE", "<", ["AR"]),
        ("^", "AS", "#", ["EY", "SS"]),
        ("<", "AR", "O", ["AX", "RR2"]),
        ("<", "A", "^R", ["AX"]),
        ("", "AR", "#", ["XR"]),
        ("<:", "ANY", "", ["EH", "NN1", "IY"]),
        ("", "AGAIN", "", ["AX", "PA2", "GG1", "EH", "EH", "NN1"]),
        ("", "A", "WA", ["AX"]),
        ("", "AW", "", ["AO", "AO"]),
        ("<:", "A", "^+<", ["EY"]),
        ("<", "A", "^#", ["AX"]),
        ("", "A", "^+#", ["EY"]),
        ("#:", "ALLY", "", ["AX", "LL", "IY"]),
        ("<", "AL", "#", ["AX", "LL"]),
        ("#:", "AG", "E", ["IH", "PA2", "JH"]),
        ("", "A", "^%", ["EY"]),
        ("", "A", "^+:#", ["AE"]),
        ("<", "ARR", "", ["AX", "RR2"]),
        ("", "ARR", "", ["AE", "RR2"]),
        ("<:", "AR", "<", ["AR"]),
        ("", "AR", "<", ["ER1"]),
        ("", "AR", "", ["AR"]),
        ("", "AIR", "", ["EH", "XR"]),
        ("", "AI", "", ["EY"]),
        ("", "AY", "", ["EY"]),
        ("", "AU", "", ["AO"]),
        ("#:", "AL", "<", ["EL"]),
        ("#:", "ALS", "<", ["EL", "ZZ"]),
        ("", "ALK", "", ["AO", "PA3", "KK2"]),
        ("", "A", "L^", ["AO"]),
        ("<:", "ABLE", "", ["EY", "PA2", "BB2", "EL"]),
        ("", "ABLE", "", ["AX", "PA2", "BB2", "EL"]),
        ("", "ANG", "+", ["EY", "NN1", "PA2", "JH"]),
        ("", "A", "", ["AE"]),
    ],
    "B": [
        ("<", "B", "<", ["PA2", "BB2", "IY"]),
        ("MAY", "BE", "", ["BB2", "IY"]),
        ("<", "BE", "^#", ["PA2", "BB2", "IY"]),
        ("<", "BEEN", "<", ["BB2", "IH", "NN1"]),
        ("<", "BOTH", "<", ["PA2", "BB2", "OW", "TH"]),
        ("<", "BUS", "#", ["PA2", "BB2", "IH", "ZZ"]),
        ("", "BUIL", "", ["PA2", "BB2", "IH", "IH", "LL"]),
        ("", "B", "B", []),
        ("", "B", "<", ["PA2", "BB1"]),
        ("", "B", "S", ["PA2", "BB1"]),
        ("", "BT", "", ["PA3", "TT2"]),
        ("<", "B", "^", ["PA2", "BB1"]),
        ("", "B", "", ["PA2", "BB2"]),
    ],
    "C": [
        ("<", "C", "<", ["SS", "SS", "IY"]),
        ("<", "CH", "^", ["PA3", "KK1"]),
        ("^E", "CH", "", ["PA3", "KK1"]),
        ("", "CH", "", ["PA3", "CH"]),
        ("S", "CI", "#", ["SS", "SS", "AY"]),
        ("", "CI", "#", ["SH"]),
        ("", "CI", "O", ["SH"]),
        ("", "CI", "EN", ["SH"]),
        ("", "C", "+", ["SS", "SS"]),
        ("C", "C", "", []),
        ("", "CK", "#", ["PA3", "KK1"]),
        ("", "CK", "", ["PA3", "KK2"]),
        ("", "COM", "%", ["PA3", "KK3", "AX", "MM"]),
        ("", "CC", "+", ["PA3", "KK1", "SS", "SS"]),
        ("", "C", "<", ["PA3", "KK2"]),
        ("", "C", "S", ["PA3", "KK2"]),
        ("", "C", ">", ["PA3", "KK3"]),
        ("", "C", "", ["PA3", "KK1"]),
    ],
    "D": [
        ("<", "D", "<", ["PA2", "DD2", "IY"]),
        ("", "D", "D", []),
        ("#:", "DED", "<", ["PA2", "DD2", "IH", "PA2", "DD1"]),
        (".E", "D", "<", ["PA2", "DD1"]),
        ("#*E", "D", "<", ["PA3", "TT2"]),
        ("<", "DE", "^#", ["PA2", "DD2", "IH"]),
        ("<", "DO", "<", ["PA2", "DD2", "UW2"]),
        ("<", "DOES", "", ["PA2", "DD2", "AX", "ZZ"]),
        ("<", "DOING", "", ["PA2", "DD2", "UW2", "IH", "NG"]),
        ("<", "DOW", "", ["PA2", "DD2", "AW"]),
        ("#", "DU", ":A", ["PA2", "JH", "UW1"]),
        ("", "DG", "", ["PA2", "JH"]),
        ("", "DJ", "", ["PA2", "JH"]),
        ("", "D", "<", ["PA2", "DD1"]),
        ("", "D", "S", ["PA2", "DD1"]),
        ("", "D", "", ["PA2", "DD2"]),
    ],
    "E": [
        ("<", "E", "<", ["IY"]),
        ("#:", "E", "<", []),
        ("'*", "E", "<", []),
        ("*", "E", "<", ["IY"]),
        ("#", "ED", "<", ["PA2", "DD1"]),
        ("#:", "E", "D<", []),
        ("", "EV", "ER", ["EH", "VV"]),
        ("#*", "EL", "", ["EL"]),
        ("", "ERI", "#", ["YR", "IY"]),
        ("#:", "ER", "#", ["ER1"]),
        ("", "E", "^%", ["IY"]),
        ("", "ERI", "", ["EH", "EH", "RR1", "IH"]),
        ("", "ER", "#", ["EH", "XR"]),
        ("", "ER", "", ["ER1"]),
        ("<", "EVEN", "<", ["IY", "VV", "IH", "NN1"]),
        ("<", "EVEN", "", ["IY", "VV", "EH", "EH", "NN1"]),
        ("#:", "EW", "", ["YY1", "UW2"]),
        ("@", "EW", "", ["UW2"]),
        ("", "EW", "", ["YY1", "UW2"]),
        ("", "E", "O", ["IY"]),
        ("#:&", "ES", "<", ["IH", "ZZ"]),
        ("#:", "E", "S<", []),
        ("#:", "ELY", "<", ["LL", "IY"]),
        ("#:", "EMENT", "", ["MM", "IH", "NN1", "PA3", "TT2"]),
        ("", "EFUL", "", ["FF", "UH", "LL"]),
        ("", "EER", "", ["YR"]),
        ("", "EE", "", ["IY"]),
        ("", "EARN", "", ["ER2", "NN1"]),
        ("<", "EAR", "^", ["ER2"]),
        ("*", "EAR", "", ["YR"]),
        ("", "EAD", "", ["EH", "EH", "PA2", "DD1"]),
        ("#:", "EA", "<", ["IY", "AX"]),
        ("", "EA", "SU", ["EH"]),
        ("", "EA", "", ["IY"]),
        ("", "EIGH", "", ["EY"]),
        ("", "EI", "", ["IY"]),
        ("<", "EYE", "", ["AY"]),
        ("", "EY", "", ["IY"]),
        ("", "EU", "", ["UW1"]),
        ("", "E", "", ["EH"]),
    ],
    "F": [
        ("<", "F", "<", ["EH", "EH", "FF"]),
        ("", "FU", "L", ["FF", "UH"]),
        ("", "F", "F", []),
        ("", "FOUR", "", ["FF", "OR"]),
        ("", "F", "", ["FF"]),
    ],
    "G": [
        ("<", "G", "<", ["PA2", "JH", "IY"]),
        ("", "GIV", "", ["PA2", "GG1", "IH", "VV"]),
        ("<", "G", "I^", ["PA2", "GG1"]),
        ("", "GE", "T", ["PA2", "GG1", "EH"]),
        ("SU", "GGES", "", ["PA2", "GG2", "PA2", "JH", "EH", "EH", "SS"]),
        ("", "GG", "", ["PA2", "GG1"]),
        ("", "GREAT", "", ["PA2", "GG3", "RR2", "EY", "TT2"]),
        ("", "G", "<", ["PA2", "GG3"]),
        ("<B#", "G", "", ["PA2", "GG2"]),
        ("", "G", "+", ["PA2", "JH"]),
        ("#", "GH", "", ["FF"]),
        ("", "GH", "", ["PA2", "GG2"]),
        ("", "G", "", ["PA2", "GG2"]),
    ],
    "H": [
        ("<", "H", "<", ["EY", "PA3", "CH"]),
        ("<", "HAV", "", ["HH1", "AE", "VV"]),
        ("<", "HERE", "", ["HH1", "YR"]),
        ("<", "HOUR", "", ["AW", "ER1"]),
        ("", "HOW", "", ["HH1", "AW"]),
        ("", "HYP", "", ["HH1", "IH", "PA3", "PP"]),
        ("", "H", ">", ["HH2"]),
        ("", "H", "#", ["HH1"]),
        ("", "H", "", []),
    ],
    "I": [
        ("<", "IN", "", ["IH", "NN1"]),
        ("N", "I", "NE", ["AY"]),
        ("", "I", "<", ["AY"]),
        ("", "IN", "D", ["AY", "NN1"]),
        ("<:", "I", "%", ["AY"]),
        ("<:", "IED", "<", ["AY", "PA2", "DD1"]),
        ("#*", "IED", "<", ["IY", "PA2", "DD1"]),
        ("FR", "IE", "ND", ["EH"]),
        ("", "IEN", "", ["IY", "IH", "NN1"]),
        ("", "IE", "T", ["AY", "IH"]),
        ("", "IER", "", ["IY", "ER1"]),
        ("", "I", "%", ["IY"]),
        ("", "IE", "", ["IY"]),
        ("", "IN", "%", ["IY", "NN1"]),
        ("", "IR", "#", ["AY", "ER1"]),
        ("", "I", "^%", ["AY"]),
        ("", "I", "^+:#", ["IH"]),
        ("", "IZ", "%", ["AY", "ZZ"]),
        ("", "IS", "%", ["AY", "ZZ"]),
        ("[I]$% = [AY]\t\t; Maybe ", "I", "D%", ["AY"]),
        ("+^", "I", "^+", ["IH"]),
        ("", "I", "T%", ["AY"]),
        ("#*", "I", "^+", ["IH"]),
        ("", "IR", "", ["ER2"]),
        ("*", "I", "ON", ["YY1"]),
        ("", "IGH", "", ["AY"]),
        ("", "ILD", "", ["AY", "EL", "PA2", "DD1"]),
        ("", "IGN", "", ["AY", "NN1"]),
        ("", "IGN", "^", ["AY", "NN1"]),
        ("", "IGN", "%", ["AY", "NN1"]),
        ("", "IQUE", "", ["IY", "PA3", "KK2"]),
        ("", "I", "A", ["AY"]),
        ("M", "I", "C", ["AY"]),
        ("", "I", "", ["IH"]),
    ],
    "J": [("<", "J", "<", ["PA2", "JH", "EY"]), ("", "J", "", ["PA2", "JH"])],
    "K": [
        ("<", "K", "<", ["PA3", "KK1", "EY"]),
        ("<", "K", "N", []),
        ("", "K", "<", ["PA3", "KK2"]),
        ("", "K", "", ["PA3", "KK1"]),
    ],
    "L": [
        ("<", "L", "<", ["EH", "EH", "LL"]),
        ("", "LO", "C#", ["LL", "OW"]),
        ("", "L", "L", []),
        ("", "L", "%", ["EL"]),
        ("", "LEAD", "", ["LL", "IY", "PA2", "DD1"]),
        ("", "LAUGH", "", ["LL", "AE", "FF"]),
        ("", "L", "", ["LL"]),
    ],
    "M": [
        ("", "MB", "", ["MM"]),
        ("<", "M", "<", ["EH", "EH", "MM"]),
        ("", "MOV", "", ["MM", "UW2", "VV"]),
        ("", "M", "M", []),
        ("", "M", "", ["MM"]),
    ],
    "N": [
        ("<", "N", "<", ["EH", "EH", "NN1"]),
        ("E", "NG", "+", ["NN1", "PA2", "JH"]),
        ("", "NG", "R", ["NG", "PA2", "GG1"]),
        ("", "NG", "#", ["NG", "PA2", "GG1"]),
        ("", "NGL", "%", ["NG", "PA2", "GG1", "EL"]),
        ("", "NG", "", ["NG"]),
        ("", "NK", "<", ["NG", "PA3", "KK2"]),
        ("", "NK", "S", ["NG", "PA3", "KK2"]),
        ("", "NK", "", ["NG", "PA3", "KK1"]),
        ("<", "NOW", "<", ["NN2", "AW"]),
        ("", "N", "N", []),
        ("#:", "NU", "", ["NN1", "YY1", "UW1"]),
        ("<", "N", "", ["NN2"]),
        ("", "N'T", "", ["NN1", "PA3", "TT2"]),
        ("", "N", "", ["NN1"]),
    ],
    "O": [
        ("<", "O", "<", ["OW"]),
        ("", "OF", "<", ["AX", "VV"]),
        ("", "OROUGH", "", ["AX", "AX", "RR2", "OW"]),
        ("#:", "OR", "<", ["ER1"]),
        ("#:", "ORS", "<", ["ER1", "ZZ"]),
        ("", "OR", "", ["OR"]),
        ("<", "ONE", "", ["WW", "AX", "NN1"]),
        ("+", "ONE", "", ["WW", "AX", "NN1"]),
        ("*", "OW", "N", ["AW"]),
        ("", "OW", "", ["OW"]),
        ("<", "OVER", "", ["OW", "VV", "ER1"]),
        ("", "OV", "", ["AX", "VV"]),
        ("", "O", "^%", ["OW"]),
        ("", "O", "^EN", ["OW"]),
        ("", "O", "^I#", ["OW"]),
        ("", "OL", "D", ["OW", "LL"]),
        ("", "OUGHT", "", ["AO", "AO", "PA3", "TT2"]),
        ("", "OUGH", "", ["AX", "AX", "FF"]),
        ("&", "OUR", "", ["OR"]),
        (":", "OUR", "", ["AW", "ER1"]),
        ("<", "OU", "", ["AW"]),
        (":", "OU", "S#", ["AW"]),
        ("", "OUS", "", ["AX", "SS"]),
        ("", "OULD", "", ["UH", "PA2", "DD1"]),
        ("^", "OU", "^L", ["AX"]),
        ("", "OUP", "", ["UW2", "PA3", "PP"]),
        ("", "OU", "", ["AW"]),
        ("", "OY", "", ["OY"]),
        ("", "OING", "", ["OW", "IH", "NG"]),
        ("", "OI", "", ["OY"]),
        ("", "OOR", "", ["OR"]),
        ("", "OOK", "<", ["UH", "PA3", "KK2"]),
        ("", "OOK", "S", ["UH", "PA3", "KK2"]),
        ("", "OOK", "", ["UH", "PA3", "KK1"]),
        ("", "OOD", "<", ["UH", "PA2", "DD1"]),
        ("", "OO", "D", ["UH"]),
        ("", "OO", "", ["UW2"]),
        ("", "O", "E", ["OW"]),
        ("", "O", "<", ["OW"]),
        ("", "OAR", "", ["OR"]),
        ("", "OA", "", ["OW"]),
        ("<", "ONLY", "", ["OW", "NN1", "LL", "IY"]),
        ("<", "ONCE", "", ["WW", "AX", "NN1", "SS"]),
        ("", "ON'T", "", ["OW", "NN1", "PA3", "TT2"]),
        ("C", "O", "N", ["AX"]),
        ("", "O", "NG", ["AO"]),
        ("<*", "O", "N", ["AX"]),
        ("I", "ON", "", ["AX", "NN1"]),
        ("#:", "ON", "<", ["AX", "NN1"]),
        ("", "O", "ST<", ["OW"]),
        ("", "OF", "^", ["AO", "FF"]),
        ("", "OTHER", "", ["AX", "DH2", "ER1"]),
        ("", "OSS", "<", ["AO", "AO", "SS", "SS"]),
        ("#*", "OM", "", ["AX", "MM"]),
        ("", "O", "", ["AA"]),
    ],
    "P": [
        ("", "PSYCH", "", ["SS", "SS", "AY", "PA2", "KK1"]),
        ("<", "P", "<", ["PA3", "PP", "IY"]),
        ("", "PH", "", ["FF"]),
        ("", "PEOP", "", ["PA3", "PP", "IY", "PA3", "PP"]),
        ("", "POW", "", ["PA3", "PP", "AW"]),
        ("", "PUT", "<", ["PA3", "PP", "UH", "PA3", "TT2"]),
        ("", "P", "P", []),
        ("", "P", "", ["PA3", "PP"]),
    ],
    "Q": [
        ("<", "Q", "<", ["PA3", "KK1", "YY1", "UW2"]),
        ("", "QUAR", "", ["PA3", "KK3", "WH", "AA"]),
        ("", "QUE", "<", ["PA3", "KK1", "YY1", "UW2"]),
        ("", "QU", "", ["PA3", "KK3", "WH"]),
        ("", "Q", "", ["PA3", "KK3"]),
    ],
    "R": [
        ("<", "R", "<", ["AR"]),
        ("<", "RE", "^#", ["RR1", "IY"]),
        ("", "RH", "", ["RR1"]),
        ("", "R", "R", []),
        ("*", "R", "", ["RR2"]),
        ("", "R", "", ["RR1"]),
    ],
    "S": [
        ("<", "S", "<", ["EH", "EH", "SS", "SS"]),
        ("", "SH", "", ["SH"]),
        ("#", "SION", "", ["ZH", "AX", "NN1"]),
        ("", "SOME", "", ["SS", "AX", "MM"]),
        ("#", "SUR", "#", ["ZH", "ER1"]),
        ("", "SUR", "#", ["SH", "ER1"]),
        ("#", "SU", "#", ["ZH", "UW1"]),
        ("#", "SSU", "#", ["SH", "UW1"]),
        ("#", "SED", "<", ["ZZ", "PA2", "DD1"]),
        ("#", "S", "#", ["ZZ"]),
        ("", "SAID", "", ["SS", "SS", "EH", "EH", "PA2", "DD1"]),
        ("^", "SION", "", ["SH", "AX", "NN1"]),
        ("", "S", "S", []),
        (".", "S", "<", ["ZZ"]),
        ("#:.E", "S", "<", ["ZZ"]),
        ("#*?", "S", "<", ["ZZ"]),
        ("#*#", "S", "<", ["SS"]),
        ("U", "S", "<", ["SS"]),
        ("<:#", "S", "<", ["ZZ"]),
        ("<", "SCH", "", ["SS", "SS", "PA3", "KK2"]),
        ("", "S", "C+", []),
        ("#", "SM", "", ["ZZ", "MM"]),
        ("#", "S", "N'", ["ZZ"]),
        ("", "S", "<", ["SS"]),
        ("", "S", "", ["SS", "SS"]),
    ],
    "T": [
        ("", "T", "'S", ["PA3", "TT1"]),
        ("", "TCH", "", ["PA3", "CH"]),
        ("<", "T", "<", ["PA3", "TT2", "IY"]),
        ("<", "THE", "<#", ["DH1", "IY"]),
        ("<", "THE", "<", ["DH1", "AX"]),
        ("", "TO", "<", ["PA3", "TT2", "UW2"]),
        ("", "TODAY", "", ["PA3", "TT2", "UW2", "DD2", "EY"]),
        ("", "THA", "^<", ["DH1", "AE"]),
        ("<", "THIS", "<", ["DH1", "IH", "SS", "SS"]),
        ("<", "THEY", "", ["DH1", "EY"]),
        ("<", "THERE", "", ["DH1", "XR"]),
        ("<", "THER", "", ["TH", "ER1"]),
        ("", "THER", "", ["DH2", "ER1"]),
        ("", "THEIR", "", ["DH1", "XR"]),
        ("<", "THEM", ":", ["DH1", "EH", "MM"]),
        ("", "THESE", "<", ["DH1", "IY", "ZZ"]),
        ("<", "THEN", "", ["DH1", "EH", "NN1"]),
        ("", "THROUGH", "<", ["TH", "RR2", "UW2"]),
        ("", "THOSE", "", ["DH1", "OW", "SS"]),
        ("", "THOUGH", "<", ["DH1", "OW"]),
        ("<", "THUS", "", ["DH1", "AX", "SS", "SS"]),
        ("", "THE", "<", ["DH1"]),
        ("", "TH", "", ["TH"]),
        ("#:", "TED", "<", ["PA3", "TT2", "IH", "PA2", "DD1"]),
        ("S", "TI", "#N", ["PA3", "CH"]),
        ("", "TI", "O", ["SH"]),
        ("", "TI", "A", ["SH"]),
        ("", "TIEN", "", ["SH", "AX", "NN1"]),
        ("", "TUR", "#", ["PA3", "CH", "ER1"]),
        ("", "TU", "A", ["PA3", "CH", "UW1"]),
        ("<", "TWO", "", ["PA3", "TT2", "UW2"]),
        ("", "T", "T", []),
        ("", "T", "S", ["PA3", "TT1"]),
        ("", "T", "", ["PA3", "TT2"]),
    ],
    "U": [
        ("<", "U", "<", ["YY1", "UW2"]),
        ("", "UN", "I", ["YY2", "UW1", "NN1"]),
        ("<", "UN", "", ["AX", "NN1"]),
        ("<", "UPON", "", ["AX", "PA3", "PP", "AA", "NN1"]),
        ("@", "UR", "#", ["UW1", "ER1"]),
        ("", "UR", "#", ["YY1", "UW1", "ER1"]),
        ("", "UR", "*", ["ER1"]),
        ("", "U", "^<", ["AX"]),
        ("", "U", "^^", ["AX"]),
        ("", "UY", "", ["AY"]),
        ("<G", "U", "#", []),
        ("G", "U", "%", []),
        ("G", "U", "#", ["WW"]),
        ("@", "U", "", ["UW2"]),
        ("", "U", "", ["YY1", "UW1"]),
    ],
    "V": [
        ("<", "V", "<", ["VV", "IY"]),
        ("", "VIEW", "", ["VV", "YY1", "UW2"]),
        ("", "V", "", ["VV"]),
    ],
    "W": [
        ("<", "W", "<", ["PA2", "DD2", "AX", "PA2", "BB2", "EL", "YY1", "UW1"]),
        ("<", "WERE", "", ["WW", "ER2"]),
        ("<", "WAS", "<", ["WW", "AX", "ZZ"]),
        ("", "WA", "S", ["WW", "AA"]),
        ("", "WA", "T", ["WW", "AO", "AO"]),
        ("", "WAN", "", ["WW", "AA", "NN1"]),
        ("", "WHERE", "", ["WH", "XR"]),
        ("", "WHAT", "", ["WH", "AA", "PA3", "TT2"]),
        ("", "WHOL", "", ["HH2", "OW", "LL"]),
        ("", "WHO", "", ["HH2", "UW2"]),
        ("", "WO", "M", ["WW", "AX"]),
        ("", "WH", "", ["WH"]),
        ("", "WAR", "", ["WW", "OR"]),
        ("", "WOR", "^", ["WW", "ER1"]),
        ("", "WR", "", ["RR1"]),
        ("", "W", "", ["WW"]),
    ],
    "X": [
        ("<", "X", "<", ["EH", "PA3", "KK2", "SS"]),
        ("<", "X", "", ["ZZ"]),
        ("", "X", "", ["PA3", "KK2", "SS"]),
    ],
    "Y": [
        ("", "YOUR", "", ["YY2", "OR"]),
        ("<", "Y", "<", ["WW", "AY"]),
        ("", "YOUNG", "", ["YY2", "AX", "NG"]),
        ("<", "YOU", "", ["YY2", "UW2"]),
        ("", "YEAR", ":", ["YY2", "YR"]),
        ("<", "YES", "", ["YY2", "EH", "SS", "SS"]),
        ("<", "Y", "", ["YY2"]),
        ("#*", "Y", "<", ["IY"]),
        ("#*", "Y", "I", ["IY"]),
        ("<:", "Y", "<", ["AY"]),
        ("<:", "Y", "#", ["AY"]),
        ("<:", "Y", "^+:#", ["IH"]),
        ("<:", "Y", "^#", ["AY"]),
        ("", "Y", "", ["IH"]),
    ],
    "Z": [("<", "Z", "<", ["ZZ", "IY"]), ("", "Z", "Z", []), ("", "Z", "", ["ZZ"])],
    "0": [("", "0", "", ["ZZ", "YR", "OW"])],
    "1": [("", "1", "", ["WW", "AX", "AX", "NN1"])],
    "2": [("", "2", "", ["PA3", "TT2", "UW2"])],
    "3": [("", "3", "", ["TH", "RR1", "IY"])],
    "4": [("", "4", "", ["FF", "OR"])],
    "5": [("", "5", "", ["FF", "AY", "VV"])],
    "6": [("", "6", "", ["SS", "SS", "IH", "PA3", "KK2", "SS"])],
    "7": [("", "7", "", ["SS", "SS", "EH", "VV", "IH", "NN1"])],
    "8": [("", "8", "", ["EY", "PA3", "TT2"])],
    "9": [("", "9", "", ["NN2", "AY", "NN1"])],
}


@cache
def expand_meta_rule(rule):
    return "".join([META_RULE_TABLE.get(i, i) for i in rule])


class Text2sp0256:
    def __init__(self):
        self.RULES = {}
        for section, rules in RULE_TABLE.items():
            self.RULES[section] = []
            for a_rules, b_rules, c_rules, allophones in rules:
                if a_rules:
                    a_rules = re.compile(expand_meta_rule(a_rules) + r"$")
                else:
                    a_rules = None
                if c_rules:
                    c_rules = re.compile(r"^" + expand_meta_rule(c_rules))
                else:
                    c_rules = None
                self.RULES[section].append((a_rules, b_rules, c_rules, allophones))

    def translate(self, input_str):
        pos = 0
        output = []

        while pos < len(input_str):
            rules = self.RULES[input_str[pos]]
            pos_allophones = None
            for a_rules, b_rules, c_rules, allophones in rules:
                if not input_str[pos:].startswith(b_rules):
                    continue
                if a_rules:
                    if not a_rules.match(input_str[:pos]):
                        continue
                if c_rules:
                    if not c_rules.match(input_str[pos + len(b_rules) :]):
                        continue
                pos_allophones = allophones
                pos += len(b_rules)
                break
            if pos_allophones is None:
                raise ValueError
            output.extend(pos_allophones)
        output.append("PA3")
        return output


translator = Text2sp0256()
input_str = " ".join([line.upper().strip() for line in sys.stdin])
translated = bytes([ALLOPHONES[b] for b in translator.translate(input_str)])
sys.stdout.buffer.write(translated)
sys.stdout.flush()
