# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from src import IO as io
from src import text as txt_lib
from src import EXCEPT as EXC

#import sympy as sp  # Use this to print things prettyily eventually (maybe to simplify certain bits too)
import numpy as np
import sys

class MATH_OBJECTS(object):
    """ Contains all the math objects found within the input text.
      The base class for all the other objects. """

    def __init__(self, txt):
        self.txt = txt
        self.objs, self.combinators,self.obj_typ = self._find_math_objects(txt)
        self._combine_coeff_conjs()

    # Finds the outer layer of math objects
    def _find_math_objects(self, txt):
        objects = []
        combinators = []
        object_types = []
        count = 0
        while (txt.find("{") != -1 and txt.find("}") != -1):
            obj_txt, obj_type, start_ind, end_ind = self._find_first_enclosed_object(txt)
            obj = valid_math_objects[obj_type](obj_txt)
            combinator = txt[:start_ind]
            if combinator == "{" or combinator == "}":
                combinator = ""
            if count > 1:
                combinators.append(combinator.replace(combinators[count-1], ""))
            else:
                combinators.append(combinator)
            object_types.append(obj_type)
            objects.append(obj)
            txt = txt[:start_ind]+txt[end_ind:]
            count += 1
        return objects,combinators, object_types

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

    # Simplifies an occurance of a repeated coefficient to a power.
    def _combine_coeff_conjs(self):
        need_to_merge = self._find_the_same_objs(["\\coeff"])
        for i in need_to_merge:
            old_obj = self.objs[need_to_merge[i][0]]
            name = old_obj.name
            ind  = old_obj.inds
            deps = ','.join(old_obj.deps)
            if deps:
                deps = "[%s]"%deps
            diab = ['!diab!', '!adiab!'][old_obj.a_or_d == 'a']
            new_obj_txt = "{|%s|^{2}_{%s}%s %s}"%(name,ind[0], deps, diab)
            self._insert_obj(need_to_merge[i][0], COEFF(new_obj_txt), "\\coeff")
            [self._remove_obj(j+1) for j in need_to_merge[i][::-1]]

    # Finds all objects that are the same in the list of math objects
    def _find_the_same_objs(self, allowed_type):
        a_or_d = [self.objs[i].a_or_d for i in range(len(self.objs)) if self.obj_typ[i] in allowed_type]
        conjs  = [self.objs[i].conj   for i in range(len(self.objs)) if self.obj_typ[i] in allowed_type]
        names  = [self.objs[i].name   for i in range(len(self.objs)) if self.obj_typ[i] in allowed_type]
        inds   = [self.objs[i].inds   for i in range(len(self.objs)) if self.obj_typ[i] in allowed_type]
        need_to_merge = {}
        count = 0
        used_vals = []
        for i in range(len(names)):
            for j in range(len(names)):
                if i != j and i not in used_vals and j not in used_vals:
                    if names[i] == names[j] and inds[i] == inds[j]:
                        if conjs[i] != conjs[j] and a_or_d[i] == a_or_d[j]:
                            need_to_merge[count] = sorted((i,j))
                            used_vals.append(i)
                            used_vals.append(j)
                            count += 1

        return need_to_merge

    # Inserts a new object in combinators, obj_typ and objs
    def _insert_obj(self, i, obj, obj_typ, comb=""):
        self.obj_typ.insert(i,obj_typ)
        self.objs.insert(i, obj)
        self.combinators.insert(i, comb)

    # Removes an object from combinators, obj_typ and objs
    def _remove_obj(self, i):
        self.combinators.remove(self.combinators[i])
        self.objs.remove(self.objs[i])
        self.obj_typ.remove(self.obj_typ[i])

    # Converts bra-ket pair with the same name to a dirac delta (Assuming orthogonality)
    def _find_deltas(self):
        maxlen = len(self.obj_typ)
        for i in range(1,len(self.obj_typ)):
          if i < maxlen:
            if self.obj_typ[i-1]+self.combinators[i]+ self.obj_typ[i] == "\\bra\\ket":
              if self.objs[i-1].name == self.objs[i].name:
                if self.objs[i-1].a_or_d == self.objs[i].a_or_d:
                  if len(self.objs[i-1].inds) == 1 and len(self.objs[i-1].inds) == 1:
                      new_delta_obj = DELTA("\\delta{_{%s,%s} }"%(self.objs[i-1].inds[0],self.objs[i].inds[0]))
                      self._insert_obj(i, new_delta_obj, "\\delta")
                      self._remove_obj(i-1)
                      self._remove_obj(i)
                      maxlen -= 1

    # Converts the math object to latex code
    def latex(self):
        latex_str = self.objs[0].latex()
        for i in range(1,len(self.combinators)):
            latex_str += self.combinators[i]
            latex_str += self.objs[i].latex()
        return latex_str.replace("||", "|")


