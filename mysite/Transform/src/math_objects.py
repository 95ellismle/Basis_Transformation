#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 17 21:43:24 2018

@author: oem
"""

class MATH_OBJECTS(object):
    """ Contains all the math objects found within the input text.
      The base class for all the other objects. """

    def __init__(self, txt, errors, steps_taken, begin_eq, end_eq):
        self.txt = txt
        self.steps_taken =  steps_taken
        self.step_text = ""
        self.begin_eq = begin_eq
        self.end_eq = end_eq
        self.child = False
        self.__name__ = self.__class__.__name__
        self.objs, self.combinators,self.obj_typ = self._find_math_objects(txt, errors)
        self.eq_in = self.latex(errors)
        if self.objs:
            self.steps_taken += "%s%s%s\n\n"%(begin_eq, self.latex(errors), end_eq)
            self.step_text += "%sOriginal Equation was:"%self.begin_eq
            # Simplifying
            #self._combine_coeff_conjs()  #This needs work.
            self._merge_nested_sums(errors)
            self._split_sums(errors)

    # Will add an error message into the errors dict
    def _add_err_msg(self, errors, msg):
        if len(errors.keys()) == 0:
            errors[0] = msg
        else:
            new_key = max(errors.keys())+1
            errors[new_key] = msg

    # Will check if there are the correct amount of braces in the text
    def _correct_amount_of_braces(self, txt, errors):
        LBraces = txt.count("{")
        RBraces = txt.count("}")
        if LBraces == RBraces:
            return True
        else:
            if LBraces > RBraces:
                self._add_err_msg(errors, "There are more '{' than '}'! Please check you've properly closed of the braces!")
                return False, ("{","}")
            else:
                self._add_err_msg(errors, "There are more '}' than '{'! Please check you've properly closed of the braces!")
                return False, ("}","{")

    # Will follow the path that is in the path dictionary and find the math object.
    def _follow_path(self, path, errors):
        x = self.objs
        count = 0
        for i in path:
            if i < len(x):
                if x[i].child:
                    if count == len(path)-1:
                        return x[i]
                    else:
                        self._add_err_msg(errors, "Can't find path %s, the path length is too long.\nThe chain of math objects isn't as long as the amount of indices in the path)"%path)
                else:
                    if count == len(path)-1:
                        return x[i]
                    x = x[i].objs
            else:
                self._add_err_msg(errors, "Can't find path %s"%str(path))
                return False
            count += 1

    # Will recursively iterate over all objects in the self.objs list and find the parents and children.
    def _create_struct(self, lIst, obj_types, errors, parent="root", level=0, struct={}, levels={0:0}, names={}):
        if len(lIst) != len(obj_types):
            self._add_err_msg(errors, "%s._create_struct has a different number of objects and object types.\n\tobj_types = %s\n\tobjs = %s"%(self.__name__, str(obj_types), str(lIst)))
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
                self._create_struct(new_list, item.obj_typ, errors, item, level+1,struct,levels, names)
        return struct, names

    # Will create a dictionary with the path to each object in the struct dictionary
    def _create_paths(self, lIst, errors, parent_i=0, level=0, paths={}):
        for i, item in enumerate(lIst):
            if paths.get(level)  == None:
                paths[level] = []
            if level == 0:
                paths[0] = [[i] for i in range(len(self.objs))]
            else:
                paths[level].append(paths[level-1][parent_i]+[i])
            if not item.child:
                new_list = item.objs
                self._create_paths(new_list, errors, i, level+1, paths)
        return paths

    # Re-writes the parent summations with multiple child summations as multiple parent summations with 1 child.
    def _one_child_parent_sums(self, errors):
        orig_latex = self.latex(errors)
        self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ, errors)
        self.paths  = self._create_paths(self.objs, errors)
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
                            new_sum = SUM("{_{%s}}"%(','.join(child.inds)), errors, self.steps_taken, self.begin_eq, self.end_eq)
                            new_sum.objs = [grandchild]
                            new_sum.obj_typ = ["\\sum"]
                            new_sum.combinators = [""]
                            parent._insert_obj(len(parent.objs)+1, new_sum, "\\sum", comb, errors)
                        count = 0
                        for index in sorted(adopted_grandchildren_indices):
                            child._remove_obj(index-count, errors)
                            count += 1
        self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ, errors, parent="root", level=0, struct={}, levels={0:0}, names={})
        self.paths  = self._create_paths(self.objs, errors, parent_i=0, level=0, paths={})
        if self.latex(errors) != orig_latex:
            self.steps_taken += "%s%s%s"%(self.begin_eq, self.latex(errors), self.end_eq)
            self.step_text += "%sSplit summations with multiple nesting into multiple parent sums and 1 child:"%self.begin_eq


    # Returns a list of lists containing items that are in between the indices provided
    def _divide_list(self, indices, list_in,errors):
        if len(indices) > 0:
            list_out = [list_in[:indices[0]]]
            if len(indices) > 1:
                list_out += [list_in[indices[i-1]:indices[i]] for i in range(1,len(indices))]
            list_out += [list_in[indices[-1]:]]
            return list_out
        else:
            return [list_in]

    # Re-writes the parent summations with multiple child summations as multiple parent summations with 1 child.
    def _split_sums(self, errors):
        orig_latex = self.latex(errors)
        for level in self.struct:
            count = 0
            for i, (child,parent) in enumerate(self.struct[level]):
                if child.__name__ == "SUM":
                    instances_of_combs = [i for i,comb in enumerate(child.combinators) if any(comb == i for i in ['+','-'])]
                    if not instances_of_combs:
                        continue
                    new_objs  = self._divide_list(instances_of_combs, child.objs, errors)
                    new_combs = self._divide_list(instances_of_combs, child.combinators, errors)
                    for cI in range(len(new_combs)):
                        new_combs[cI][0] = ''
                    new_typs  = self._divide_list(instances_of_combs, child.obj_typ, errors)
                    inds = child.inds
                    NEW_OBJS = {}
                    for objI in range(len(new_objs)):
                        NEW_OBJS[objI] = SUM("{_{%s} }"%",".join(inds), errors, self.steps_taken, self.begin_eq, self.end_eq)
                        NEW_OBJS[objI].objs = new_objs[objI]
                        NEW_OBJS[objI].combinators = new_combs[objI]
                        NEW_OBJS[objI].obj_typ = new_typs[objI]
                    for objI in NEW_OBJS:
                        count += 1
                        parent._insert_obj(len(parent.objs)+1, NEW_OBJS[objI], "\\sum", " + ", errors)

            if count > 0:
                for i in range(0,len(parent.objs)-count):
                    parent._remove_obj(0, errors)
        if self.latex(errors) != orig_latex:
            self.steps_taken += "%s%s%s"%(self.begin_eq, self.latex(errors), self.end_eq)
            self.step_text += "%sSplit summations with a + or - in (this is a code thing rather than a maths thing):"%self.begin_eq
        self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ, errors, parent="root", level=0, struct={}, levels={0:0}, names={})
        self.paths  = self._create_paths(self.objs, errors, parent_i=0, level=0, paths={})
        self._simplify_U(errors)

    # Will remove any sums without any indices
    def _remove_empty_sums(self, errors):
        for level in self.struct:
          for i, (child,parent) in enumerate(self.struct[level]):
              if child.__name__ == "SUM":
                  if not child.inds:
                      for j in range(len(child.objs)):
                          parent._insert_obj(i+1, child.objs[j], child.obj_typ[j], child.combinators[j], errors)
                      parent._remove_obj(i, errors)

    # Will simplify the U transformation matricies by removing indices from the sum and making a dirac delta
    def _simplify_U(self, errors):
       LaTeX = self.latex(errors)
       for level in self.struct:
          for i, (child,parent) in enumerate(self.struct[level]):
              if child.__name__ == "SUM":
                can_simp, indices, U_places = child._can_simplify_U(errors)
                if can_simp:
                    U_places = sorted(U_places)
                    count = 0
                    for X in U_places:
                        if len(X) != 2:
                           self._add_err_msg(errors, "Something went wrong with the SUM._can_simplify_U() function. It is telling me I can simplify %i"%child.latex(errors))
                           return False
                        sortX = sorted(X)
                        delta_inds = [child.objs[u-count].inds[0] for u in sortX]
                        new_delta = DELTA("{_{%s}}"%",".join(delta_inds))
                        for x in sortX:
                           child._remove_obj(x-count, errors)
                           count += 1
                        child._insert_obj(len(child.objs)+1, new_delta, "\\delta", "", errors)
                        for ind in indices:
                            child.inds = [j for j in child.inds if j != ind]
                        LaTeX = self.latex(errors)
                        self.steps_taken += "%s%s%s"%(self.begin_eq, LaTeX, self.end_eq)
                        self.step_text += "%sSimplifying the U terms using the relationship $\\sum\\limits_{x}U^{*}_{bx}U_{ax} = \delta_{ab}$:"%self.begin_eq
                child._simplify_deltas(errors)
       latex_str = self.latex(errors)
       if latex_str != LaTeX:
         self.steps_taken += "%s%s%s"%(self.begin_eq, latex_str, self.end_eq)
         self.step_text += "%sLet them Kronecker deltas work their magic:"%self.begin_eq
   #self._remove_empty_sums()

       self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ, errors, parent="root", level=0, struct={}, levels={0:0}, names={})
       self.paths  = self._create_paths(self.objs, errors, parent_i=0, level=0, paths={})
       # * If sum indices are empty, remove sum:
       # * Use the function _simplify_deltas

    # Will combine nested sums into single sums with just 1 summation sign. This will  merge any parent sums into the child and the delete the parent.
    def _merge_nested_sums(self, errors):
        self._one_child_parent_sums(errors)
        level = 0
        add_level = True
        while (level <= max(self.struct.keys())):
            for i, (child,parent) in enumerate(self.struct[level]):
                if child.__name__ == "SUM" and child.__name__ == parent.__name__:
                    [child.inds.append(i) for i in parent.inds] # Merge the parent's indices with the child
                    self.objs[self.paths[level][i][-2]] = child # Replace the parent with the child
                    add_level = False
                    self.struct, self.struct_names = self._create_struct(self.objs, self.obj_typ, errors, parent="root", level=0, struct={}, levels={0:0}, names={})
                    self.paths  = self._create_paths(self.objs, errors, parent_i=0, level=0, paths={})
            if add_level:
                level += 1
            else:
                level = 0
                add_level= True

    # Finds all the math objects in the text from the valid_math_objects dict
    def _find_math_objects(self, txt, errors):
        objects = []
        combinators = []
        object_types = []
        count = 0
        while (txt.find("{") != -1 and txt.find("}") != -1):
            obj_txt, obj_type, start_ind, end_ind = self._find_first_enclosed_object(txt, errors)
            if not obj_txt:
                break
            obj = valid_math_objects[obj_type](obj_txt, errors, self.steps_taken, self.begin_eq, self.end_eq)
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
    def _find_first_enclosed_object(self, txt, errors):
        for i, letter in enumerate(txt):
            if letter == "{":
                up_to_txt = txt[:i]
                start_ind = up_to_txt.rfind('\\')
                obj = up_to_txt[start_ind:]
                if obj in valid_math_objects:
                    end_ind = self._find_matching_str(txt[i:], "{","}", errors)
                    if end_ind == None:
                        return False, False, False, False
                    end_ind += i
                    return txt[i:end_ind], obj, start_ind, end_ind
                else:
                    return False, False, False, False
        else:
            return False, False, False, False
    # Finds the matching right string to go with the left one
    def _find_matching_str(self, txt, left_str, right_str, errors):
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
        self._add_err_msg(errors, "Couldn't find the enclosing brace, txt = %s"%txt)

    # Simplifies an occurance of a repeated coefficient to a power.
    def _combine_coeff_conjs(self, errors):
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
            self._insert_obj(need_to_merge[i][0], COEFF(new_obj_txt), "\\coeff", "", errors)
            [self._remove_obj(j+1, errors) for j in need_to_merge[i][::-1]]

    # Finds all objects that are the same in the list of math objects
    def _find_the_same_objs(self, allowed_type, errors):
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
    def _insert_obj(self, i, obj, obj_typ, comb, errors):
        self.obj_typ.insert(i,obj_typ)
        self.objs.insert(i, obj)
        self.combinators.insert(i, comb)

    # Removes an object from combinators, obj_typ and objs
    def _remove_obj(self, i, errors):
        self.combinators = self.combinators[:i] + self.combinators[i+1:]
        self.objs = self.objs[:i] + self.objs[i+1:]
        self.obj_typ = self.obj_typ[:i] + self.obj_typ[i+1:]

    # Converts bra-ket pair with the same name to a dirac delta (Assuming orthogonal bases -which the adiabatic and quassi diabatic bases are)
    def _find_deltas(self, errors):
        maxlen = len(self.obj_typ)
        for i in range(1,len(self.obj_typ)):
          if i < maxlen:
            if self.obj_typ[i-1]+self.combinators[i]+ self.obj_typ[i] == "\\bra\\ket":
              if self.objs[i-1].name == self.objs[i].name:
                if self.objs[i-1].a_or_d == self.objs[i].a_or_d:
                  if len(self.objs[i-1].inds) == 1 and len(self.objs[i-1].inds) == 1:
                      new_delta_obj = DELTA("\\delta{_{%s,%s} }"%(self.objs[i-1].inds[0],self.objs[i].inds[0]))
                      self._insert_obj(i, new_delta_obj, "\\delta", errors)
                      self._remove_obj(i-1, errors)
                      self._remove_obj(i, errors)
                      maxlen -= 1

    # Converts the math object to latex code
    def latex(self, errors):
        if not self.objs:
            self._add_err_msg(errors, "No math objects found in ''%s'' "%self.txt)
            return ""
        latex_str = self.objs[0].latex(errors)
        for i in range(1,len(self.combinators)):
            latex_str += "%s\n"%self.combinators[i].replace(" ", "")
            latex_str += self.objs[i].latex(errors)
        return latex_str.replace("||", "|")


class SUM(MATH_OBJECTS):
    " Stores info on any summations "

    def __init__(self, txt, errors, steps_taken, begin_eq, end_eq):
        self.steps_taken =  steps_taken
        self.begin_eq = begin_eq
        self.end_eq = end_eq
        self.inds, self.txt = self._find_index(txt, errors)
        if not self.inds:
            return
        self.child = False
        self.__name__ = self.__class__.__name__
        self.objs, self.combinators,self.obj_typ = self._find_math_objects(self.txt, errors)
        self._find_deltas(errors) # Will convert bras and kets into delta functions

        # Simplifying
        self._simplify_deltas(errors)
        #self._combine_coeff_conjs(errors)  #This needs work.

    def _simplify_1_delta_with_indices(self, delta_inds, delta_I, errors):
        change = False

        # Won't currently work if other parent math objects are inside.
        # This is because it won't recursively change things, lower down.
        if any(not i.child for i in self.objs):
            self._add_err_msg(errors, "Sorry I currently can't cancel the kronecker delta in the sum %s.\nThis is something that needs coding in."%self.latex(errors))
            return
        # Finds the relevant math objects
        #print(delta_inds, [j.inds for j in self.objs])
        # Holds all objects that have relevant indices
        relevant_objs = [obj for i,obj in enumerate(self.objs) if delta_inds[0] in obj.inds and i != delta_I and obj.child]
        # Change any occurance of the first delta index to the second delta index
        new_inds = self.inds[:]
        for i,ind in enumerate(new_inds):
            if delta_inds[0] == ind:
                if delta_inds[1] in new_inds:
                    new_inds.remove(ind)
                else:
                    new_inds[i] = delta_inds[1]


        for obj in relevant_objs:
            change = True
            if delta_inds[0] in obj.inds:
                obj.inds = [i.replace(delta_inds[0], delta_inds[1]) for i in obj.inds]

        return new_inds, change

    # Will let a single kronecker delta do it's thing in a sum. Takes the index of the delta as a argument
    def _simplify_1_delta(self, delta_I, errors):
        delta_inds = self.objs[delta_I].inds
        new_inds, change = self._simplify_1_delta_with_indices(delta_inds, delta_I)
        # Remove the delta from the sum
        self.inds = new_inds
        self._remove_obj(delta_I, errors)

        self._combine_coeff_conjs()

    # NEED TO WORK ON THIS! I WANT TO GENERALISE IT SO IT WORKS IF THE <a|b> PAIR ARE INSIDE ANOTHER PARENT.
    #    SAY A \nabla{}
    # If any dirac deltas are in the sum then simplify the expression
    def _simplify_deltas(self, errors):
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
    def _can_simplify_U(self, errors):
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
    def _find_index(self, txt, errors):
        if "_" not  in txt:
            self._add_err_msg(errors, "Can't find any indices in \%s%s"%(self.__name__.lower(),txt))
            return False, False
        txt = txt[txt.find('_'):]
        if txt[1] != '{':
            end_ind = 2
            index = [txt[1]]
        else:
            end_ind = txt.find('}')
            index = txt[txt.find('{')+1:end_ind].split(',')
        return index, txt[end_ind:]

    # Converts the math object to latex code
    def latex(self, errors):
        if not self.inds:
            return ""
        inds = ','.join(self.inds)
        left_bracket  = ""
        right_bracket = ""
        if any(i in self.combinators for i in ('+','-')):
            left_bracket = "\\left["
            right_bracket = "\\right]"
        if self.objs:
            latex_str = "\\sum\\limits_{%s} %s %s "%(inds, left_bracket, self.objs[0].latex(errors))
        else:
            latex_str = "\\sum\\limits_{%s}"%(inds)
        for i in range(1,len(self.combinators)):
            latex_str += self.combinators[i]
            latex_str += self.objs[i].latex(errors)
        latex_str += right_bracket
        return latex_str

class BRA(SUM):
    " Stores info on bras"

    def __init__(self, txt, errors, steps_taken="", begin_eq="", end_eq=""):
        self.txt = txt
        self.child = True
        self.__name__ = self.__class__.__name__
        self.a_or_d = self._find_adiab_or_diab(txt, errors)
        self.name = self._find_var_name(txt, errors)
        self.deps = self._find_dependencies(txt, errors)
        self.inds = self._find_index(txt, errors)[0]
        if not self.inds:
            return

    # Finds the name of a variable
    def _find_var_name(self, txt, errors):
        end_of_name_possibils = ('_','[','}','^','!')
        end_of_name_index = min([txt.find(i) for i in end_of_name_possibils if txt.find(i) != -1])
        name = txt[1:end_of_name_index]
        return name

    # Finds the index of a coefficients or bra/ket
    def _find_adiab_or_diab(self, txt, errors):
        if "psi" in txt:
            return "a"
        if "phi" in txt:
            return "d"
        else:
            self._add_err_msg(errors, "I don't know whether \%s%s is diabatic or adiabatic!"%(self.__name__.lower(),txt))

    # Finds the dependencies of terms
    def _find_dependencies(self, txt, errors):
        dependencies = []
        if txt.find('[') != -1 and txt.find(']') != -1:
            txt = txt[txt.find('[')+1:txt.find(']')]
            [dependencies.append(i) for i in txt.split(',')]
        return dependencies

    # Converts diabatic bras to adiabatic
    def _diab_2_adiab(self, errors):
        pass

    # Converts the math object to latex code
    def latex(self, errors):
        if not self.inds:
            return ""
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

class KET(BRA):
    " Stores info on kets "

    def __init__(self, txt, errors, steps_taken="", begin_eq="", end_eq=""):
        BRA.__init__(self, txt, steps_taken="", begin_eq="", end_eq="")
        self.txt = txt

    # Converts adiabatic kets to diabatic
    def _adiab_2_diab(self, errors):
        pass

    # Converts diabatic kets to adiabatic
    def _diab_2_adiab(self, errors):
        pass

    # Converts the math object to latex code
    def latex(self, errors):
        if not self.inds:
            return ""
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

class COEFF(BRA):
    " Stores info on the coefficients "

    def __init__(self, txt, errors, steps_taken="", begin_eq="", end_eq=""):
        BRA.__init__(self, txt, errors, steps_taken="", begin_eq="", end_eq="")
        self.txt = txt
        if not self.inds:
            self._add_err_msg(errors, "I can't find any indices in \%s%s they are set the same as in LaTeX e.g. X_{ind}"%(self.__name__.lower(), txt))
            return
        self.conj = self._find_conj(txt)
        self.pow = int(self._find_powers(txt))

    # Finds whether the coefficient should be treated as the conjugate
    def _find_conj(self, txt, errors):
        if "*" in txt:
            return True
        else:
            return False

    # Finds the index of a coefficients or bra/ket
    def _find_adiab_or_diab(self, txt, errors):
        if "c" in txt.lower():
            return "a"
        if "u" in txt.lower():
            return "d"
        else:
            self._add_err_msg(errors, "I don't know whether \%s%s is diabatic or adiabatic!"%(self.__name__.lower(),txt))

    # Finds any powers
    def _find_powers(self, txt, errors):
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
    def _adiab_2_diab(self, errors):
        if len(self.inds) > 1:
            self._add_err_msg(errors, "More than 1 index on the bra %s"%self.txt)
        ind = self.inds[0]
        trans_txt = "{_X \\coeff{u_{X}[R,t]} \\U{_{%s,X}} }"%ind
        return SUM(trans_txt, errors, self.steps_taken, self.begin_eq, self.end_eq)
        #C_l = \sum\limits_{m}u_m U_{lm}

    # Converts diabatic coeffs to adiabatic
    def _diab_2_adiab(self, errors):
        pass

    # Converts the math object to latex code
    def latex(self, errors):
        if not self.inds:
            return ""
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

    def __init__(self, txt, errors, steps_taken="", begin_eq="", end_eq=""):
        self.txt = txt
        self.inds = self._find_index(txt, errors)[0]
        if not self.inds:
            return
        self.__name__ = self.__class__.__name__
        self.child= True

    def latex(self, errors):
        if not self.inds:
            return ""
        inds = ",".join(self.inds)
        return "\\delta_{%s}"%inds

class U(COEFF):
    """ A transformation matrix object """

    def __init__(self, txt, errors, steps_taken="", begin_eq="", end_eq=""):
        self.txt = txt
        self.__name__ = self.__class__.__name__
        self.child = True
        self.deps = self._find_dependencies(txt)
        self.inds = self._find_index(txt, errors)[0]
        if not self.inds:
            return
        self.conj = self._find_conj(txt)
        if self.conj:
            self.bra, self.ket = self._create_bra_ket_conj(self.inds, errors)
        else:
            self.bra, self.ket = self._create_bra_ket(self.inds, errors)

    # Creates the Bra and the Ket as part of the U matrix
    def _create_bra_ket(self, inds, errors):
        if len(inds) != 2:
            if "," in inds:
                self._add_err_msg(errors, "The number of indices for the U matrix, %s, is %i it should be 2!\n\nDid you forget to seperate indices by a comma?"%(self.txt, len(inds)))
            else:
                self._add_err_msg(errors, "The number of indices for the U matrix, %s, is %i it should be 2!\nDid you forget to put them in curly braces e.g. _{l,n}?"%(self.txt, len(inds)))
        bra = BRA("{\phi_{%s}[R,t]}"%(inds[0]))
        ket = KET("{\psi_{%s}[R,t]}"%(inds[1]))
        return bra,ket

    # Creates the Bra and the Ket as part of the U matrix
    def _create_bra_ket_conj(self, inds, errors):
        if len(inds) != 2:
            if "," in inds:
                self._add_err_msg(errors, "The number of indices for the U matrix, %s, is %i it should be 2!\n\nDid you forget to seperate indices by a comma?"%(self.txt, len(inds)))
            else:
                self._add_err_msg(errors, "The number of indices for the U matrix, %s, is %i it should be 2!\nDid you forget to put them in curly braces e.g. _{l,n}?"%(self.txt, len(inds)))
        bra = BRA("{\psi_{%s}[R,t]}"%(inds[1]), errors)
        ket = KET("{\phi_{%s}[R,t]}"%(inds[0]), errors)
        return bra,ket

    # Creates a string with LaTeX code for this object
    def latex(self, errors):
        if not self.inds:
            return ""
        inds = ",".join(self.inds)
        return "U_{%s}"%inds

latex_with_deps = False

valid_math_objects = {'\\sum':SUM,'\\coeff':COEFF,'\\ket':KET,'\\bra':BRA, "\\delta":DELTA, "\\U":U}
child_math_objects = {'\\coeff':COEFF,'\\ket':KET,'\\bra':BRA, "\\delta":DELTA, "\\U":U}
