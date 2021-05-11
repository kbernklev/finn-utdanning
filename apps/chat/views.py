from django.shortcuts import render, redirect
from .forms import SendMessageForm
from .models import Message, Chat
from apps.registration.models import Student
from apps.studyadvisor.views import send_fargetema


# Loads the basic chat page
def chatView(request):
    context = getChats(request)
    return render(request, "chat/chat.html", context)


# Gets all the chats that the user is a part of and the ones for meant for everyone
def getChats(request):
    user = request.user
    chats = Chat.objects.filter(participants=user).order_by('-last_message__sent_at')
    Alle = Student.objects.filter(username='Alle')  # User used instead of having all users in a chat you just have
    # this universal user
    allChat = Chat.objects.filter(participants__in=Alle)

    context = {
        'user': user,
        'chats': chats,
        'allChat': allChat,
        'chat': None,
    }
    send_fargetema(request, context)  # Makes sure either the global or personal color theme is used for the site
    return context


# Loads the requested chat
def loadChat(request, pk):
    chat = Chat.objects.all().filter(id=pk).first()  # Get's the requested chat
    user = request.user
    # If the send button is pushed
    if request.method == "POST":
        form = SendMessageForm(request.POST)
        # Form to send a message
        if form.is_valid():
            send = form.save(commit=False)
            send.from_user = user
            send.to_chat = chat
            send.message = form.cleaned_data['message']
            # Checks if the message sent is the command to close the chat and makes sure it's an admin or advisor that
            # uses the command
            if send.message == "!close" and (user.is_staff or user.groups.filter(name='veileder').exists()):
                send.message = "Denne chaten er nå lukket"  # Changes the message sent to display that the chat was closed
                chat.is_closed = True
                chat.save()
            send.save()
            updateChats()
        return redirect('chat', pk)  # Reloads the chat
    # Else the messages in the chat gets loaded
    context = getChats(request)
    messages = Message.objects.filter(to_chat=chat)  # Gets the messages sent to the requested chat
    alle = Student.objects.filter(username='Alle').first()
    check = [user, alle]  # List of users used to make sure if you're meant to see a chat
    form = SendMessageForm(request.POST)
    # Checks if a user is advisor, if so, adds the advisor user to the check list
    if user.groups.filter(name='veileder').exists():
        veileder = Student.objects.filter(username='Veileder').first()  # Universal advisor user,
        # instead of having all advisors in the chat
        check.append(veileder)
    x = 0
    # Checks if atleast one of the users in the check list is a participant of the chat
    for participant in chat.participants.all():
        if participant in check:
            x = 1
    if x == 0:
        # If none of the users were in the chat they get redirected back to the basic chat page and wont be able to load
        # the requested chat
        return redirect("chats")

    context.update({
        'Chat': chat,
        'messages': messages,
        'form': form,
    })
    return render(request, "chat/chat.html", context)


# Updates the chat objects to make sure they have all their messages
def updateChats():
    for chat in Chat.objects.all():
        chat.messages.set(Message.objects.filter(to_chat=chat))
        chat.last_message = chat.messages.last()
        chat.save()


# Loads the send Feedback page
def sendFeedback(request):
    # If the send button is pushed
    if request.method == "POST":
        form = SendMessageForm(request.POST)
        if form.is_valid():
            user = request.user
            # If the user isn't signed in the feedback is sent anonymously
            if not user.is_authenticated:
                user = Student.objects.filter(username='Anonym').first()
            admin = Student.objects.filter(username='Admin').first()  # Universal Admin user
            # Creates a new chat, sets the participants to be the user/anonymous and admin and sends the message
            chat = Chat.objects.create()
            chat.participants.set([admin, user])
            chat.is_feedback = True
            chat.save()
            send = form.save(commit=False)
            send.from_user = user
            send.to_chat = chat
            send.message = form.cleaned_data['message']
            send.save()
            updateChats()
        return redirect('home')  # Redirects to the front page after the message is sent
    # Else it gets and loads the form to send feedback
    form = SendMessageForm(request.POST)
    context = {
        'form': form,
    }
    send_fargetema(request, context)
    return render(request, "chat/sendFeedback.html", context)