class SUM(MATH_OBJECTS):
    " Stores info on any summations "

    def __init__(self, txt):
        self.inds, self.txt = self._find_index(txt)
        self.objs, self.combinators,self.obj_typ = self._find_math_objects(self.txt)
        self._simplify_delta()

    # If any dirac deltas are in the sum then simplify the expression
    def _simplify_delta(self):
        self._find_deltas()
        if "\\delta" in self.obj_typ:
            delta_I = self.obj_typ.index("\\delta")
            delta_inds = self.objs[delta_I].inds
            # Both the dirac delta's indices must be in the summation
            if not all(j in self.inds for j in delta_inds):
                return
            # Won't currently work if other parent math objects are inside.
            # This is because it won't recursively change things, lower down.
            if any(i not in child_math_objects for i in self.obj_typ):
                EXC.WARN("Sorry I currently can't cancel the dirac delta in the sum %s"%self.latex())
                return
            # Finds the relevant math objects
            relevant_objs = [] # Holds all objects that have relevant indices
            for i, Typ in enumerate(self.obj_typ):
                if Typ in child_math_objects:
                    if any(j in delta_inds for j in self.objs[i].inds) and "\\delta" not in Typ:
                        relevant_objs.append(self.objs[i])
            # Change any occurance of the first delta index to the second delta index
            self.inds = list(set([i.replace(delta_inds[1], delta_inds[0]) for i in  self.inds]))
            for obj in relevant_objs:
                if delta_inds[1] in obj.inds:
                    obj.inds = [i.replace(delta_inds[1], delta_inds[0]) for i in obj.inds]
            # Remove the delta from the sum
            self.obj_typ = self.obj_typ[:delta_I] + self.obj_typ[delta_I+1:]
            self.combinators = self.combinators[:delta_I] + self.combinators[delta_I+1:]
            self.objs = self.objs[:delta_I] + self.objs[delta_I+1:]
            self._combine_coeff_conjs()
        else:
            return

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
    def latex(self):
        inds = ','.join(self.inds)
        left_bracket  = ""
        right_bracket = ""
        if any(i in self.combinators for i in ('+','-')):
            left_bracket = "\\left["
            right_bracket = "\\right]"
        latex_str = "\\sum\\limits_{%s} %s %s "%(inds, left_bracket, self.objs[0].latex())
        for i in range(1,len(self.combinators)):
            latex_str += self.combinators[i]
            latex_str += self.objs[i].latex()
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

    # Finds the name of a variable
    def _find_var_name(self, txt):
        end_of_name_possibils = ('_','[','}','^','!')
        end_of_name_index = min([txt.find(i) for i in end_of_name_possibils if txt.find(i) != -1])
        name = txt[1:end_of_name_index]
        return name

    # Finds the index of a coefficients or bra/ket
    def _find_adiab_or_diab(self, txt):
        if "psi" in txt:
            return "a"
        if "phi" in txt:
            return "d"
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
    def latex(self):
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

    # Converts diabatic bras to adiabatic
    def _diab_2_adiab(self):
        pass

