from typing import Any, Dict
from django.shortcuts import render, HttpResponseRedirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.views import View
from .forms import AddPost, CommentForm, RegisterForm, UpdatePost
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy , reverse
from .models import Post, Profile, User, Comment, Notification
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic import DetailView, DeleteView
from django.views.generic.edit import UpdateView
from django.db.models import Q
from django.core.paginator import Paginator
# Create your views here.


def filtered_posts(active_site_user):

    if str(active_site_user) != "mateusz":
        active_user_profile = Profile.objects.get(pk=active_site_user.id) 
        following_users_pk = active_user_profile.following.all().values_list('pk', flat=True)
        filtered_posts_by_following_users = Post.objects.filter(author__pk__in=following_users_pk ).order_by("-date_of_creation")

        posts_by_user = active_user_profile.user_created_posts.all().order_by("-id")

        merge_list = filtered_posts_by_following_users | posts_by_user

    else:
        merge_list = None
    
    return merge_list.order_by("-id")

def shared_followers(current_user):
    current_user_profile = Profile.objects.get(pk=current_user.id)
    following_users_pk = current_user_profile.following.all().values_list('pk', flat=True) ## Obecni obserwujący naszego użytkownika
    filered_users_by_shared_follows = User.objects.filter(following__pk__in=following_users_pk).order_by("-id") ## użytkownicy, którzy sa obserwowani przez naszych obserwujących
    final_list = filered_users_by_shared_follows.exclude(Q(id__in=following_users_pk.values_list('id', flat=True)) | Q(username=current_user_profile.user))
    
    return final_list.distinct()




@method_decorator(login_required(login_url='/login'), name='dispatch')
class MainFeedbackWallView(View):
    def get(self, request):

        
        if str(request.user) == "mateusz":
            all_posts = Post.objects.all().order_by("-id")
            context = {
            "all_posts" : all_posts,
            }
            return render(request, "core/index.html", context)
        
        else:

            add_post_form = AddPost()
            comment_form = CommentForm()

            filtered_users = shared_followers(request.user)
            filtered_posts_by_following_users = filtered_posts(request.user)

            paginator = Paginator(filtered_posts_by_following_users, 5) 
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
            context = {
                "filtered_users": filtered_users,
                "add_post_form": add_post_form,
                "comment_form" : comment_form,
                "notifications_read": request.user.notification_to_user.all().exclude(user_notify_sender=request.user),
                "page_obj":page_obj
            }

            return render(request, "core/index.html", context)

    def post(self, request):

        add_post_form = AddPost()
        all_posts = Post.objects.all().order_by("-date_of_creation")
        filtered_posts_by_following_users = filtered_posts(request.user)

        if "title" in request.POST or "content" in request.POST:
            add_post_form = AddPost(request.POST)

            if add_post_form.is_valid():

                add_comment = CommentForm()

                post = add_post_form.save(commit=False)
                post.author = request.user.profile
                post.image = request.FILES.get('image')
                post.save()

                post_html = render_to_string('core/includes/post.html', {'post': post, "comment_form": add_comment}, request=request)

                return JsonResponse({'status': 'ok', 'post_html': post_html})
            else:
                # Zwracanie informacji o błędach formularza
                errors = add_post_form.errors.as_json()
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
        
        if "post_id" in request.POST:
            post_obj = get_object_or_404(Post, id=request.POST.get('post_id'))

            if post_obj.likes.filter(id=request.user.id).exists():
                post_obj.likes.remove(request.user)
                notification = Notification.objects.filter(post=post_obj, user_notify_sender=request.user, type=4)
                notification.delete()
            else:
                post_obj.likes.add(request.user)
                notification = Notification(post=post_obj, user_notify_sender=request.user , user_notify=post_obj.author.user, type=4)
                notification.save()
            
            context = {
                'post':post_obj,
            }

            like_html = render_to_string('core/includes/like.html', context, request=request)

            return JsonResponse({'like_html': like_html })


        context = {
            "posts": all_posts,
            "add_post_form": add_post_form,
            "users_filtered_posts": filtered_posts_by_following_users,
            "notifications_read": request.user.notification_to_user.all()
        }
        return render(request, "core/index.html", context)




