from django.shortcuts import redirect


def redirec_to_admin_view(request):
    return redirect('/admin')
