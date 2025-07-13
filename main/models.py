from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    company = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    project_updates = models.BooleanField(default=True)
    investment_alerts = models.BooleanField(default=True)
    marketing_communications = models.BooleanField(default=False)

    # Privacy settings
    profile_visibility = models.CharField(max_length=20, choices=[
        ('public', 'Public'),
        ('registered', 'Registered Users'),
        ('private', 'Private')
    ], default='public')
    show_activity_status = models.BooleanField(default=True)
    show_investment_history = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_full_name(self):
        return self.user.get_full_name() or self.user.username

    def get_projects_count(self):
        return self.user.project_set.count()

    def get_total_funded(self):
        """Get total amount this user has received from investors"""
        from django.db.models import Sum
        total = Transaction.objects.filter(project__user=self.user).aggregate(Sum('amount_eth'))
        return total['amount_eth__sum'] or 0

    def get_investments_made(self):
        """Get total amount this user has invested in other projects"""
        from django.db.models import Sum
        total = Transaction.objects.filter(user=self.user).aggregate(Sum('amount_eth'))
        return total['amount_eth__sum'] or 0

    def get_investments_count(self):
        """Get number of investments this user has made"""
        return Transaction.objects.filter(user=self.user).count()

    def get_funded_projects_count(self):
        """Get number of projects this user has funded"""
        return Transaction.objects.filter(user=self.user).values('project').distinct().count()

    def get_success_rate(self):
        """Calculate success rate based on projects that reached their funding goal"""
        total_projects = self.get_projects_count()
        if total_projects == 0:
            return 0

        successful_projects = 0
        for project in self.user.project_set.all():
            if project.current_funding() >= project.funding_goal:
                successful_projects += 1

        return round((successful_projects / total_projects) * 100, 1)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        UserProfile.objects.create(user=instance)

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    description = models.TextField(max_length=200)
    problem = models.TextField(max_length=200, blank=True, null=True)
    market = models.TextField(max_length=200, blank=True, null=True)
    competition = models.TextField(max_length=200, blank=True, null=True)
    details = models.TextField(max_length=200, blank=True, null=True)
    stage = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    url = models.URLField(blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', null=True, blank=True)
    funding_goal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def current_funding(self):
        """Calculate total funding received for this project"""
        from django.db.models import Sum
        total = Transaction.objects.filter(project=self).aggregate(Sum('amount_eth'))
        return total['amount_eth__sum'] or 0
    
    def funding_percentage(self):
        """Calculate funding percentage"""
        if self.funding_goal <= 0:
            return 0
        return min(100, int((self.current_funding() / self.funding_goal) * 100))


class Position(models.Model):
    COMPENSATION_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('equity', 'Equity Split'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="positions")
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=200)
    compensation_type = models.CharField(max_length=10, choices=COMPENSATION_CHOICES, default='unpaid')
    def __str__(self):
        return f"{self.title} - {self.project.name}"
    



class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    experience = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.applicant.username} -> {self.position.title}"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Link to Django user
    user_address = models.CharField(max_length=42)  # MetaMask address
    tx_hash = models.CharField(max_length=66, unique=True)
    amount_eth = models.DecimalField(max_digits=10, decimal_places=5)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"{self.amount_eth} ETH from {self.user.username}"
        return f"{self.amount_eth} ETH from {self.user_address[:10]}..."


class Message(models.Model):
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"


# Add the Chat model for the chatbot
class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.message[:30]}'

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('application', 'Application'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('message', 'Message'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"
