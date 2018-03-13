# Basis_Transformation
Some code to transform the basis of an equation from adiabatic to diabatic

The idea behind this code is to save me time in the long run constantly converting equations from the adiabatic basis to the (orthogonal-)diabatic basis. Also it is a task that is very suited to using OOP paradigms -something I would like to explore further. Hopefully also if I develop it to a workable state people in the group may use it.

At the moment, the equation is specified in the file To_Transform and certain functions are used to define mathematical operations. These are:
 * \\sum{_{indices} }
 * \\coeff{name_{indices}[dependencies]}
 * \\U{_{indices}[dependencies]}
 * \\bra{name_{indices}[dependencies]}
 * \\ket{name_{indices}[dependencies]}
 * \\delta{_{indicies}}
 
 An example input file could be:
 \\sum{_l \coeff{u_l[R,t} }
 
This would be read as a sum of the (diabatic) u coefficients over all l.
