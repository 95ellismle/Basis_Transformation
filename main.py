# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from src import IO as io
from src import text as txt_lib
from src import EXCEPT as EXC

#import sympy as sp  # Use this to print things prettyily eventually (maybe to simplify certain bits too)
import sys

steps_taken = ''
begin_eq = "\\begin{dmath*}\n"
end_eq   = "\n\\end{dmath*}"

class MATH_OBJECTS(object):
    """ Contains all the math objects found within the input text.
      The base class for all the other objects. """

    def __init__(self, txt):
        global steps_taken
        self.txt = txt
        self.child = False
        self.__name__ = self.__class__.__name__
        self.objs, self.combinators,self.obj_typ = self._find_math_objects(txt)
        steps_taken += "Original Equation was:\n\n%s%s%s]\n\n"%(begin_eq, self.latex(), end_eq)
        # Simplifying
        #self._combine_coeff_conjs()  #This needs work.
        self._merge_nested_sums()
        self._split_sums()
    
    # Will follow the path that is in the path dictionary and find the math object.
    def _follow_path(self, path):
        x = self.objs
        count = 0
        for i in path:
            if i < len(x):
                if x[i].child:
                    if count == len(path)-1:
                        return x[i]
                    else:
                        print("Can't find path %s, the path length is too long.\nThe chain of math objects isn't as long as the amount of indices in the path)"%path)
                else:
                    if count == len(path)-1:
                        return x[i]
                    x = x[i].objs
            else:
                print("Can't find path %s"%str(path))
                return False
            count += 1
            
    # Will recursively iterate over all objects in the self.objs list and find the parents and children.
    def _create_struct(self, lIst, obj_types, parent="root", level=0, struct={}, levels={0:0}, names={}):
        if len(lIst) != len(obj_types):
            EXC.WARN("%s._create_struct has a different number of objects and object types.\n\tobj_types = %s\n\tobjs = %s"%(self.__name__, str(obj_types), str(lIst)))
        for i, item in enumerate(lIst):
            if parent == "root":
                parent = self
            if levels.get(level) == None:
                levels[level] = 0
            if struct.get(level)  == None:
                struct[level] = []
                names[level] = []
            struct[level].append((item, parent))
            names[level].append(item.__name__)
            levels[level] += 1
            if obj_types[i] not in child_math_objects:
                new_list = item.objs
                self._create_struct(new_list, item.obj_typ, item, level+1,struct,levels, names)
        return struct, names

    # Will create a dictionary with the path to each object in the struct dictionary
    def _create_paths(self, lIst, parent_i=0, level=0, paths={}):
        for i, item in enumerate(lIst):
            if paths.get(level)  == None:
                paths[level] = []
            if level == 0:
                paths[0] = [[i] for i in range(len(self.objs))]  
            else:
                paths[level].append(paths[level-1][parent_i]+[i])
            if not item.child:
                new_list = item.objs
                self._create_paths(new_list, i, level+1, paths)
        return paths
    
    # Re-writes the parent summations with multiple child summations as multiple parent summations with 1 child.
    def _one_child_parent_sums(self):
        global steps_taken
        orig_latex = self.latex()
        self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ)    
        self.paths  = self._create_paths(self.objs)
        for level in self.struct:
            for i, (child,parent) in enumerate(self.struct[level]):
                if child.__name__ == "SUM":
                    if child.obj_typ.count("\\sum") > 1:
                        grandchildren_to_adopt = []
                        grandchildren_combinators = []
                        adopted_grandchildren_indices = []
                        for i, grandchlid in enumerate(child.objs):
                            if i != 0 and grandchlid.__name__ == "SUM":
                                grandchildren_to_adopt.append(grandchlid)
                                grandchildren_combinators.append(child.combinators[i])
                                adopted_grandchildren_indices.append(i)
                            else:
                                continue
                        for grandchild,comb,i in zip(grandchildren_to_adopt,grandchildren_combinators,adopted_grandchildren_indices):
                            new_sum = SUM("{_{%s}}"%(','.join(child.inds)))
                            new_sum.objs = [grandchild]
                            new_sum.obj_typ = ["\\sum"]
                            new_sum.combinators = [""]
                            parent._insert_obj(len(parent.objs)+1, new_sum, "\\sum", comb)
                        count = 0
                        for index in sorted(adopted_grandchildren_indices):
                            child._remove_obj(index-count)
                            count += 1    
        self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ, parent="root", level=0, struct={}, levels={0:0}, names={})    
        self.paths  = self._create_paths(self.objs, parent_i=0, level=0, paths={})
        if self.latex() != orig_latex:
            steps_taken += "Split the sums to create 1 child parent sum:\n\n%s%s%s]\n\n"%(begin_eq, self.latex(), end_eq)


    # Returns a list of lists containing items that are in between the indices provided
    def _divide_list(self, indices, list_in):
        if len(indices) > 0:
            list_out = [list_in[:indices[0]]]
            if len(indices) > 1:
                list_out += [list_in[indices[i-1]:indices[i]] for i in range(1,len(indices))]
            list_out += [list_in[indices[-1]:]]
            return list_out
        else:
            return [list_in]
    
    # Re-writes the parent summations with multiple child summations as multiple parent summations with 1 child.
    def _split_sums(self):
        global steps_taken
        orig_latex = self.latex()
        for level in self.struct:
            count = 0
            for i, (child,parent) in enumerate(self.struct[level]):
                if child.__name__ == "SUM":
                    instances_of_combs = [i for i,comb in enumerate(child.combinators) if any(comb == i for i in ['+','-'])]
                    new_objs  = self._divide_list(instances_of_combs, child.objs)
                    new_combs = self._divide_list(instances_of_combs, child.combinators)
                    for cI in range(len(new_combs)):
                        new_combs[cI][0] = ''
                    new_typs  = self._divide_list(instances_of_combs, child.obj_typ)
                    inds = child.inds
                    NEW_OBJS = {}
                    for objI in range(len(new_objs)):
                        NEW_OBJS[objI] = SUM("{_{%s} }"%",".join(inds))
                        NEW_OBJS[objI].objs = new_objs[objI]
                        NEW_OBJS[objI].combinators = new_combs[objI]
                        NEW_OBJS[objI].obj_typ = new_typs[objI]
                    for objI in NEW_OBJS:
                        count += 1
                        parent._insert_obj(len(parent.objs)+1, NEW_OBJS[objI], "\\sum", " + ")
            if count > 0:
                for i in range(0,len(parent.objs)-count):
                    parent._remove_obj(0)
        self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ, parent="root", level=0, struct={}, levels={0:0}, names={})    
        self.paths  = self._create_paths(self.objs, parent_i=0, level=0, paths={})
        self._simplify_U()
        if self.latex() != orig_latex:
            steps_taken += "Split the sums to create 1 child parent sum:\n\n%s%s%s]\n\n"%(begin_eq, self.latex(), end_eq)

    
    # Will remove any sums without any indices
    def _remove_empty_sums(self):
        for level in self.struct: 
          for i, (child,parent) in enumerate(self.struct[level]):
              if child.__name__ == "SUM":
                  if not child.inds:
                      for j in range(len(child.objs)):
                          parent._insert_obj(i+1, child.objs[j], child.obj_typ[j], child.combinators[j])
                      parent._remove_obj(i)
    
    # Will simplify the U transformation matricies by removing indices from the sum and making a dirac delta
    def _simplify_U(self):
       for level in self.struct: 
          for i, (child,parent) in enumerate(self.struct[level]):
              if child.__name__ == "SUM":
                can_simp, indices, U_places = child._can_simplify_U()
                if can_simp:
                    U_places = sorted(U_places)
                    count = 0
                    for X in U_places:
                        if len(X) != 2:
                           EXC.WARN("Something went wrong with the SUM._can_simplify_U() function. It is telling me I can simplify %i"%child.latex())
                           return False
                        sortX = sorted(X) 
                        delta_inds = [child.objs[u-count].inds[0] for u in sortX]
                        new_delta = DELTA("{_{%s}}"%",".join(delta_inds)) 
                        for x in sortX:
                           child._remove_obj(x-count)
                           count += 1
                        child._insert_obj(len(child.objs)+1, new_delta, "\\delta", "")
                        for ind in indices:
                            child.inds = [j for j in child.inds if j != ind]
                child._simplify_deltas()
       #self._remove_empty_sums()
                                
       self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ, parent="root", level=0, struct={}, levels={0:0}, names={})    
       self.paths  = self._create_paths(self.objs, parent_i=0, level=0, paths={})
       # * If sum indices are empty, remove sum:
       # * Use the function _simplify_deltas
        
    # Will combine nested sums into single sums with just 1 summation sign. This will  merge any parent sums into the child and the delete the parent.
    def _merge_nested_sums(self):
        self._one_child_parent_sums()
        level = 0
        add_level = True
        while (level <= max(self.struct.keys())):
            for i, (child,parent) in enumerate(self.struct[level]):
                if child.__name__ == "SUM" and child.__name__ == parent.__name__:
                    [child.inds.append(i) for i in parent.inds] # Merge the parent's indices with the child
                    self.objs[self.paths[level][i][-2]] = child # Replace the parent with the child
                    add_level = False
                    self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ, parent="root", level=0, struct={}, levels={0:0}, names={})    
                    self.paths  = self._create_paths(self.objs, parent_i=0, level=0, paths={})
            if add_level:
                level += 1
            else:
                level = 0
                add_level= True
                
    # Checks the text and sees whether it is the correct format (This need improving)
    def _check_txt(self, txt, obj_type):
        obj_type = obj_type[1:].title()
        if obj_type == "\\sum":
           tmp_txt = txt[txt.find('{'):]
           if "_" != tmp_txt[1]:
               EXC.WARN("Can't find any indices in the %s.\nTxt = %s"%(obj_type, txt))   

    # Finds all the math objects in the text from the valid_math_objects dict
    def _find_math_objects(self, txt):
        objects = []
        combinators = []
        object_types = []
        count = 0
        while (txt.find("{") != -1 and txt.find("}") != -1):
            obj_txt, obj_type, start_ind, end_ind = self._find_first_enclosed_object(txt)
            self._check_txt(txt, obj_type)
            obj = valid_math_objects[obj_type](obj_txt)
            combinator = txt[:start_ind]
            combinator.replace("{","") # This may need to be more rigorous I don't know. It is fine for now though.
            combinator.replace("}","")
            if count > 1:
                combinators.append(combinator)
            else:
                combinators.append(combinator)
            object_types.append(obj_type)
            objects.append(obj)
            txt = txt[:start_ind-len(combinator)]+txt[end_ind:]
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
        EXC.WARN("Couldn't find the enclosing brace, txt = %s"%txt)

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
        self.combinators = self.combinators[:i] + self.combinators[i+1:]
        self.objs = self.objs[:i] + self.objs[i+1:]
        self.obj_typ = self.obj_typ[:i] + self.obj_typ[i+1:]

    # Converts bra-ket pair with the same name to a dirac delta (Assuming orthogonal bases -which the adiabatic and quassi diabatic bases are)
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
            latex_str += "%s\n"%self.combinators[i].replace(" ", "")
            latex_str += self.objs[i].latex()
        return latex_str.replace("||", "|")


