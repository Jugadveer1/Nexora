from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Project, Position, Application, Transaction, Chat, Message, UserProfile, Notification
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import json
from django.db import models
import os
from dotenv import load_dotenv
import logging
from django.utils import timezone
from django.views.decorators.http import require_POST
from decimal import Decimal
import requests
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import io
from django.db.models.functions import TruncMonth, TruncDay
# Load .env variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Groq client if API key is available
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
try:
    from groq import Groq
    if GROQ_API_KEY:
        groq_client = Groq(api_key=GROQ_API_KEY)
    else:
        logger.warning("Missing GROQ_API_KEY in environment variables!")
except ImportError:
    logger.warning("Groq package not installed. Install with: pip install groq")
    groq_client = None

def ask_groqcloud(message):
    """Send a message to Groq API and get a response"""
    if not groq_client:
        return "AI service is currently unavailable. Please try again later."
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a startup funding platform. Provide concise, helpful answers about startups, funding, and entrepreneurship."},
                {"role": "user", "content": message},
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return "Sorry, I'm having trouble connecting to my brain right now. Please try again later."

@login_required
def chatbot_api(request):
    """Handle chatbot API interactions"""
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()

        if message:
            try:
                response = ask_groqcloud(message)
                chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
                chat.save()
                return JsonResponse({'message': message, 'response': response})
            except Exception as e:
                logger.error(f"Chatbot API error: {e}")
                return JsonResponse({'error': 'Failed to get response from AI. Please try again later.'}, status=500)
        else:
            return JsonResponse({'error': 'Empty message'}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# Create your views here.

def blog(request):
    return render(request, 'blog.html')

def your_view(request):
    step_labels = ["Description", "Problem", "Market", "Competition", "(Details)"]
    return render(request, "home.html", {"step_labels": step_labels})


# Home view that works for both authenticated and non-authenticated users
def home(request):
    # If user is not authenticated, show the landing page without login modal
    if not request.user.is_authenticated:
        return render(request, 'home.html')
    
    # For authenticated users, show their projects
    query = request.GET.get('q', '')
    category = request.GET.get('category')
    stage = request.GET.get('stage')
    mine = request.GET.get('mine') == '1'
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            market = request.POST.get('market')
            problem = request.POST.get('problem')
            competition = request.POST.get('competition')
            details = request.POST.get('details')
            stage = request.POST.get('stage')
            category = request.POST.get('category')
            url = request.POST.get('url')
            banner = request.FILES.get('banner')
            funding_goal = request.POST.get('funding_goal', 0)

            # Validate required fields
            if not name or not description or not stage or not category:
                messages.error(request, "Please fill in all required fields.")
                return render(request, 'home.html')

            # Create the project (single creation, not duplicate)
            project = Project.objects.create(
                user=request.user,
                name=name,
                description=description,
                market=market,
                problem=problem,
                competition=competition,
                details=details,
                stage=stage,
                category=category,
                url=url,
                banner=banner,
                funding_goal=funding_goal
            )


            # Parse positions JSON
            try:
                positions_data = json.loads(request.POST.get('positions_json', '[]'))
                if not isinstance(positions_data, list):
                    positions_data = []
            except json.JSONDecodeError:
                # Handle invalid JSON by defaulting to empty list
                positions_data = []

            # Create positions for the project
            for pos in positions_data:
                if isinstance(pos, dict) and all(key in pos for key in ['title', 'description', 'compensation_type']):
                    Position.objects.create(
                        project=project,
                        title=pos['title'],
                        description=pos['description'],
                        compensation_type=pos['compensation_type']
                    )

            messages.success(request, f"Project '{name}' created successfully!")
            return redirect('home')

        except Exception as e:
            messages.error(request, f"Error creating project: {str(e)}")
            return render(request, 'home.html')
    # ENHANCED SEARCH AND FILTERING
    query = request.GET.get('q', '').strip()
    projects = Project.objects.all()

    if query:
        projects = projects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(problem__icontains=query) |
            Q(market__icontains=query) |
            Q(competition__icontains=query) |
            Q(details__icontains=query)
        )

    if category:
        projects = projects.filter(category__iexact=category)

    if stage:
        projects = projects.filter(stage__iexact=stage)

    if mine:
        projects = projects.filter(user=request.user)

    projects = projects.order_by('-created_at')

    # Add funding percentage calculation for each project
    for project in projects:
        if project.funding_goal > 0:
            current_funding = project.current_funding()
            project.funding_percentage = min(100, (current_funding / project.funding_goal) * 100)
        else:
            project.funding_percentage = 0
    # Add unread message count if user is authenticated
    unread_messages_count = 0
    if request.user.is_authenticated:
        # Count unread messages for projects owned by the user
        project_applications = Application.objects.filter(position__project__user=request.user)
        unread_messages_count = Message.objects.filter(
            application__in=project_applications,
            recipient=request.user,
            is_read=False
        ).count()
    
    context = {
        'projects': projects,
        'query': query,
        'selected_category': category,
        'selected_stage': stage,
        'mine': mine,
        'unread_messages_count': unread_messages_count
    }
    
    return render(request, 'home.html', context)