class SignupPageView(View):
    def get(self, request):
        register_form = RegisterForm()

        return render(request, "core/register.html", {
            "register_form": register_form
        })
    
    def post(self, request):
        
        register_form = RegisterForm(request.POST)  

        if register_form.is_valid():

            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password1']

            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            user_login = authenticate(username=username, password=password)
            login(request, user_login)

            user_model = User.objects.get(username=username)                                                ## Pobieramy model Usera, który został utworzony powyżej w modelu "User"
            new_profile = Profile.objects.create(user=user_model, id=user_model.id)                         ## Tworzymy na podstawie "user_model" obiekt w naszym modelu Profile
            new_profile.save()

            return HttpResponseRedirect("/")
        else:
            return render(request, "core/register.html", {
                "register_form": register_form
            })
        

@method_decorator(login_required(login_url='/login'), name='dispatch')
class PostDetailView(DetailView):
    template_name = "core/post-detail.html"
    model = Post


    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)
        post_object = context['post']

        context['comments'] = post_object.post_comment.all().order_by('-id')
        context['notifications_read'] = self.request.user.notification_to_user.all().exclude(user_notify_sender=self.request.user)
        context['comment_form'] = CommentForm()
        
        return context

    def post(self, request, pk):
        
        if "text" in request.POST:
            add_comment = CommentForm(request.POST)

            if add_comment.is_valid():
                post_object = Post.objects.get(pk=pk)

                comment = add_comment.save(commit=False)
                comment.user_name = request.user
                comment.post = post_object
                comment.save()

                notification = Notification(user_notify=post_object.author.user, notification_text=comment.text , user_notify_sender=request.user, post=post_object,type=2)
                notification.save()

        if "comment-reply" in request.POST:

            parent_comment_id = request.POST.get('comment_id')
            comment_reply_text = request.POST.get('comment-reply')
            post_object = Post.objects.get(pk=pk)
            comment_parent_object = Comment.objects.get(pk=parent_comment_id)
            user_name = request.user

            comment = Comment.objects.create(user_name=user_name,post=post_object,text=comment_reply_text, reply=comment_parent_object)
            comment.save()
            


            if comment_parent_object.user_name == post_object.author.user:
                notification = Notification(user_notify=post_object.author.user, comment_id = comment , notification_text=comment_reply_text ,user_notify_sender=request.user, post=post_object, type=3)
                notification.save()
        
        if "comment_pk" in request.POST:

            commend_id = request.POST.get('comment_pk')
            instance = Comment.objects.get(pk=commend_id)

            post_instance = Post.objects.get(pk=instance.post.id)

            notification = Notification.objects.filter(user_notify_sender=request.user, notification_text=instance.text, type=2)
            notification.delete()

            instance.delete()
        
        if "reply_pk" in request.POST:
            reply_id = request.POST.get('reply_pk')
            instance = Comment.objects.get(pk=reply_id)

            post_instance = Post.objects.get(pk=instance.post.id)
            
            notification = Notification.objects.filter(post=post_instance, comment_id = instance.id, user_notify_sender=request.user,  type=3)##, date=instance.date_added)
            notification.delete()

            instance.delete()

        return HttpResponseRedirect(reverse("post-detail-page", args=[pk]))
        
@method_decorator(login_required(login_url='/login'), name='dispatch')
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/profile'
    
    def test_func(self):
        post = self.get_object()
        if self.request.user.profile == post.author:
            return True
        return False

@method_decorator(login_required(login_url='/login'), name='dispatch')
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = UpdatePost
    template_name = "core/post_from.html"

    def form_valid(self, form):
        form.instance.author = self.request.user.profile
        return super().form_valid(form)
    
    def get_success_url(self):
          post_pk=self.kwargs['pk']
          return reverse_lazy('post-detail-page', kwargs={'pk': post_pk})
    
    def get_context_data(self, **kwargs):
        context = super(PostUpdateView, self).get_context_data(**kwargs)
        context['notifications_read'] = self.request.user.notification_to_user.all().exclude(user_notify_sender=self.request.user)
        return context


    def test_func(self):
        post = self.get_object()

        if self.request.user.profile == post.author:
            return True
        return False
    

@login_required(login_url='/login')
def liked_posts(request):
    user = request.user
    user_liked_posts = user.postlikes.all()

    paginator = Paginator(user_liked_posts, 20) 
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)


    context = {
        "liked_posts" : user_liked_posts,
        "page_obj":page_obj,
        'notifications_read' : request.user.notification_to_user.all().exclude(user_notify_sender=request.user)
    }

    return render(request, 'core/liked-posts.html', context)