class KET(BRA):
    " Stores info on kets "

    def __init__(self, txt):
        BRA.__init__(self, txt)
        self.txt = txt

    # Converts the math object to latex code
    def latex(self):
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
        self.conj = self._find_conj(txt)
        self.pow = int(self._find_powers(txt))
        
    # Converts the math object to latex code
    def latex(self):
        deps = ','.join(self.deps)
        inds = ','.join(self.inds)
        latex_str = " %s"%self.name
        if self.pow > 1:
            latex_str += "^{%s}"%self.pow
        if inds:
            latex_str += "_{%s}"%(inds)
        if deps and latex_with_deps:
            latex_str += "(%s)"%(deps)
        if self.conj:
            latex_str += "^{*}"
        return latex_str

    # Finds whether the coefficient should be treated as the conjugate
    def _find_conj(self, txt):
        if "*" in txt:
            return True
        else:
            return False
        
    # Finds the index of a coefficients or bra/ket
    def _find_adiab_or_diab(self, txt):
        if "c" in txt.lower():
            return "a"
        if "u" in txt.lower():
            return "d"
        else:
            EXC.ERROR("I don't know whether %s is diabatic or adiabatic!"%txt)

    # Finds any powers
    def _find_powers(self, txt):
        if txt.find('^') == -1:
            return 1
        txt = txt[txt.find('^'):]
        if txt[1] != '{':
            end_ind = 2
            index = txt[1]
        else:
            end_ind = txt.find('}')
            index = txt[txt.find('{')+1:end_ind]
        return index

    # Converts adiabatic bras to diabatic
    def _adiab_2_diab(self):
        if len(self.inds) > 1:
            EXC.ERROR("More than 1 index on the bra %s"%self.txt)
        ind = self.inds[0]
        trans_txt = "{_X \\coeff{u_{X}[R,t]} \\U{_{%s,X}} }"%ind
        return SUM(trans_txt)
        #C_l = \sum\limits_{m}u_m U_{lm}

    # Converts diabatic coeffs to adiabatic
    def _diab_2_adiab(self):
        pass

class DELTA(BRA):
    """ A Dirac delta object """

    def __init__(self, txt):
        self.txt = txt
        self.inds = self._find_index(txt)[0]

    def latex(self):
        inds = ",".join(self.inds)
        return "\\delta_{%s}"%inds

class U(COEFF):
    """ A Dirac delta object """

    def __init__(self, txt):
        self.txt = txt
        self.inds = self._find_index(txt)[0]
        self.conj = self._find_conj(txt)
        if self.conj:
            self.bra, self.ket = self._create_bra_ket_conj(self.inds)
        else:
            self.bra, self.ket = self._create_bra_ket(self.inds)
    
    # Creates the Bra and the Ket as part of the U matrix
    def _create_bra_ket(self, inds):
        if len(inds) != 2:
            EXC.ERROR("The number of indices for the U matrix, %s, is %i it should be 2!"%(self.txt, len(inds)))
        bra = BRA("{\phi_{%s}[R,t]}"%(inds[0]))
        ket = KET("{\psi_{%s}[R,t]}"%(inds[1]))
        return bra,ket
    
    # Creates the Bra and the Ket as part of the U matrix
    def _create_bra_ket_conj(self, inds):
        if len(inds) != 2:
            EXC.ERROR("The number of indices for the U matrix, %s, is %i it should be 2!"%(self.txt, len(inds)))
        bra = BRA("{\psi_{%s}[R,t]}"%(inds[1]))
        ket = KET("{\phi_{%s}[R,t]}"%(inds[0]))
        return bra,ket
    
    # Creates a string with LaTeX code for this object
    def latex(self):
        inds = ",".join(self.inds)
        return "U_{%s}"%inds

latex_with_deps = False

valid_math_objects = {'\\sum':SUM,'\\coeff':COEFF,'\\ket':KET,'\\bra':BRA, "\\delta":DELTA, "\\U":U}
child_math_objects = {'\\coeff':COEFF,'\\ket':KET,'\\bra':BRA, "\\delta":DELTA, "\\U":U}

transform_path = io.folder_correct("./To_Transform")
transform_txt  = io.open_read(transform_path)
transform_txt = txt_lib.clean_eq(transform_txt)

if not len(transform_txt):
    print("Can't find any text")
    sys.exit()
    
math_objs = MATH_OBJECTS(transform_txt)
print("\n",math_objs.latex())