# Ensure only authenticated users can access this view
# @login_required
# def home(request):
#     if request.method == 'POST' and request.user.is_authenticated:
#         name = request.POST.get('name')
#         description = request.POST.get('description')
#         market = request.POST.get('market')
#         problem = request.POST.get('problem')
#         competition = request.POST.get('competition')
#         details = request.POST.get('details')
#         stage = request.POST.get('stage')
#         category = request.POST.get('category')
#         url = request.POST.get('url')
#         banner = request.FILES.get('banner')
        
        
#         funding_goal = request.POST.get('funding_goal', 0)
#         project=Project.objects.create(
#             user=request.user,
#             name=name,
#             description=description,
#             market=market,
#             problem=problem,
#             competition=competition,
#             details=details,
#             stage=stage,
#             category=category,
#             url=url,
#             banner=banner,
#             funding_goal=funding_goal 
#         )
        
#         # Parse positions JSON
#         positions_data = json.loads(request.POST.get('positions_json', '[]'))
#         for pos in positions_data:
#             Position.objects.create(
#                 project=project,
#                 title=pos['title'],
#                 description=pos['description'],
#                 compensation_type=pos['compensation_type']
#             )

#         return redirect('home')  # Make sure your URL name is 'home'
#     projects = Project.objects.all().order_by('-created_at')  # Show newest first
#     return render(request, 'home.html', {'projects': projects})



# Login view
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'Username does not exist')
            return render(request, 'home.html', {'show_login': True})
        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(request, 'Invalid password')
            return render(request, 'home.html', {'show_login': True})
        login(request, user)
        return redirect('home')
    # For GET requests, show the login modal
    return render(request, 'home.html', {'show_login': True})

