from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.messages import constants as messages_constants
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/polls/'), name='index'),
    path('polls/', include('polls.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
]


MESSAGE_TAGS = {
    messages_constants.ERROR: 'danger',
}

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
