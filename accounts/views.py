from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    CreateView,
    TemplateView,
    UpdateView,
    DetailView,
    ListView,
)
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render

from .forms import SigninForm, SignUpForm, ProfileEditForm
from .models import Profile, FriendShip
from tweets.models import Tweet, Like


User = get_user_model()


class SignUpView(CreateView):
    template_name = "accounts/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("accounts:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password1"]
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            return response


class WelcomeView(TemplateView):
    template_name = "welcome/index.html"


class HomeView(ListView):
    template_name = "accounts/home.html"
    context_object_name = "tweets"
    model = Tweet
    queryset = (
        Tweet.objects.select_related("user")
        .prefetch_related("like_set")
        .order_by("-created_at")
    )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["followings"] = FriendShip.objects.select_related(
            "following", "followed"
        ).filter(following=self.request.user)
        ctx["liked_list"] = Like.objects.filter(user=self.request.user).values_list(
            "tweet", flat=True
        )
        return ctx


class SigninView(LoginView):
    form_class = SigninForm
    template_name = "accounts/signin.html"


class SignoutView(LogoutView):
    template_name = "accounts/signin.html"


class UserProfileView(LoginRequiredMixin, DetailView):
    template_name = "accounts/profile.html"
    model = Profile
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tweets = (
            Tweet.objects.select_related("user")
            .filter(user=self.request.user)
            .prefetch_related("like_set")
            .order_by("-created_at")
        )
        ctx["tweets"] = tweets
        ctx["followings_num"] = (
            FriendShip.objects.select_related("following", "followed")
            .filter(following=self.request.user)
            .count()
        )
        ctx["followers_num"] = (
            FriendShip.objects.select_related("following", "followed")
            .filter(followed=self.request.user)
            .count()
        )
        ctx["liked_list"] = Like.objects.filter(user=self.request.user).values_list(
            "tweet", flat=True
        )
        return ctx


class UserProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "accounts/profile_edit.html"
    model = Profile
    form_class = ProfileEditForm

    def get_success_url(self):
        return reverse("accounts:user_profile", kwargs={"pk": self.object.pk})

    def test_func(self):
        profile = self.get_object()
        return self.request.user == profile.user


class FollowView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/follow.html"
    model = FriendShip

    def post(self, request, *args, **kwargs):
        try:
            following = User.objects.get(username=request.user.username)
            followed = User.objects.get(username=self.kwargs["username"])
            if following == followed:
                messages.warning(request, "自分自身はフォローできません。")
                return render(request, "accounts/follow.html")
            elif FriendShip.objects.filter(
                following=following, followed=followed
            ).exists():
                messages.warning(request, "すでにフォローしています。")
                return render(request, "accounts/follow.html")
            else:
                FriendShip.objects.create(following=following, followed=followed)
                return HttpResponseRedirect(reverse_lazy("accounts:home"))
        except User.DoesNotExist:
            messages.error(request, "存在しないユーザーです。")
            raise Http404


class UnFollowView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/unfollow.html"

    def post(self, request, *args, **kwargs):
        try:
            following = User.objects.get(username=request.user.username)
            followed = User.objects.get(username=self.kwargs["username"])
            if following == followed:
                messages.warning(request, "自分自身はフォロー解除できません。")
                return render(request, "accounts/unfollow.html")
            elif FriendShip.objects.filter(
                following=following, followed=followed
            ).exists():
                FriendShip.objects.filter(
                    following=following, followed=followed
                ).delete()
                return HttpResponseRedirect(reverse_lazy("accounts:home"))
            else:
                messages.warning(request, "無効な操作です。")
                return render(request, "accounts/unfollow.html")
        except User.DoesNotExist:
            messages.error(request, "存在しないユーザーです。")
            raise Http404


class FollowingListView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/following_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["followings"] = FriendShip.objects.select_related(
            "following", "followed"
        ).filter(following=self.request.user)
        return ctx


class FollowerListView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/follower_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["followings"] = FriendShip.objects.select_related(
            "following", "followed"
        ).filter(following=self.request.user)
        ctx["followers"] = FriendShip.objects.select_related(
            "following", "followed"
        ).filter(followed=self.request.user)
        return ctx