# Register view
def register_user(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already in use')
            return render(request, 'home.html', {'show_register': True})

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        login(request, user)
        return redirect('home')

    # For GET requests, show the register modal
    return render(request, 'home.html', {'show_register': True})

# Logout view
def logout_view(request):
    logout(request)
    return redirect('home')



@login_required
def submit_application(request):
    if request.method == 'POST':
        position_id = request.POST.get('position_id')
        reason = request.POST.get('reason')
        experience = request.POST.get('experience')

        position = get_object_or_404(Position, id=position_id)

        # Check for duplicate application (optional)
        existing = Application.objects.filter(position=position, applicant=request.user)
        if existing.exists():
            messages.warning(request, "You have already applied for this position.")
            return redirect('home')

        application = Application.objects.create(
            position=position,
            applicant=request.user,
            reason=reason,
            experience=experience
        )

        # Create initial message from applicant to project owner
        initial_message_content = f"Hi! I'm interested in the {position.title} position for your project '{position.project.name}'.\n\nReason for applying: {reason}"
        if experience:
            initial_message_content += f"\n\nMy experience: {experience}"

        Message.objects.create(
            application=application,
            sender=request.user,
            recipient=position.project.user,
            content=initial_message_content
        )

        # Create notification for project owner
        Notification.objects.create(
            user=position.project.user,  # Project owner
            title="New Application Received",
            message=f"{request.user.username} applied for {position.title} position in your project '{position.project.name}'",
            notification_type="application",
            related_object_id=application.id
        )

        messages.success(request, "Application submitted successfully.")
        return redirect('home')
    

# @login_required
# def notifications_view(request):
#     applications = Application.objects.filter(
#         position__project__user=request.user
#     ).select_related('position', 'position__project', 'applicant').order_by('-created_at')

#     return render(request, 'notifications.html', {'applications': applications})



@login_required
def notifications_view(request):
    from collections import defaultdict
    from .models import Project, Application
    from django.db.models import Q

    # Get search and filter parameters
    search_project = request.GET.get('search_project', '')
    filter_status = request.GET.get('filter_status', '')
    search_applicant = request.GET.get('search_applicant', '')

    # Start with user's projects
    user_projects = Project.objects.filter(user=request.user)\
        .prefetch_related('positions')\
        .order_by('-created_at')

    # Filter projects by search term if provided
    if search_project:
        user_projects = user_projects.filter(name__icontains=search_project)

    # Get applications for these projects
    applications = Application.objects.filter(
        position__project__in=user_projects
    ).select_related('position', 'position__project', 'applicant')\
     .order_by('-created_at')

    # Filter by status if provided
    if filter_status:
        applications = applications.filter(status=filter_status)

    # Filter by applicant username if provided
    if search_applicant:
        applications = applications.filter(applicant__username__icontains=search_applicant)

    # Add unread message counts
    for app in applications:
        unread_count = Message.objects.filter(
            application=app,
            recipient=request.user,
            is_read=False
        ).count()
        app.has_unread = unread_count > 0
        app.unread_count = unread_count

    grouped_apps = defaultdict(list)
    for app in applications:
        grouped_apps[app.position.project].append(app)

    # Maintain project order while grouping
    project_data = [(project, grouped_apps.get(project, [])) for project in user_projects]

    # Get all user projects for the search dropdown
    all_user_projects = Project.objects.filter(user=request.user).order_by('name')

    context = {
        'grouped_apps': project_data,
        'all_user_projects': all_user_projects,
        'search_project': search_project,
        'filter_status': filter_status,
        'search_applicant': search_applicant,
    }

    return render(request, 'notifications.html', context)



@csrf_exempt
def save_transaction(request):
    if request.method == "POST":
        data = json.loads(request.body)
        project_id = data.get("project_id")
        amount_eth = Decimal(str(data.get("amount_eth")))
        user_address = data.get("user_address")
        tx_hash = data.get("tx_hash")

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)

        # Save the transaction with user link if authenticated
        transaction_data = {
            'user_address': user_address,
            'tx_hash': tx_hash,
            'amount_eth': amount_eth,
            'project': project
        }

        # Link to user if authenticated
        if request.user.is_authenticated:
            transaction_data['user'] = request.user

        Transaction.objects.create(**transaction_data)

        # Update current funding
        total_funded = Transaction.objects.filter(project=project).aggregate(total=models.Sum('amount_eth'))['total'] or Decimal('0')
        percentage = (total_funded / project.funding_goal) * 100
        percentage = float(min(percentage, 100))

        # Determine whether to trigger confetti/message
        session_key = f"funded_{project_id}"
        trigger_celebration = False

        if total_funded >= project.funding_goal and not request.session.get(session_key):
            request.session[session_key] = True  # Mark as shown
            trigger_celebration = True

        return JsonResponse({
            'project_id': project.id,
            'current_funding': str(total_funded),
            'funding_goal': str(project.funding_goal),
            'percentage': percentage,
            'celebrate': trigger_celebration  # this is key
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)
def get_project_funding(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        total_funded = Transaction.objects.filter(project=project).aggregate(total=Sum('amount_eth'))['total'] or Decimal('0')
        percentage = float(min((total_funded / project.funding_goal) * 100, 100))

        session_key = f"funded_{project_id}"
        trigger_celebration = False

        if total_funded >= project.funding_goal and not request.session.get(session_key):
            request.session[session_key] = True
            trigger_celebration = True

        return JsonResponse({
            'project_id': project.id,
            'current_funding': str(total_funded),
            'funding_goal': str(project.funding_goal),
            'percentage': percentage,
            'celebrate': trigger_celebration
        })

    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
@login_required
def message_history(request, application_id):
    """Get message history for an application"""
    try:
        # Verify the user has permission to view these messages
        application = Application.objects.get(id=application_id)
        
        # Check if user is either the project owner or the applicant
        if request.user != application.position.project.user and request.user != application.applicant:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        # Check if application is approved (only approved applications can access messaging)
        if application.status != 'approved':
            return JsonResponse({'error': 'Messaging is only available for approved applications'}, status=403)
        
        # Mark messages as read if user is recipient
        Message.objects.filter(
            application=application,
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        # Get all messages for this application
        messages = Message.objects.filter(application=application).order_by('timestamp')
        
        # Format messages for JSON response
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                'is_sender': msg.sender == request.user,
                'is_read': msg.is_read
            })
        
        return JsonResponse({'messages': message_list})
    
    except Application.DoesNotExist:
        return JsonResponse({'error': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def send_message(request):
    """Send a message to an applicant or project owner"""
    try:
        application_id = request.POST.get('application_id')
        content = request.POST.get('content')
        
        if not application_id or not content:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        application = Application.objects.get(id=application_id)

        # Check messaging permissions
        if request.user == application.applicant:
            # Applicant can only send messages if application is approved
            # (Initial message is created automatically during application submission)
            if application.status != 'approved':
                return JsonResponse({'success': False, 'error': 'You can only send messages after your application is approved'}, status=403)
        elif request.user == application.position.project.user:
            # Project owner can always send messages
            pass
        else:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        # Determine sender and recipient
        if request.user == application.position.project.user:
            # Project owner sending to applicant
            sender = request.user
            recipient = application.applicant
        elif request.user == application.applicant:
            # Applicant sending to project owner
            sender = request.user
            recipient = application.position.project.user
        else:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        # Create and save the message
        message = Message(
            application=application,
            sender=sender,
            recipient=recipient,
            content=content
        )
        message.save()

        # Create notification for message recipient
        if recipient == application.applicant:
            # Message sent to applicant
            Notification.objects.create(
                user=recipient,
                title="New Message Received 💬",
                message=f"You have a new message from {sender.username} regarding your application for {application.position.title} in '{application.position.project.name}'",
                notification_type="message",
                related_object_id=application.id
            )
        else:
            # Message sent to project owner
            Notification.objects.create(
                user=recipient,
                title="New Message Received 💬",
                message=f"You have a new message from {sender.username} regarding the {application.position.title} position in your project '{application.position.project.name}'",
                notification_type="message",
                related_object_id=application.id
            )

        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                'is_sender': True
            }
        })
    
    except Application.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# New page views
