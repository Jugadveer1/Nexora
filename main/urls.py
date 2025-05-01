from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # No login required for home
    path('login/', views.login_page, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('apply/', views.submit_application, name='submit_application'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('save-transaction/', views.save_transaction, name='save_transaction'),
    path('project-funding/<int:project_id>/', views.get_project_funding, name='project_funding'),
    path('chatbot-api/', views.chatbot_api, name='chatbot_api'),
    path('blog/', views.blog, name='blog'),
    path('messages/history/<int:application_id>/', views.message_history, name='message_history'),
    path('messages/send/', views.send_message, name='send_message'),
    
]
