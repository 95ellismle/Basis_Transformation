1#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  5 20:43:53 2018

@author: oem
"""

import os 

from src import EXCEPT as EXC

# Checks if a filepath or folderpath exists
def path_leads_somewhere(path):
    if os.path.isfile(path) or os.path.isdir(path):
        return True
    else:
        return False

#Checks if the directory exists and makes it if not
def check_mkdir(path, max_depth=2):
    path = folder_correct(path)
    lpath = path.split('/')
    act_folders = []
    for i in range(2,len(lpath)):
        sub_path = '/'.join(lpath[:i])
        if not path_leads_somewhere(sub_path):
            act_folders.append(False)
        else:
            act_folders.append(True)
    if not all(act_folders[:-max_depth]):
        EXC.ERROR("Too many folders need to be created please check the filepaths, or increase the amount of folder I am allowed to create (check_mkdir).")
    else:
        for i in range(2,len(lpath)+1):
            sub_path = '/'.join(lpath[:i])
            if not os.path.isdir(sub_path) and '.' not in sub_path[sub_path.rfind('/'):]:
               os.mkdir(sub_path)
    return True

# Returns an absolute file/folder path. Will convert the relative file/folerpaths such as ../foo -> $PATH_TO_PYTHON_MINUS_1/foo
def folder_correct(f, make_file=False):
    f = os.path.expanduser(f)
    f = f.replace("//",'/')
    folder = os.path.isdir(f)
    if '/' not in f:
        f = './'+f
    flist = f.split('/')
    clist = os.getcwd().split('/')
    if flist[0] != clist[0] and flist[1] != clist[1]:
        cind, find = 0, 0
        for i in flist:
            if i == '..':
                cind += 1
                find += 1
            if i == '.':
                find += 1
        if cind != 0:
            clist = clist[:-cind]
        flist = flist[find:]
    else:
        clist = []
    if flist[-1] != '' and folder or (not path_leads_somewhere('/'.join(clist+flist)) and '.' not in f[f.rfind('/'):]):
        flist.append('')
    f= '/'.join(clist+flist)
    if make_file:
        if not path_leads_somewhere(f):
            if folder or '.' not in f[f.rfind('/'):]:
                check_mkdir(f)
            else:
                if not path_leads_somewhere(f[:f.rfind('/')]):
                    check_mkdir(f[:f.rfind('/')])
                File = open(f, 'a+')
                File.close()
        return f
    else:
        return f
    
# Opens and write a string to a file
def open_write(filename, message, mkdir=False, type_open='w+'):
    folder_correct(filename, mkdir)
    if not path_leads_somewhere:
        f = open(filename, 'w+')
    else:
        f = open(filename, type_open)
    f.write(message)
    f.close()

# Reads a file and closes it
def open_read(filename, throw_error=True):
    filename = folder_correct(filename)
    if path_leads_somewhere(filename):
        f = open(filename, 'r')
        txt = f.read()
        f.close()
        return txt
    else:
        if throw_error:
            EXC.ERROR("The %s file doesn't exist!"%filename)
        return False