def about(request):
    """About page view"""
    return render(request, 'about.html')

def features(request):
    """Features page view"""
    return render(request, 'features.html')

def contact(request):
    """Contact page view"""
    return render(request, 'contact.html')

@login_required
def profile(request):
    """User profile page view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Handle profile update
        try:
            # Update User model fields
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.save()

            # Update UserProfile fields
            profile.bio = request.POST.get('bio', '')
            profile.location = request.POST.get('location', '')
            profile.website = request.POST.get('website', '')
            profile.phone = request.POST.get('phone', '')
            profile.company = request.POST.get('company', '')
            profile.job_title = request.POST.get('job_title', '')
            profile.linkedin_url = request.POST.get('linkedin_url', '')
            profile.twitter_url = request.POST.get('twitter_url', '')
            profile.github_url = request.POST.get('github_url', '')

            # Handle avatar upload
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']

            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

    # Get user statistics using UserProfile methods
    user_projects = Project.objects.filter(user=request.user)

    context = {
        'user': request.user,
        'profile': profile,
        'projects_count': profile.get_projects_count(),
        'total_funded': profile.get_total_funded(),
        'investments_made': profile.get_investments_made(),
        'investments_count': profile.get_investments_count(),
        'funded_projects_count': profile.get_funded_projects_count(),
        'success_rate': profile.get_success_rate(),
        'recent_projects': user_projects.order_by('-created_at')[:3]
    }

    return render(request, 'profile.html', context)

@login_required
def settings(request):
    """User settings page view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_account':
            # Update account settings
            profile.timezone = request.POST.get('timezone', 'UTC')
            profile.language = request.POST.get('language', 'en')
            profile.save()
            messages.success(request, 'Account settings updated successfully!')

        elif action == 'update_notifications':
            # Update notification preferences
            profile.email_notifications = request.POST.get('email_notifications') == 'on'
            profile.push_notifications = request.POST.get('push_notifications') == 'on'
            profile.project_updates = request.POST.get('project_updates') == 'on'
            profile.investment_alerts = request.POST.get('investment_alerts') == 'on'
            profile.marketing_communications = request.POST.get('marketing_communications') == 'on'
            profile.save()
            messages.success(request, 'Notification preferences updated successfully!')

        elif action == 'update_privacy':
            # Update privacy settings
            profile.profile_visibility = request.POST.get('profile_visibility', 'public')
            profile.show_activity_status = request.POST.get('show_activity_status') == 'on'
            profile.show_investment_history = request.POST.get('show_investment_history') == 'on'
            profile.save()
            messages.success(request, 'Privacy settings updated successfully!')

        elif action == 'change_password':
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password changed successfully! Please log in again.')
                return redirect('login')

        return redirect('settings')

    context = {
        'user': request.user,
        'profile': profile
    }

    return render(request, 'settings.html', context)