class SUM(MATH_OBJECTS):
    " Stores info on any summations "

    def __init__(self, txt):
        self.inds, self.txt = self._find_index(txt)
        self.child = False
        self.__name__ = self.__class__.__name__
        self.objs, self.combinators,self.obj_typ = self._find_math_objects(self.txt)
        self._find_deltas() # Will convert bras and kets into delta functions

        # Simplifying
        self._simplify_deltas()
        #self._combine_coeff_conjs()  #This needs work.
    
    def _simplify_1_delta_with_indices(self, delta_inds):
        # Won't currently work if other parent math objects are inside.
        # This is because it won't recursively change things, lower down.
        if any(not i.child for i in self.objs):
            EXC.WARN("Sorry I currently can't cancel the kronecker delta in the sum %s.\nThis is something that needs coding in."%self.latex())
            return
        # Finds the relevant math objects
        relevant_objs = [] # Holds all objects that have relevant indices
        for i, Typ in enumerate(self.obj_typ):
            if self.objs[i].child:
                if any(j in delta_inds[0] for j in self.objs[i].inds) and "\\delta" not in Typ:
                    relevant_objs.append(self.objs[i])
        # Change any occurance of the first delta index to the second delta index
        new_inds = self.inds[:]
        for i in range(len(new_inds)):
            if delta_inds[1] in new_inds:
                new_inds[i] = new_inds[i].replace(delta_inds[0], "D")
            else:
                new_inds[i] = new_inds[i].replace(delta_inds[0], delta_inds[1])
            new_inds = [i for i in new_inds if i != 'D']
        for obj in relevant_objs:
            if delta_inds[1] in obj.inds:
                obj.inds = [i.replace(delta_inds[0], delta_inds[1]) for i in obj.inds]
        return new_inds

    # Will let a single kronecker delta do it's thing in a sum. Takes the index of the delta as a argument
    def _simplify_1_delta(self, delta_I):
        delta_inds = self.objs[delta_I].inds
        new_inds = self._simplify_1_delta_with_indices(delta_inds)
        # Remove the delta from the sum
        if new_inds != self.inds: # Something has changed
            self.inds = new_inds
            self._remove_obj(delta_I)
        elif any(j in delta_inds for j in self.inds):
            delta_inds = [delta_inds[1],delta_inds[0]]
            new_inds = self._simplify_1_delta_with_indices(delta_inds)
            if new_inds != self.inds: # Something has changed
                self.inds = new_inds
                self._remove_obj(delta_I)
        self._combine_coeff_conjs()

    # NEED TO WORK ON THIS! I WANT TO GENERALISE IT SO IT WORKS IF THE <a|b> PAIR ARE INSIDE ANOTHER PARENT.
    #    SAY A \nabla{}
    # If any dirac deltas are in the sum then simplify the expression
    def _simplify_deltas(self):
        delta_inds_P = [i for i,obj_typ in enumerate(self.obj_typ) if obj_typ == "\\delta"]
        delta_inds = [i for i,obj_typ in enumerate(self.obj_typ) if obj_typ == "\\delta"]
        count = 0
        inf_killer = 0
        while (len(delta_inds) > 0 and inf_killer < 50):
            self._simplify_1_delta(delta_inds[count])
            delta_inds = [i for i,obj_typ in enumerate(self.obj_typ) if obj_typ == "\\delta"]
            if delta_inds == delta_inds_P:
                count += 1
            if count >= len(delta_inds):
                break
            delta_inds_P = delta_inds[:]
            inf_killer += 1
