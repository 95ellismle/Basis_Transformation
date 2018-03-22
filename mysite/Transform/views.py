from django.shortcuts import render

from .models import Transform
# Create your views here.

def index(request):
    if not request.POST.get("equation_in"):
        context = {'print_eq':False}
    else:
        equation_in = request.POST['equation_in']
        Trans = Transform(equation_in)
        steps_taken = [i for i in Trans.eq.steps_taken.split("**#") if i]
        step_text = [i for i in Trans.eq.step_text.split('**#') if i]
        context = {'eq_in':Trans.eq.eq_in,
                   'print_eq': Trans.eq.eq_in.count("\\") > 0,
                    "test":"",
                    'steps':zip(steps_taken,step_text),
                    'print_steps':len(steps_taken) > 1,
                    }
    return render(request, "Transform/index.html",context)
