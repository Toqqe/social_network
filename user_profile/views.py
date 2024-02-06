

from django.shortcuts import get_object_or_404, render, HttpResponseRedirect, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from core.models import Profile, Post, Notification
from django.views import View
from django.contrib.auth.models import User
from core.forms import AddPost, CommentForm
from django.http import JsonResponse
from django.template.loader import render_to_string
from .forms import UpdateUserForm, UpdateProfileform
from django.core.paginator import Paginator
# Create your views here.

def is_user_authenticated(user, user_request):
    is_user_same_as_authenticated = False
    
    if user == user_request:
        is_user_same_as_authenticated = True

    return is_user_same_as_authenticated


def is_following(user_follower, user_following):

    is_following = False
    selected_user_obj = Profile.objects.get(pk=user_following) ## Cały obiekt danego usera
    current_user_profile_obj = Profile.objects.get(pk=user_follower) ## Cały obiekt zalogowanego usera

    if current_user_profile_obj.user in selected_user_obj.following.all():
        is_following = True
    else:
        is_following = False

    return is_following


@method_decorator(login_required(login_url='/login'), name='dispatch')
class ProfileDetailView(View):
    def get(self, request, user):
        comment_form = CommentForm()
        user = get_object_or_404(User, username=user)
        user_profile = user.profile
        user_posts = user_profile.user_created_posts.all().order_by("-id") ## Wszystkie posty utworzone przez X usera
        is_user_same_as_authenticated = is_user_authenticated(user, request.user)
        following = is_following(user_profile.id, request.user.id)
    

        paginator = Paginator(user_posts, 5) 
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "following" : following,
            "user_profile": user_profile,
            "is_user_same_as_authenticated": is_user_same_as_authenticated,
            "comment_form": comment_form,
            "notifications_read": request.user.notification_to_user.all().exclude(user_notify_sender=request.user),
            "page_obj":page_obj

        }

        if is_user_same_as_authenticated:
            add_post_on_wall = AddPost()
            context["add_post_on_wall"] = add_post_on_wall

        return render(request, "user_profile/user-profile.html", context)
    


    def post(self, request, user):
        
        user = get_object_or_404(User, username=user)
        is_user_same_as_authenticated = is_user_authenticated(user, request.user)
        user_profile = user.profile
        user_posts = user_profile.user_created_posts.all().order_by("-id")
        following = is_following(user_profile.id, request.user.id)

        comment_form = CommentForm()
        add_post_on_wall = AddPost()

        if "title" in request.POST or "content" in request.POST: 
            add_post_on_wall = AddPost(request.POST)

            if add_post_on_wall.is_valid():

                comment_form = CommentForm()

                post = add_post_on_wall.save(commit=False)
                post.author = request.user.profile
                post.image = request.FILES.get('image')
                post.save()

                post_html = render_to_string('user_profile/includes/post.html', {'post': post, "comment_form": comment_form}, request=request)

                return JsonResponse({'status': 'ok', 'post_html': post_html})
            else:
                # Zwracanie informacji o błędach formularza
                errors = add_post_on_wall.errors.as_json()
                return JsonResponse({'status': 'error', 'errors': errors})

            
        if "text" in request.POST:
            add_comment = CommentForm(request.POST)


            if add_comment.is_valid():
                commented_post_pk = request.POST['post_pk']
                post_object = Post.objects.get(pk=commented_post_pk)

                comment = add_comment.save(commit=False)
                comment.user_name = request.user
                comment.post = post_object

                notification = Notification(post=post_object, user_notify_sender=request.user, notification_text=comment.text, user_notify=post_object.author.user, type=2)
                notification.save()

                comment.save()

                return HttpResponseRedirect(reverse("post-detail-page", args=[commented_post_pk]))

        if "profile_pk" in request.POST:

            add_post_on_wall = AddPost()

            
            current_user_profile_obj = Profile.objects.get(user=request.user) ## Cały obiekt profilu zalogowanego usera

            selected_user_profile_pk = request.POST.get('profile_pk') ## Id klienta, u którego kliknięty był follow
            selected_user_obj = Profile.objects.get(pk=selected_user_profile_pk)
       

            if current_user_profile_obj in selected_user_obj.user.following.all():
                current_user_profile_obj.following.remove(selected_user_obj.user)
                notification = Notification.objects.filter(user_notify_sender=request.user, type=1)
                notification.delete()

            else:
                current_user_profile_obj.following.add(selected_user_obj.user)
                notification = Notification(user_notify=selected_user_obj.user, user_notify_sender=request.user, type=1)
                notification.save()
            
            following = is_following(selected_user_profile_pk, request.user.id)

        context = {
            "following" : following,
            "user_profile": user_profile,
            "page_obj": user_posts,
            "is_user_same_as_authenticated": is_user_same_as_authenticated,
            "add_post_on_wall" : add_post_on_wall,
            "comment_form": comment_form,
            "notifications_read": request.user.notification_to_user.all().exclude(user_notify_sender=request.user)
        }

        return render(request, "user_profile/user-profile.html", context)



