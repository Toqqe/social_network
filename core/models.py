from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import  MinLengthValidator
from django.contrib.auth.models import User as UserModel
# Create your models here.

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_img = models.ImageField(upload_to='profile_images', default='blank-usr-img.png')
    description = models.TextField(blank=True, max_length=250)
    following = models.ManyToManyField(User, related_name="following", blank=True)
    
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}"
        
    
class Post(models.Model):
    title = models.TextField(max_length=80, blank=True)
    image = models.ImageField(upload_to="post_images", null=True, blank=True)
    date_of_creation = models.DateField(auto_now=False, auto_now_add=True)
    content = models.TextField(validators=[MinLengthValidator(10)], max_length=2000)
    likes = models.ManyToManyField(User, related_name="postlikes", blank=True)

    author = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, related_name="user_created_posts")

    def __str__(self):
        return f"{self.title} - {self.id}"

class Comment(models.Model):
    user_name = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="user_commented_post")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=False, related_name="post_comment" )

    text = models.TextField(max_length=400)
    date_added = models.DateTimeField(auto_now=False,auto_now_add=True)

    reply = models.ForeignKey('self', null=True, related_name="replies", on_delete=models.CASCADE)

class Notification(models.Model):
    N_CHOICES = [(1,'Follow'),(2,'Comment'),(3,'Reply'), (4,'Like')]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_notification", blank=True, null=True)
    comment_id = models.OneToOneField(Comment,blank=True,null=True, on_delete=models.CASCADE)
    user_notify = models.ForeignKey(User,  on_delete=models.CASCADE, related_name="notification_to_user")
    user_notify_sender = models.ForeignKey(User,  on_delete=models.CASCADE, related_name="notification_from_user")
    type = models.IntegerField(choices=N_CHOICES)
    notification_text = models.CharField(max_length=100, blank=False)
    date = models.DateTimeField(auto_now=False, auto_now_add=True)


    def __str__(self):
        return f"{self.id} - {self.post} - {self.user_notify} - {self.user_notify_sender} - {self.type}"