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

from .forms import LoginForm, SignUpForm, ProfileEditForm
from .models import Profile, FriendShip
from tweets.models import Tweet

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
    queryset = Tweet.objects.select_related("user").order_by("-created_at")


class LoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            return response


class LogoutView(LogoutView):
    template_name = "accounts/login.html"


class UserProfileView(LoginRequiredMixin, DetailView):
    template_name = "accounts/profile.html"
    model = Profile
    context_object_name = "profile"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tweets"] = (
            Tweet.objects.select_related("user")
            .filter(user=self.request.user)
            .order_by("-created_at")
        )
        return ctx


class UserProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "accounts/profile_edit.html"
    model = Profile
    form_class = ProfileEditForm

    def get_success_url(self):
        return reverse("accounts:user_profile", kwargs={"pk": self.object.pk})

    def test_func(self):
        if Profile.objects.filter(pk=self.kwargs["pk"]).exists():
            current_user = self.request.user
            return current_user.pk == self.kwargs["pk"]
        else:
            raise Http404


class FollowView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/follow.html"
    model = FriendShip

    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(username=self.request.user.username)
            following = User.objects.get(username=self.kwargs["username"])
        except User.DoesNotExist:
            # フォローするユーザーが存在しないとき
            messages.warning(request, "存在しないユーザーです。")
            return HttpResponseRedirect(reverse_lazy("accounts:home"))
        if user == following:
            # 自分自身をフォローしたときの動作
            messages.warning(request, "自分自身はフォローできません。")
        else:
            instance = FriendShip.objects.create(user=user)
            instance.following.add(following)

        return HttpResponseRedirect(reverse_lazy("accounts:home"))


class UnFollowView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/unfollow.html"

    # def post(self, request, *args, **kwargs):
    #     try:
    #         user = User.objects.get(username=self.request.user.username)
    #         following = User.objects.get(username=self.kwargs["username"])
    #     except User.DoesNotExist:
    #         # フォローするユーザーが存在しないとき
    #         messages.warning(request, "存在しないユーザーです。")
    #         return HttpResponseRedirect(reverse_lazy("accounts:home"))
    #     if user == following:
    #         # 自分自身をフォローしたときの動作
    #         messages.warning(request, "自分自身はフォローできません。")
    #         pass
    #     else:
    #         instance = FriendShip.objects.create(user=user)
    #         instance.following.add(following)

    # return HttpResponseRedirect(reverse_lazy("accounts:home"))


class FollowingListView(TemplateView):
    template_name = "accounts/following_list.html"


class FollowerListView(TemplateView):
    template_name = "accounts/follower_list.html"