@login_required(login_url='/login')
def index(request):
    active_user = str(request.user.profile.user).lower()
    redirect_path = reverse("user-profile", args=[active_user])
    return HttpResponseRedirect(redirect_path)


@login_required(login_url='/login')
def search(request):

    if "search_query" not in request.POST:
        forwarded_value = ""
    else:
        forwarded_value = request.POST['search_query']

    users = User.objects.filter(username__contains=forwarded_value).exclude(is_superuser=True).order_by("username") ## Wszyscy, którzy zawierają podaną frazę w wyszkiwarce

    current_user_profile = Profile.objects.get(user=request.user) ## Profil obecnego użytkownika

    following_users_pk = current_user_profile.following.all().values_list('pk', flat=True) ## Obecni obserwujący naszego użytkownika
    filered_users_by_shared_follows = User.objects.filter(following__pk__in=following_users_pk).order_by("-id") ## użytkownicy, którzy sa obserwowani przez naszych obserwujących

    paginator = Paginator(users, 20) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    context = {
        "users": page_obj,
        "shared_proifles":filered_users_by_shared_follows,
        "all_current_user_follows":current_user_profile.following.all(),
        "user_profile": current_user_profile,
        "notifications_read": request.user.notification_to_user.all().exclude(user_notify_sender=request.user)
    }

    return render(request, "user_profile/search.html", context)



@login_required(login_url='/login')
def user_settings(request):
    active_user_profile = Profile.objects.get(pk=request.user.id)

    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user, user=request.user)
        profile_form = UpdateProfileform(request.POST, request.FILES, instance=request.user.profile)

        if "clear-img" in request.POST:
            tmp_profile_form = profile_form.save(commit=False)
            tmp_profile_form.profile_img = '/blank-usr-img.png'
            tmp_profile_form.save()
            return redirect('user-settings')
    
        if user_form.is_valid() and profile_form.save():

            user_form.save() 
            profile_form.save() 
            return redirect('user-settings')
        
    else:

        user_form = UpdateUserForm(instance=request.user, user=request.user)
        profile_form = UpdateProfileform(instance=request.user.profile)

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "user_profile" : active_user_profile,
        "notifications_read": request.user.notification_to_user.all().exclude(user_notify_sender=request.user)
    }

    return render(request, 'user_profile/settings.html', context )



@login_required(login_url='/login')
def notifications(request):
    user = request.user
    user_notify = Notification.objects.filter(user_notify=user).order_by('-date').exclude(user_notify_sender=user)

    if "hide_not_v" in request.POST:
        not_value = request.POST['hide_not_v']
        notification_obj = Notification.objects.get(pk=not_value)
        notification_obj.delete()
    
    if "hide_delete_all" in request.POST:
        user_notify.delete()

    paginator = Paginator(user_notify, 20) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    notfications_read = request.user.notification_to_user.all().exclude(user_notify_sender=user)


    context = {
        "notify" : page_obj,
        "user_profile" : user.profile,
        "notifications_read": notfications_read
    }

    return render(request, 'user_profile/notifications.html', context)