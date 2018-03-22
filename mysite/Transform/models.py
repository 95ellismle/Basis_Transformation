#from django.db import models

from .src import math_objects as MO

# # Create your models here.
# class Transform(object):
#
#     def __init__(self, equation_in):
#         self.eq_in = equation_in
#         self.eq_out = "BOB"
#         self.steps = ['1','2','3']

class Transform(object):

    def __init__(self, equation_in):
        steps_taken = ""
        begin_eq = "**#"
        end_eq = ""
        self.errors = {}
        self.eq = MO.MATH_OBJECTS(equation_in, self.errors, steps_taken, begin_eq, end_eq)
