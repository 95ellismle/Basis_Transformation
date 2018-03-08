# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from src import IO as io
from src import text as txt_lib
from src import EXCEPT as EXC

import sympy as sp


class MATH_OBJECTS(object):
    """ Contains all the math objects found within the input text.
      The base class for all the other objects. """

    def __init__(self, txt):
        self.txt = txt
        self.objs,self.combinators = self._find_math_objects(txt)
        self.latex = self._to_latex()

    # Finds the outer layer of math objects
    def _find_math_objects(self, txt):
        objects = []
        combinators = []
        count = 0
        while (txt.find("{") != -1 and txt.find("}") != -1):
            obj_txt, obj_type, start_ind, end_ind = self._find_first_enclosed_object(txt)
            obj = valid_math_objects[obj_type](obj_txt)
            combinator = txt[:start_ind]
            if count > 1:
                combinators.append(combinator.replace(combinators[count-1], ""))
            else:
                combinators.append(combinator)
            objects.append(obj)
            txt = txt[:start_ind]+txt[end_ind:]
            count += 1
        return objects,combinators

    # Finds the first valid math object that is enclosed by braces
    def _find_first_enclosed_object(self, txt):
        for i, letter in enumerate(txt):
            if letter == "{":
                up_to_txt = txt[:i]
                start_ind = up_to_txt.rfind('\\')
                obj = up_to_txt[start_ind:]
                if obj in valid_math_objects:
                    end_ind = self._find_matching_str(txt[i:], "{","}")+i
                    return txt[i:end_ind], obj, start_ind, end_ind

    # Finds the matching right string to go with the left one
    def _find_matching_str(self, txt, left_str, right_str):
        count2 = False
        count=0
        for i,letter in enumerate(txt):
            if letter == left_str:
                count += 1
                count2 = True
            if letter == right_str:
                count -= 1
            count = abs(count)
            if count == 0 and count2:
                return i+1
            
    # Converts the math object to latex code
    def _to_latex(self):
        latex_str = self.objs[0].latex
        for i in range(1,len(self.combinators)):
            latex_str += self.combinators[i]
            latex_str += self.objs[i].latex
        return latex_str.replace("||", "|")

class SUM(MATH_OBJECTS):
    " Stores info on any summations "

    def __init__(self, txt):
        self.inds, self.txt = self._find_index(txt)
        self.objs, self.combinators = self._find_math_objects(self.txt)
        self.latex = self._to_latex()
        
    # Finds the index of a coefficients or bra/ket
    def _find_index(self, txt):
        if txt.find('_') == -1:
            return []
        txt = txt[txt.find('_'):]
        if txt[1] != '{':
            end_ind = 2
            index = [txt[1]]
        else:
            end_ind = txt.find('}')
            index = txt[txt.find('{')+1:end_ind].split(',')
        return index, txt[end_ind:]
    
    # Converts the math object to latex code
    def _to_latex(self):
        inds = ','.join(self.inds)
        left_bracket  = ""
        right_bracket = ""
        if any(i in self.combinators for i in ('+','-')):
            left_bracket = "\\left["
            right_bracket = "\\right]"
        latex_str = "\\sum\\limits_{%s} %s %s "%(inds, left_bracket, self.objs[0].latex)
        for i in range(1,len(self.combinators)):
            latex_str += self.combinators[i]
            latex_str += self.objs[i].latex
        latex_str += right_bracket
        return latex_str

class BRA(SUM):
    " Stores info on bras"

    def __init__(self, txt):
        self.txt = txt
        self.a_or_d = self._find_adiab_or_diab(txt)
        self.name = self._find_var_name(txt)
        self.deps = self._find_dependencies(txt)
        self.inds = self._find_index(txt)[0]
        self.latex = self._to_latex()
        
    # Finds the name of a variable
    def _find_var_name(self, txt):
        end_of_name_possibils = ('_','[','}')
        end_of_name_index = min([txt.find(i) for i in end_of_name_possibils if txt.find(i) != -1])
        name = txt[1:end_of_name_index]
        return name

        # Finds the index of a coefficients or bra/ket
    def _find_adiab_or_diab(self, txt):
        if txt.count("!diab!") > 0:
            return "d"
        elif txt.count("!adiab!") > 0:
            return "a"
        else:
            EXC.ERROR("I don't know whether %s is diabatic or adiabatic!"%txt)

    # Finds the dependencies of terms
    def _find_dependencies(self, txt):
        dependencies = []
        if txt.find('[') != -1 and txt.find(']') != -1:
            txt = txt[txt.find('[')+1:txt.find(']')]
            [dependencies.append(i) for i in txt.split(',')]
        return dependencies

    # Converts the math object to latex code
    def _to_latex(self):
        name = self.name
        deps = ','.join(self.deps)
        inds = ','.join(self.inds)
        latex_str = "\\langle"
        if inds:
            latex_str += " %s_{%s}"%(name,inds)
        if deps and latex_with_deps:
            latex_str += "(%s)"%(deps)
        latex_str += "|"
        return latex_str
    
    # Converts adiabatic bras to diabatic
    def _adiab_2_diab(self):
        pass

    # Converts diabatic bras to adiabatic
    def _diab_2_adiab(self):
        pass
    
class KET(BRA):
    " Stores info on kets "

    def __init__(self, txt):
        BRA.__init__(self, txt)
        self.txt = txt
    
    # Converts the math object to latex code
    def _to_latex(self):
        name = self.name
        deps = ','.join(self.deps)
        inds = ','.join(self.inds)
        latex_str = "|"
        if inds:
            latex_str += "%s_{%s}"%(name,inds)
        if deps and latex_with_deps:
            latex_str += "(%s)"%(deps)
        latex_str += "\\rangle"
        return latex_str
    
    # Converts adiabatic kets to diabatic
    def _adiab_2_diab(self):
        pass

    # Converts diabatic kets to adiabatic
    def _diab_2_adiab(self):
        pass
        
class COEFF(BRA):
    " Stores info on the coefficients "

    def __init__(self, txt):
        BRA.__init__(self, txt)
        self.txt = txt

    # Converts the math object to latex code
    def _to_latex(self):
        deps = ','.join(self.deps)
        inds = ','.join(self.inds)
        latex_str = " %s"%self.name
        if inds:
            latex_str += "_{%s}"%(inds)
        if deps and latex_with_deps:
            latex_str += "(%s)"%(deps)
        return latex_str       
        
    # Converts adiabatic coeffs to diabatic
    def _adiab_2_diab(self):
        pass

    # Converts diabatic coeffs to adiabatic
    def _diab_2_adiab(self):
        pass


latex_with_deps = False

valid_math_objects = {'\\sum':SUM,'\\coeff':COEFF,'\\ket':KET,'\\bra':BRA}

transform_path = io.folder_correct("./To_Transform")
transform_txt  = io.open_read(transform_path)
transform_txt = txt_lib.clean_eq(transform_txt)


math_objs = MATH_OBJECTS(transform_txt)

print(math_objs.latex)
