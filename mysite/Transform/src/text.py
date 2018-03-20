#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  5 21:27:27 2018

@author: oem
"""

# Removes any comments from some text
def comment_remove(string, cmt_str='#'):
    x = [i for i in string.split('\n') if i]
    x = [i for i in x if i[0] != cmt_str]
    x = [i[:i.find(cmt_str)] if i.find(cmt_str) != -1 else i for i in x ]
    string = '\n'.join(x)
    return string
   
# Standardises the txt and removes any unecessary information
def clean_eq(txt):
    txt = comment_remove(txt)
    txt = txt.replace("\n", "")
    txt = txt.replace(" ","")
    return txt