#            
            

    # Will find and simplify any U_{Xi}* U_{Yi} pairs
    def _can_simplify_U(self):
        bad_return = False, False, False
        U_count = self.obj_typ.count("\\U")
        if U_count >= 2: # Need more than 1 U matrix
            all_inds = [obj.inds for obj in self.objs]
            U_second_inds = [self.objs[i].inds[1] for i in range(len(self.objs)) if "\\U" in self.obj_typ[i]]
            U_second_inds_D = {i:0 for i in U_second_inds}
            for i in U_second_inds:
                U_second_inds_D[i] += 1 # Count the number of indices and add this to the dictionary
            # Can't simplify cases where more than or less than 2 matricies with their second indices the same
            if not all(U_second_inds_D[i] == 2 for i in U_second_inds_D): 
                return bad_return
            end_func = False
            for index in U_second_inds_D:
                num_indices = sum([i.count(index) for i in all_inds])
                if num_indices != 2:
                    U_second_inds_D = {p:2 for p in U_second_inds_D if p != index}
                    continue
                if index not in self.inds:
                    U_second_inds_D = {p:2 for p in U_second_inds_D if p != index}
                    continue
            if end_func:
                return bad_return
            valid_indices = list(U_second_inds_D.keys())
            U_indices = [[i for i in range(len(self.objs)) if self.obj_typ[i] == "\\U" and self.objs[i].inds[1] == j] for j in valid_indices]
            return True, valid_indices, U_indices
            
            U_second_inds_D = {i:U_second_inds_D[i] for i in U_second_inds_D if U_second_inds_D[i] == 2}
        else:
            return bad_return
            

    # Finds the index of a coefficients or bra/ket
    def _find_index(self, txt):
        if "_" not  in txt:
            EXC.WARN("Can't find any indices.\nTxt = %s"%txt)
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
        if self.objs:
            latex_str = "\\sum\\limits_{%s} %s %s "%(inds, left_bracket, self.objs[0].latex())
        else:
            latex_str = "\\sum\\limits_{%s}"%(inds)
        for i in range(1,len(self.combinators)):
            latex_str += self.combinators[i]
            latex_str += self.objs[i].latex()
        latex_str += right_bracket
        return latex_str

