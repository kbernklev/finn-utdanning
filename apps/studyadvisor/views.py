from django.shortcuts import render, redirect, get_object_or_404
from .models import Interesser, Studier, RelevantStudie, Studieforslag, Fargetema
from .forms import StudieforslagForm, EndreInteresseForm, EndreStudieForm, FargetemaForm
from django.contrib.auth.decorators import user_passes_test


#   This returns true if the user is a veileder:
def veileder_check(user):
    isVeileder = user.groups.all().filter(name='veileder').exists()
    return isVeileder


#   This takes a context (variables to be sent to html view) as parameter and
#   adds information about the user's color theme so that the color vaiables
#   can be used in the css-code:
def send_fargetema(request, context):
    if request.user.is_authenticated:
        fargetemaPrivat = Fargetema.objects.filter(bruker=request.user)
        #   Chech if the user has a personal color theme and if it's enabled:
        if len(fargetemaPrivat) > 0 and fargetemaPrivat[0].brukPersonlig == True:
            #   If true use personal color theme:
            context['navbarFarge'] = fargetemaPrivat[0].navbarFarge
            context['bakgrunnFarge'] = fargetemaPrivat[0].bakgrunnFarge
            #   Important to return here so that personal color theme does not get overwritten by global color theme:
            return
    fargetemaGlobal = Fargetema.objects.filter(bruker=None)
    #   Chech if there exists a global color theme if it's enabled:
    if len(fargetemaGlobal) > 0 and fargetemaGlobal[0].brukPersonlig == True:
        #   If true use global color theme:
        context['navbarFarge'] = fargetemaGlobal[0].navbarFarge
        context['bakgrunnFarge'] = fargetemaGlobal[0].bakgrunnFarge
    return


#   This view should only be available for veiledere:
@user_passes_test(veileder_check, login_url='home', redirect_field_name=None)
def personligFargetema(request):
    #   This view contains logic for the "personligfargetema.html" page.
    #   Get the user's current personal color theme:
    gamleFargetema = Fargetema.objects.filter(bruker=request.user)
    if request.method == "POST":
        form = None
        #   Check if the user actually has an available personal color theme:
        if len(gamleFargetema) > 0:
            #   If true set the values of the input elements on the html page to reflect this color theme:
            form = FargetemaForm(request.POST, instance=gamleFargetema[0])
        else:
            #   If user hasn't created a personal color theme before add a default color theme that the user can change on the html page:
            nyttFargetema = Fargetema.objects.create(navbarFarge='#000000', bakgrunnFarge='#000000')
            form = FargetemaForm(request.POST, instance=nyttFargetema)
        #   When the user clicks the button to save his changes to the color theme:
        if form.is_valid():
            fargetema = form.save(commit=False)
            if request.user.is_authenticated:
                fargetema.bruker = request.user
            fargetema.navbarFarge = form.cleaned_data['navbarFarge']
            fargetema.bakgrunnFarge = form.cleaned_data['bakgrunnFarge']
            #   Save the new changes to user's personal color theme in the data base:
            fargetema.save()
    form = None
    #   If the user doesn't make a POST request, check if he has a personal color theme:
    if len(gamleFargetema) > 0:
        #   If true set the values of the input elements on the html page to reflect this color theme:
        form = FargetemaForm(instance=gamleFargetema[0])
    else:
        #   If not show default/empty input values:
        form = FargetemaForm()
    #   The values of the user's personal color theme gets sent to the html page in the following context:
    context = {
        'form': form
    }
    #   Add information about the user's current color theme to the context, so that the values can be used in css:
    send_fargetema(request, context)
    return render(request, "studyadvisor/personligfargetema.html", context)


#   This view should only be available for staff:
@user_passes_test(lambda u: u.is_staff, login_url='home', redirect_field_name=None)
def globaltFargetema(request):
    #   This view contains logic for the "globaltfargetema.html" page.
    #   Get the current global color theme:
    gamleFargetema = Fargetema.objects.filter(bruker=None)
    if request.method == "POST":
        form = None
        #   Check if there actually exists a global color theme:
        if len(gamleFargetema) > 0:
            #   If true set the values of the input elements on the html page to reflect this color theme:
            form = FargetemaForm(request.POST, instance=gamleFargetema[0])
        else:
            #   If there doesn't exist a global color theme add a default/empty color theme that the user can change on the html page:
            nyttFargetema = Fargetema.objects.create(navbarFarge='#000000', bakgrunnFarge='#000000')
            form = FargetemaForm(request.POST, instance=nyttFargetema)
        #   When the user clicks the button to save his changes to the color theme:
        if form.is_valid():
            fargetema = form.save(commit=False)
            fargetema.bruker = None
            fargetema.navbarFarge = form.cleaned_data['navbarFarge']
            fargetema.bakgrunnFarge = form.cleaned_data['bakgrunnFarge']
            #   Save the new changes to the global color theme in the data base:
            fargetema.save()
    form = None
    #   If the user doesn't make a POST request, check if there exists a global color theme:
    if len(gamleFargetema) > 0:
        #   If true set the values of the input elements on the html page to reflect this color theme:
        form = FargetemaForm(instance=gamleFargetema[0])
    else:
        #   If not show default/empty input values:
        form = FargetemaForm()
    #   The values of the global color theme gets sent to the html page in the following context:
    context = {
        'form': form
    }
    #   Add information about the user's current color theme to the context, so that the values can be used in css:
    send_fargetema(request, context)
    return render(request, "studyadvisor/globaltfargetema.html", context)