@csrf_exempt
def chat_api(request):
    """Chatbot API endpoint using Groq"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'success': False, 'error': 'Message is required'})

        # Load Groq API key from environment
        load_dotenv()
        groq_api_key = os.getenv('GROQ_API_KEY')

        if not groq_api_key:
            return JsonResponse({'success': False, 'error': 'API key not configured'})

        # Prepare the prompt for entrepreneur assistance
        system_prompt = """You are Nexora AI Assistant, a specialized AI helper for entrepreneurs and startup founders. You provide expert advice on:

- Business strategy and planning
- Funding and investment strategies
- Market research and analysis
- Startup best practices
- Technical guidance for tech startups
- Networking and mentorship advice
- Product development and MVP creation
- Marketing and customer acquisition
- Financial planning and budgeting
- Legal considerations for startups

Keep your responses concise, actionable, and tailored to early-stage entrepreneurs. Use a friendly but professional tone. If asked about topics outside entrepreneurship, politely redirect to business-related topics."""

        # Call Groq API
        headers = {
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'model': 'llama3-8b-8192',  # Using Llama 3 8B model
            'temperature': 0.7,
            'max_tokens': 500,
            'top_p': 0.9
        }

        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']

            return JsonResponse({
                'success': True,
                'response': ai_response
            })
        else:
            logging.error(f"Groq API error: {response.status_code} - {response.text}")
            return JsonResponse({
                'success': False,
                'error': 'AI service temporarily unavailable'
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except requests.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Network error'})
    except Exception as e:
        logging.error(f"Chat API error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

@login_required
def applicant_messages_view(request):
    """View for applicants to see their applications and messages"""
    applications = Application.objects.filter(applicant=request.user).select_related('position__project__user').order_by('-created_at')

    # Get recent notifications for the applicant
    notifications = Notification.objects.filter(user=request.user)[:5]
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'applicant_messages.html', {
        'applications': applications,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count
    })

@csrf_exempt
@login_required
def update_application_status(request):
    """Update application status (approve/reject)"""
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        new_status = request.POST.get('status')

        if new_status not in ['approved', 'rejected']:
            return JsonResponse({'success': False, 'error': 'Invalid status'})

        try:
            application = Application.objects.get(id=app_id)

            # Check if user is the project owner
            if application.position.project.user != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied'})

            if application.status == 'approved' or application.status == 'rejected':
                return JsonResponse({'success': False, 'error': 'Status already set'})

            application.status = new_status
            application.save()

            # Create notification for applicant
            if new_status == 'approved':
                Notification.objects.create(
                    user=application.applicant,
                    title="Application Approved! 🎉",
                    message=f"Great news! Your application for {application.position.title} position in '{application.position.project.name}' has been approved. You can now start messaging with the project owner.",
                    notification_type="approval",
                    related_object_id=application.id
                )
            elif new_status == 'rejected':
                Notification.objects.create(
                    user=application.applicant,
                    title="Application Update",
                    message=f"Thank you for your interest in {application.position.title} position in '{application.position.project.name}'. Unfortunately, we've decided to move forward with other candidates.",
                    notification_type="rejection",
                    related_object_id=application.id
                )

            return JsonResponse({'success': True})
        except Application.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Application not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def chatbot_view(request):
    """Render the chatbot interface with chat history"""
    if request.user.is_authenticated:
        chats = Chat.objects.filter(user=request.user).order_by('created_at')
        return render(request, 'chatbot.html', {'chats': chats})
    # For unauthenticated users, pass an empty list
    return render(request, 'chatbot.html', {'chats': []})

@login_required
def ai_mentorship(request):
    return render(request, 'Chatbot-main.html')

@login_required
@require_POST
def mark_notifications_read(request):
    """Mark all notifications as read for the current user"""
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def analytics_dashboard(request):
    """Analytics dashboard with real data from models"""

    # Basic metrics
    total_users = User.objects.count()
    total_projects = Project.objects.count()
    total_applications = Application.objects.count()
    total_funding = Transaction.objects.aggregate(Sum('amount_eth'))['amount_eth__sum'] or 0

    # User role analysis (based on whether they've created projects or applied to positions)
    entrepreneurs = User.objects.filter(project__isnull=False).distinct().count()
    investors = User.objects.filter(
        userprofile__investment_alerts=True
    ).distinct().count()
    # Calculate others (users who are neither entrepreneurs nor investors)
    others = total_users - entrepreneurs - investors + User.objects.filter(
        project__isnull=False, userprofile__investment_alerts=True
    ).distinct().count()  # Add back users who are both

    # Monthly user growth (past 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_signups_raw = User.objects.filter(
        date_joined__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(count=Count('id')).order_by('month')

    # Format monthly data for frontend
    monthly_signups = [
        {'month': item['month'].strftime('%Y-%m'), 'count': item['count']}
        for item in monthly_signups_raw
    ]

    # Daily signups (past 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_signups_raw = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).annotate(
        day=TruncDay('date_joined')
    ).values('day').annotate(count=Count('id')).order_by('day')

    # Format daily data for frontend
    daily_signups = [
        {'day': item['day'].strftime('%Y-%m-%d'), 'count': item['count']}
        for item in daily_signups_raw
    ]

    # Projects by category
    projects_by_category = Project.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')

    # Projects by stage
    projects_by_stage = Project.objects.values('stage').annotate(
        count=Count('id')
    ).order_by('-count')

    # Recent activity
    recent_projects = Project.objects.select_related('user').order_by('-created_at')[:5]
    recent_applications = Application.objects.select_related('applicant', 'position__project').order_by('-created_at')[:5]

    # Funding metrics
    funded_projects = Project.objects.filter(transactions__isnull=False).distinct().count()
    avg_funding_per_project = Transaction.objects.aggregate(
        avg_funding=Sum('amount_eth')
    )['avg_funding'] or 0
    if funded_projects > 0:
        avg_funding_per_project = avg_funding_per_project / funded_projects

    context = {
        'total_users': total_users,
        'total_projects': total_projects,
        'total_applications': total_applications,
        'total_funding': round(float(total_funding), 4),
        'entrepreneurs': entrepreneurs,
        'investors': investors,
        'others': others,
        'monthly_signups': list(monthly_signups),
        'daily_signups': list(daily_signups),
        'projects_by_category': list(projects_by_category),
        'projects_by_stage': list(projects_by_stage),
        'recent_projects': recent_projects,
        'recent_applications': recent_applications,
        'funded_projects': funded_projects,
        'avg_funding_per_project': round(float(avg_funding_per_project), 4),
    }

    return render(request, 'analytics_dashboard.html', context)

@login_required
def network_explorer(request):
    """Network explorer to browse users with filtering and search"""

    # Get all users with their profiles
    users = User.objects.select_related('userprofile').filter(
        userprofile__profile_visibility__in=['public', 'registered']
    ).exclude(id=request.user.id)  # Exclude current user

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(userprofile__company__icontains=search_query) |
            Q(userprofile__job_title__icontains=search_query) |
            Q(userprofile__location__icontains=search_query)
        )

    # Role filter
    role_filter = request.GET.get('role', '')
    if role_filter == 'entrepreneur':
        users = users.filter(project__isnull=False).distinct()
    elif role_filter == 'investor':
        users = users.filter(userprofile__investment_alerts=True).exclude(project__isnull=False).distinct()

    # Location filter
    location_filter = request.GET.get('location', '')
    if location_filter:
        users = users.filter(userprofile__location__icontains=location_filter)

    # Industry filter (based on project categories)
    industry_filter = request.GET.get('industry', '')
    if industry_filter:
        users = users.filter(project__category__icontains=industry_filter).distinct()

    # Add role information to each user
    users_with_roles = []
    for user in users:
        user_data = {
            'user': user,
            'profile': user.userprofile,
            'is_entrepreneur': user.project_set.exists(),
            'is_investor': user.userprofile.investment_alerts,
            'projects_count': user.project_set.count(),
            'applications_count': user.application_set.count(),
        }

        # Determine primary role
        if user_data['is_entrepreneur'] and user_data['is_investor']:
            user_data['primary_role'] = 'Entrepreneur & Investor'
        elif user_data['is_entrepreneur']:
            user_data['primary_role'] = 'Entrepreneur'
        elif user_data['is_investor']:
            user_data['primary_role'] = 'Investor'
        else:
            user_data['primary_role'] = 'Member'

        # Get user's project categories for tags
        user_categories = list(user.project_set.values_list('category', flat=True).distinct())
        user_data['tags'] = user_categories[:3]  # Limit to 3 tags

        users_with_roles.append(user_data)

    # Get filter options
    all_locations = UserProfile.objects.exclude(location='').values_list('location', flat=True).distinct()
    all_industries = Project.objects.values_list('category', flat=True).distinct()

    context = {
        'users': users_with_roles,
        'search_query': search_query,
        'role_filter': role_filter,
        'location_filter': location_filter,
        'industry_filter': industry_filter,
        'all_locations': sorted(set(all_locations)),
        'all_industries': sorted(set(all_industries)),
        'total_users': len(users_with_roles),
    }

    return render(request, 'network_explorer.html', context)

@csrf_exempt
@login_required
def ai_mentorship_api(request):
    """API endpoint for AI mentorship chat"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'success': False, 'error': 'Message is required'})

        # Enhanced entrepreneurship-focused system prompt
        system_prompt = """You are an expert AI entrepreneurship mentor with deep knowledge in:
        - Business strategy and planning
        - Startup funding and investment
        - Market validation and customer development
        - Product development and MVP creation
        - Team building and leadership
        - Growth hacking and marketing
        - Financial planning and management
        - Legal and regulatory considerations
        - Scaling and operations
        - Exit strategies

        Provide practical, actionable advice tailored to startup founders and entrepreneurs.
        Be encouraging but realistic. Ask clarifying questions when needed to provide better guidance.
        Keep responses concise but comprehensive, focusing on actionable insights."""

        # Get AI response using Groq
        ai_response = ask_groqcloud_mentorship(user_message, system_prompt)

        return JsonResponse({
            'success': True,
            'response': ai_response
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"AI Mentorship API error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

def ask_groqcloud_mentorship(message, system_prompt):
    """Enhanced Groq API call for mentorship with system prompt"""
    if not groq_client:
        return "AI mentorship service is currently unavailable. Please try again later."

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API error in mentorship: {str(e)}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."


@login_required
def export_user_data(request):
    """Export user data as PDF"""
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#7c3aed'),
        alignment=1  # Center alignment
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#7c3aed')
    )

    # Get user data
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Title
    title = Paragraph("Nexora - User Data Export", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))

    # User Information
    user_info_heading = Paragraph("Personal Information", heading_style)
    elements.append(user_info_heading)

    user_data = [
        ['Field', 'Value'],
        ['Username', user.username],
        ['Full Name', f"{user.first_name} {user.last_name}".strip() or 'Not provided'],
        ['Email', user.email],
        ['Date Joined', user.date_joined.strftime('%B %d, %Y')],
        ['Bio', profile.bio or 'Not provided'],
        ['Location', profile.location or 'Not provided'],
        ['Company', profile.company or 'Not provided'],
        ['Job Title', profile.job_title or 'Not provided'],
        ['Website', profile.website or 'Not provided'],
        ['Phone', profile.phone or 'Not provided'],
    ]

    user_table = Table(user_data, colWidths=[2*inch, 4*inch])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(user_table)
    elements.append(Spacer(1, 20))

    # Statistics
    stats_heading = Paragraph("Account Statistics", heading_style)
    elements.append(stats_heading)

    stats_data = [
        ['Metric', 'Value'],
        ['Projects Created', str(profile.get_projects_count())],
        ['Total Funded (ETH)', f"{profile.get_total_funded():.4f}"],
        ['Investments Made (ETH)', f"{profile.get_investments_made():.4f}"],
        ['Number of Investments', str(profile.get_investments_count())],
        ['Projects Funded', str(profile.get_funded_projects_count())],
        ['Success Rate', f"{profile.get_success_rate()}%"],
    ]

    stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(stats_table)
    elements.append(Spacer(1, 20))

    # Projects
    projects = Project.objects.filter(user=user).order_by('-created_at')
    if projects.exists():
        projects_heading = Paragraph("Your Projects", heading_style)
        elements.append(projects_heading)

        project_data = [['Project Name', 'Category', 'Stage', 'Funding Goal (ETH)', 'Current Funding (ETH)', 'Created Date']]

        for project in projects:
            project_data.append([
                project.name,
                project.category,
                project.stage,
                f"{project.funding_goal:.2f}",
                f"{project.current_funding():.4f}",
                project.created_at.strftime('%Y-%m-%d')
            ])

        projects_table = Table(project_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        projects_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(projects_table)
        elements.append(Spacer(1, 20))

    # Investment History
    investments = Transaction.objects.filter(user=user).order_by('-timestamp')
    if investments.exists():
        investments_heading = Paragraph("Investment History", heading_style)
        elements.append(investments_heading)

        investment_data = [['Project', 'Amount (ETH)', 'Transaction Hash', 'Date']]

        for investment in investments:
            investment_data.append([
                investment.project.name if investment.project else 'Unknown',
                f"{investment.amount_eth:.4f}",
                f"{investment.tx_hash[:10]}...{investment.tx_hash[-6:]}",
                investment.timestamp.strftime('%Y-%m-%d %H:%M')
            ])

        investments_table = Table(investment_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        investments_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(investments_table)

    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Nexora Platform"
    footer = Paragraph(footer_text, styles['Normal'])
    elements.append(footer)

    # Build PDF
    doc.build(elements)

    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="nexora_user_data_{user.username}.pdf"'
    response.write(pdf)

    return response
