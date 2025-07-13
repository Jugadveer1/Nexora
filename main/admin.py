from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Project, Position, Application, Message, Notification
# Unregister the default User admin
admin.site.unregister(User)

# Register it again (optionally with custom admin)
admin.site.register(User, UserAdmin)
admin.site.register(Project)
admin.site.register(Position)
admin.site.register(Application)
admin.site.register(Message)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']