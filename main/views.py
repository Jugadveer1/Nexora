from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Project, Position, Application, Transaction, Chat, Message
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.db import models
import os
from dotenv import load_dotenv
import logging
from django.utils import timezone
from django.views.decorators.http import require_POST
from decimal import Decimal
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
        project=Project.objects.create(
            user=request.user,
            name=name,
            description=description,
            market=market,
            problem = problem,
            competition=competition,
            details=details,
            stage=stage,
            category=category,
            url=url,
            banner=banner
        )



        funding_goal = request.POST.get('funding_goal', 0)
        project=Project.objects.create(
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
        
        for pos in positions_data:
            Position.objects.create(
                project=project,
                title=pos['title'],
                description=pos['description'],
                compensation_type=pos['compensation_type']
            )
        return redirect('home')  # Make sure your URL name is 'home'
    # SEARCH
    query = request.GET.get('q', '')
    projects = Project.objects.all()
    if query:
        projects = projects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(problem__icontains=query)
        )

    if category:
        projects = projects.filter(category__iexact=category)

    if stage:
        projects = projects.filter(stage__iexact=stage)

    if mine:
        projects = projects.filter(user=request.user)

    projects = projects.order_by('-created_at')
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

        Application.objects.create(
            position=position,
            applicant=request.user,
            reason=reason,
            experience=experience
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

    # Order projects by most recent first
    user_projects = Project.objects.filter(user=request.user)\
        .prefetch_related('positions')\
        .order_by('-created_at')

    applications = Application.objects.filter(
        position__project__in=user_projects
    ).select_related('position', 'position__project', 'applicant')\
     .order_by('-created_at')

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

    return render(request, 'notifications.html', {'grouped_apps': project_data})



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

        # Save the transaction
        Transaction.objects.create(
            user_address=user_address,
            tx_hash=tx_hash,
            amount_eth=amount_eth,
            project=project
        )

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