#   This view contains logic for the "frontpage.html" page:
def frontpage(request):
    if request.method == "POST":
        #   Get all the interests that the user selected:
        form = StudieforslagForm(request.POST)
        if form.is_valid():
            #   Create a variable sf for generation of a new studieforslag:
            sf = form.save(commit=False)
            if request.user.is_authenticated:
                #   Set studieforslag's attached user to the current logged in user:
                sf.student = request.user
            else:
                #   If the user is a guest set studieforslag's attached user to None:
                sf.student = None
            sf = form.save()

            #   This for loop increments the popularity of all the selected interests by 1:
            for int in sf.interesser.all():
                i = Interesser.objects.get(pk=int.pk)
                i.popularitet += 1
                i.save()

            #   Loop through all studies:
            for s in Studier.objects.all():
                rel = 0  # Relevance
                #   For each selected interest check if it is relevant to the current study:
                for i in sf.interesser.all():
                    if s.interesser.all().filter(pk=i.pk).exists():
                        #   If the interest is relevant to the current study add 1 to it's relevance:
                        rel += 1
                if rel > 0:
                    #   If the current study is somewhat relevant to the chosen interests add it to the studieforslag:
                    RelevantStudie.objects.create(studieforslag=sf, studie=s, relevans=rel)
            #   Save the studieforslag:
            sf.save()
            #   The following context gets sent to the "studieforslag.html" page to be used as variables in the html code:
            context = {
                'studier': RelevantStudie.objects.all().filter(studieforslag_id=sf.pk).order_by('-relevans'),
                'interesser': sf.interesser.all().order_by('navn'),
                'popInteresser': Interesser.objects.all().order_by('-popularitet')[:10]
            }
            #   Add information about the user's current color theme to the context, so that the values can be used in css:
            send_fargetema(request, context)
            return render(request, "studyadvisor/studieforslag.html", context)

    #       If the user didn't make a POST request just display the interests on "frontpage.html" page:
    form = StudieforslagForm()
    context = {
        'form': form
    }
    #   Add information about the user's current color theme to the context, so that the values can be used in css:
    send_fargetema(request, context)
    return render(request, "frontpage.html", context)


#   This view contains logic for the "prev_searches.html" page:
def prev_searches(request):
    #   Get all of the user's previous studieforslag:
    studie_forslag = Studieforslag.objects.all().filter(student=request.user).reverse()
    #   Create array of arrayer with information about the studieforslag and its relevant studies:
    prev_search = []
    for studieforslag in studie_forslag:
        #   For each studieforslag put it into the array together with its relevant studies:
        relevantstudie = RelevantStudie.objects.all().filter(studieforslag=studieforslag).order_by('-relevans')
        prev_search.append([studieforslag, relevantstudie])
    #   The following context gets sent to the "prev_searches.html" page to be used as variables in the html code:
    context = {
        'searches': prev_search,
    }
    #   Add information about the user's current color theme to the context, so that the values can be used in css:
    send_fargetema(request, context)
    return render(request, "studyadvisor/prev_searches.html", context)


#   This view should only be available for veiledere:
@user_passes_test(veileder_check, login_url='home', redirect_field_name=None)
def nyInteresse(request):
    #   This view contains logic for the "nyinteresse.html" page:
    if request.method == "POST":
        #   Get all the values that the user put into the input elements:
        form = EndreInteresseForm(request.POST)

        if form.is_valid():
            interesse = form.save(commit=False)
            interesse.navn = form.cleaned_data['navn']
            #   Create the new interest based on the user's given input values:
            interesse.save()
            return redirect("endre")
    else:
        #   If the user did not make a POST request just show the page with the appropriate input elements for creation of a new interest:
        form = EndreInteresseForm()
        context = {
            'form': form
        }
        #   Add information about the user's current color theme to the context, so that the values can be used in css:
        send_fargetema(request, context)
        return render(request, "studyadvisor/nyinteresse.html", context)