class BRA(SUM):
    " Stores info on bras"

    def __init__(self, txt):
        self.txt = txt
        self.child = True
        self.__name__ = self.__class__.__name__
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
            EXC.WARN("I don't know whether %s is diabatic or adiabatic!"%txt)

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
            EXC.WARN("I don't know whether %s is diabatic or adiabatic!"%txt)

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
            EXC.WARN("More than 1 index on the bra %s"%self.txt)
        ind = self.inds[0]
        trans_txt = "{_X \\coeff{u_{X}[R,t]} \\U{_{%s,X}} }"%ind
        return SUM(trans_txt)
        #C_l = \sum\limits_{m}u_m U_{lm}

    # Converts diabatic coeffs to adiabatic
    def _diab_2_adiab(self):
        pass
    
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

class DELTA(BRA):
    """ A Dirac delta object """

    def __init__(self, txt):
        self.txt = txt
        self.inds = self._find_index(txt)[0]
        self.__name__ = self.__class__.__name__
        self.child= True

    def latex(self):
        inds = ",".join(self.inds)
        return "\\delta_{%s}"%inds

class U(COEFF):
    """ A transformation matrix object """

    def __init__(self, txt):
        self.txt = txt
        self.__name__ = self.__class__.__name__
        self.child = True
        self.deps = self._find_dependencies(txt)
        self.inds = self._find_index(txt)[0]
        self.conj = self._find_conj(txt)
        if self.conj:
            self.bra, self.ket = self._create_bra_ket_conj(self.inds)
        else:
            self.bra, self.ket = self._create_bra_ket(self.inds)
    
    # Creates the Bra and the Ket as part of the U matrix
    def _create_bra_ket(self, inds):
        if len(inds) != 2:
            if "," in inds:
                EXC.WARN("The number of indices for the U matrix, %s, is %i it should be 2!\n\nDid you forget to seperate indices by a comma?"%(self.txt, len(inds)))
            else:
                EXC.WARN("The number of indices for the U matrix, %s, is %i it should be 2!\nDid you forget to put them in curly braces e.g. _{l,n}?"%(self.txt, len(inds)))
        bra = BRA("{\phi_{%s}[R,t]}"%(inds[0]))
        ket = KET("{\psi_{%s}[R,t]}"%(inds[1]))
        return bra,ket
    
    # Creates the Bra and the Ket as part of the U matrix
    def _create_bra_ket_conj(self, inds):
        if len(inds) != 2:
            if "," in inds:
                EXC.WARN("The number of indices for the U matrix, %s, is %i it should be 2!\n\nDid you forget to seperate indices by a comma?"%(self.txt, len(inds)))
            else:
                EXC.WARN("The number of indices for the U matrix, %s, is %i it should be 2!\nDid you forget to put them in curly braces e.g. _{l,n}?"%(self.txt, len(inds)))
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
print("\n",steps_taken)
