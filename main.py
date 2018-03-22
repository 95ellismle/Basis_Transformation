# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from src import IO as io
from src import text as txt_lib
from src import math_objects as MO

#import sympy as sp  # Use this to print things prettyily eventually (maybe to simplify certain bits too)
import sys
#import os

class Transform(object):
    
    def __init__(self, equation_in):
        steps_taken = ""
        begin_eq = "\n"
        end_eq = "\n"
        math_objs = MO.MATH_OBJECTS(equation_in, steps_taken, begin_eq, end_eq)
        print(math_objs.latex())

transform_path = io.folder_correct("./To_Transform")
transform_txt  = io.open_read(transform_path)
transform_txt = txt_lib.clean_eq(transform_txt)

if not len(transform_txt):
    print("Can't find any text")
    sys.exit()

Transform("\sum{_k \delta_{jk}}")


#tex_folderpath = io.folder_correct('./steps')
#tex_filepath = tex_folderpath + "steps.tex"
#
#io.open_write(tex_filepath, MO.steps_taken)
#latex_cmd = "pdflatex --output-directory='%s'"%tex_folderpath
#os.system("%s %s"%(latex_cmd, tex_filepath))
#
#unneeded_tex = ['.aux','.log']
#del_files = [tex_folderpath+i for i in os.listdir(tex_folderpath) if any(j in i for j in unneeded_tex)]
#for i in del_files:
#    os.remove(i)
