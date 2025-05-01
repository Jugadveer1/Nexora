from django.db import models
from django.contrib.auth.models import User
# Create your models here.

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
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    experience = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.applicant.username} -> {self.position.title}"


class Transaction(models.Model):
    user_address = models.CharField(max_length=42)
    tx_hash = models.CharField(max_length=66, unique=True)
    amount_eth = models.DecimalField(max_digits=10, decimal_places=5)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
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