#   This view should only be available for veiledere:
@user_passes_test(veileder_check, login_url='home', redirect_field_name=None)
def nyttStudie(request):
    #   This view contains logic for the "nystudieretning.html" page:
    if request.method == "POST":
        #   Get all the values that the user put into the input elements:
        form = EndreStudieForm(request.POST)

        if form.is_valid():
            studie = form.save()
            studie.navn = form.cleaned_data['navn']
            studie.interesser.set(form.cleaned_data['interesser'])
            #   Create the new study based on the user's given input values:
            studie.save()
            return redirect("endre")
    else:
        #   If the user did not make a POST request just show the page with the appropriate input elements for creation of a new study:
        form = EndreStudieForm()
        context = {
            'form': form
        }
        #   Add information about the user's current color theme to the context, so that the values can be used in css:
        send_fargetema(request, context)
        return render(request, "studyadvisor/nystudieretning.html", context)


#   This view should only be available for veiledere:
@user_passes_test(veileder_check, login_url='home', redirect_field_name=None)
def endre(request):
    #   This view contains logic for the "endrestudint.html" page.

    #   The following context is used in the html page for displaying all interests and studies from the database in seperate lists:
    context = {
        'interesser': Interesser.objects.all().order_by('navn'),
        'studier': Studier.objects.all().order_by('navn')
    }
    #   Add information about the user's current color theme to the context, so that the values can be used in css:
    send_fargetema(request, context)
    return render(request, "studyadvisor/endrestudint.html", context)


#   This view should only be available for veiledere:
@user_passes_test(veileder_check, login_url='home', redirect_field_name=None)
def endreInteresse(request, id):
    #   This view contains logic for the "endreinteresse.html" page.

    #   The user has clicked on a interest that he wants to change. The interests id is sent as a parameter, and here it's used to get the interest:
    interesse = get_object_or_404(Interesser, pk=id)

    if request.method == "POST":
        #   Set form equal to what the user changed it to:
        form = EndreInteresseForm(request.POST, instance=interesse)

        #   If the user's specified input values are valid, then change the interest to use these new values:
        if form.is_valid():
            interesse = form.save(commit=False)
            interesse.navn = form.cleaned_data['navn']
            #   Save changes to the interest:
            interesse.save()
            return redirect("endre")
    else:
        #   If the user did not make a POST request just show the page with the appropriate input elements for editing of the specified interest:
        form = EndreInteresseForm(instance=interesse)
        context = {
            'form': form,
            'id': id
        }
        #   Add information about the user's current color theme to the context, so that the values can be used in css:
        send_fargetema(request, context)
        return render(request, "studyadvisor/endreinteresse.html", context)


#   This view should only be available for veiledere:
@user_passes_test(veileder_check, login_url='home', redirect_field_name=None)
def endreStudie(request, id):
    #   This view contains logic for the "endrestudie.html" page.

    #   The user has clicked on a study that he wants to change. The study id is sent as a parameter, and here it's used to get the study:
    studie = get_object_or_404(Studier, pk=id)

    if request.method == "POST":
        #   Set form equal to what the user changed it to:
        form = EndreStudieForm(request.POST, instance=studie)

        #   If the user's specified input values are valid, then change the study to use these new values:
        if form.is_valid():
            studie = form.save(commit=False)
            studie.navn = form.cleaned_data['navn']
            studie.interesser.set(form.cleaned_data['interesser'])
            #   Save changes to the study:
            studie.save()
            return redirect("endre")
    else:
        #   If the user did not make a POST request just show the page with the appropriate input elements for editing of the specified study:
        form = EndreStudieForm(instance=studie)
        context = {
            'form': form,
            'id': id
        }
        #   Add information about the user's current color theme to the context, so that the values can be used in css:
        send_fargetema(request, context)
        return render(request, "studyadvisor/endrestudie.html", context)


#   This view should only be available for veiledere:
@user_passes_test(veileder_check, login_url='home', redirect_field_name=None)
def slettInteresse(request, id):
    #   The user has clicked on an interest and pressed the delete button.
    #   The id of the interest is passed as a parameter and is used to get the interest:
    interesse = Interesser.objects.get(id=id)
    #   Delete the interest from database:
    interesse.delete()
    return redirect("endre")


#   This view should only be available for veiledere:
@user_passes_test(veileder_check, login_url='home', redirect_field_name=None)
def slettStudie(request, id):
    #   The user has clicked on a study and pressed the delete button.
    #   The id of the study is passed as a parameter and is used to get the study:
    studie = Studier.objects.get(id=id)
    #   Delete the study from database:
    studie.delete()
    return redirect("endre")
