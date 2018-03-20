from django.shortcuts import render

from .models import Transform
# Create your views here.

def index(request):
    if not request.POST.get("equation_in"):
        context = {'print_eq':False}
    else:
        equation_in = request.POST['equation_in']
        Trans = Transform(equation_in)
        context = {'eq_in':Trans.eq.eq_in,
                   'print_eq': True,
                    "test":"",
                    'steps':zip(Trans.eq.steps_taken.split('**#'),Trans.eq.step_text.split('**#')),
                    }
    return render(request, "Transform/index.html",context)
