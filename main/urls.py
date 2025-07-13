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
    path('api/chat/', views.chat_api, name='chat_api'),
    path('blog/', views.blog, name='blog'),
    path('messages/history/<int:application_id>/', views.message_history, name='message_history'),
    path('messages/send/', views.send_message, name='send_message'),
    path('chatbot-api/', views.chatbot_api, name='chatbot_api'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('applicant/messages/', views.applicant_messages_view, name='applicant_messages'),
    path('applications/update_status/', views.update_application_status, name='update_application_status'),
    # New pages
    path('about/', views.about, name='about'),
    path('features/', views.features, name='features'),
    path('contact/', views.contact, name='contact'),
    # User pages
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    # AI Mentorship
    path('ai-mentorship/', views.ai_mentorship, name='ai_mentorship'),
    path('ai-mentorship-api/', views.ai_mentorship_api, name='ai_mentorship_api'),
    # Analytics and Network
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('network/', views.network_explorer, name='network_explorer'),
    # Data Export
    path('export-data/', views.export_user_data, name='export_user_data'),
    # Notifications
    path('notifications/mark-all-read/', views.mark_notifications_read, name='mark_notifications_read'),
]