# Loads the ask Adivsor page
def askAdvisor(request):
    user = request.user
    # Makes sure the user is signed in or else redirects to the front page
    if user.is_authenticated:
        # If the send button is pushed a new chat is created with the user and all the advisors
        if request.method == "POST":
            form = SendMessageForm(request.POST)
            if form.is_valid():
                veileder = Student.objects.filter(username='Veileder').first()
                chat = Chat.objects.create()
                chat.participants.set([veileder, user])
                pk = chat.id
                send = form.save(commit=False)
                send.from_user = user
                send.to_chat = chat
                send.message = form.cleaned_data['message']
                send.save()
                updateChats()
            return redirect('chat', pk)
        # Else it gets and loads the form to ask advisors
        form = SendMessageForm(request.POST)
        context = {
            'form': form,
        }
        send_fargetema(request, context)
        return render(request, "chat/askAdvisor.html", context)
    return redirect('home')


# Loads the message all page
def messageAll(request):
    user = request.user
    # Checks if user is admin or else redirects to the front page
    if user.is_staff:
        # If the send button is pushed a new chat is created with all users and sent from Admin
        if request.method == "POST":
            form = SendMessageForm(request.POST)
            if form.is_valid():
                alle = Student.objects.filter(username='Alle').first()
                admin = Student.objects.filter(username='Admin').first()
                chat = Chat.objects.create()
                chat.participants.set([alle])
                chat.is_closed = True
                chat.save()
                pk = chat.id
                send = form.save(commit=False)
                send.from_user = admin
                send.to_chat = chat
                send.message = form.cleaned_data['message']
                send.save()
                updateChats()
            return redirect('adminChat', pk)
        # Else it gets and loads the form to message all page
        form = SendMessageForm(request.POST)
        context = {
            'form': form,
        }
        send_fargetema(request, context)
        return render(request, "chat/messageAll.html", context)
    return redirect('home')


# Loads the basic advisor chat page
def advisorChatView(request):
    context = getAdvisorChats(request)
    return render(request, "chat/AdvisorInbox.html", context)


# Gets all the chats meant for advisors
def getAdvisorChats(request):
    user = request.user
    # Makes sure the user is either admin or advisor
    if user.is_staff or user.groups.all().filter(name='veileder').exists():
        chats = Chat.objects.filter(participants=user).order_by('-last_message__sent_at')
        admin = Student.objects.filter(username='Admin').first()
        veileder = Student.objects.filter(username='Veileder').first()
        # Gets all the chats with users
        veilederChats = Chat.objects.filter(participants=veileder).exclude(participants=admin)
        # Gets the chats the advisor is assigned to
        yourAssigned = veilederChats.filter(participants__username=user.username)
        # Gets all the chats an advisor har with admins
        chatsWithAdmin = Chat.objects.filter(participants=admin)
        chatsWithAdmin = chatsWithAdmin.filter(participants=veileder)
        chatsWithAdmin = chatsWithAdmin.filter(participants=user)

        context = {
            'user': user,
            'chats': chats,
            'veileder': veileder,
            'veilederChats': veilederChats,
            'yourAssigned': yourAssigned,
            'chatsWithAdmin': chatsWithAdmin,
            'chat': None,
        }
        send_fargetema(request, context)
        return context
    return redirect('chats')


# Loads the requested advisor chat
def loadAdvisorChat(request, pk):
    chat = Chat.objects.all().filter(id=pk).first()
    user = request.user
    # Makes sure the user is either admin or advisor, all advisors and admins can see all the advisor chats
    if user.is_staff or user.groups.all().filter(name='veileder').exists():
        if request.method == "POST":
            form = SendMessageForm(request.POST)
            if form.is_valid():
                # If the user isn't assigned to the chat and sends a message they automaticly gets assigned
                if not user in chat.participants.all():
                    chat.participants.add(user)
                    chat.is_assigned = True
                    chat.save()
                send = form.save(commit=False)
                send.from_user = user
                send.to_chat = Chat.objects.filter(id=pk).first()
                send.message = form.cleaned_data['message']
                # Checks if the close chat command is sent
                if send.message == "!close":
                    send.message = "Denne chaten er nå lukket"
                    chat.is_closed = True
                    chat.save()
                send.save()
                updateChats()
            return redirect('advisorChat', pk)
        context = getAdvisorChats(request)
        messages = Message.objects.filter(to_chat=chat)
        form = SendMessageForm(request.POST)

        context.update({
            'Chat': chat,
            'messages': messages,
            'form': form,
        })
        return render(request, "chat/AdvisorInbox.html", context)
    return redirect('chats')


# Loads the basic admin chat page
def adminChatView(request):
    context = getAdminChats(request)
    return render(request, "chat/AdminInbox.html", context)


# Gets all the chats meant for admins
def getAdminChats(request):
    user = request.user
    # Checks if the user is admin
    if user.is_staff:
        chats = Chat.objects.all()
        admin = Student.objects.filter(username='Admin').first()
        veileder = Student.objects.filter(username='Veileder').first()
        chatsWithAdmin = Chat.objects.filter(participants=admin)
        chatsWithAdmin = chatsWithAdmin.filter(participants=veileder)
        # Not also filtering on the user, because all the admins can see these messages
        context = {
            'user': user,
            'chats': chats,
            'admin': admin,
            'chatsWithAdmin': chatsWithAdmin,
            'chat': None,
        }
        send_fargetema(request, context)
        return context
    return redirect('chats')


# Loads the requested admin chat
def loadAdminChat(request, pk):
    chat = Chat.objects.all().filter(id=pk).first()
    user = request.user
    # Checks if the user is admin
    if user.is_staff:
        if request.method == "POST":
            form = SendMessageForm(request.POST)
            if form.is_valid():
                # If the user isn't assigned to the chat and sends a message they automaticly gets assigned
                if not user in chat.participants.all():
                    chat.participants.add(user)
                    chat.is_assigned = True
                    chat.save()
                send = form.save(commit=False)
                send.from_user = user
                send.to_chat = Chat.objects.filter(id=pk).first()
                send.message = form.cleaned_data['message']
                # Checks if the message is the close command
                if send.message == "!close":
                    send.message = "Denne chaten er nå lukket"
                    chat.is_closed = True
                    chat.save()
                send.save()
                updateChats()
            return redirect('advisorChat', pk)
        context = getAdminChats(request)
        messages = Message.objects.filter(to_chat=chat)
        form = SendMessageForm(request.POST)

        context.update({
            'Chat': chat,
            'messages': messages,
            'form': form,
        })
        return render(request, "chat/AdminInbox.html", context)
    return redirect('chats')


# Loads the ask admin page
def askAdmin(request):
    user = request.user
    # Checks if the user is signed in
    if user.is_authenticated:
        if request.method == "POST":
            form = SendMessageForm(request.POST)
            if form.is_valid():
                admin = Student.objects.filter(username='Admin').first()
                veileder = Student.objects.filter(username='Veileder').first()
                chat = Chat.objects.create()
                chat.participants.set([admin, veileder, user])
                pk = chat.id
                send = form.save(commit=False)
                send.from_user = user
                send.to_chat = chat
                send.message = form.cleaned_data['message']
                send.save()
                updateChats()
            return redirect('advisorChat', pk)
        form = SendMessageForm(request.POST)
        context = {
            'form': form,
        }
        send_fargetema(request, context)
        return render(request, "chat/askAdmin.html", context)
    return redirect('home')
