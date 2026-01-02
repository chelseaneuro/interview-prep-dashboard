from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# Initialize Anthropic client
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not found in environment")
    exit(1)

client = Anthropic(api_key=api_key)
MODEL = os.getenv('CLAUDE_MODEL', 'claude-3-haiku-20240307')

def build_prompt(question, profile, job_context=None):
    """Build the Claude prompt for interview response generation"""

    # Personal info
    personal = profile.get('personal_info', {})
    name = personal.get('name', 'the candidate')

    # Work experience
    work_exp = profile.get('work_experience', [])
    work_text = ""
    for exp in work_exp:
        work_text += f"\n• {exp.get('role')} at {exp.get('company')}\n"
        work_text += f"  {exp.get('start_date')} - {exp.get('end_date') or 'Present'}\n"
        if exp.get('responsibilities'):
            for resp in exp.get('responsibilities', [])[:3]:
                work_text += f"  - {resp}\n"
        if exp.get('technologies'):
            work_text += f"  Technologies: {', '.join(exp.get('technologies', []))}\n"

    # Skills
    skills = profile.get('skills', {})
    tech_skills = skills.get('technical', {})
    all_skills = []
    for category, items in tech_skills.items():
        if isinstance(items, list):
            all_skills.extend(items)
    skills_text = ', '.join(all_skills[:15]) if all_skills else "Not specified"

    # Projects
    projects = profile.get('projects', [])
    projects_text = ""
    for proj in projects:
        projects_text += f"\n• {proj.get('name')}: {proj.get('description')}\n"
        if proj.get('technologies'):
            projects_text += f"  Technologies: {', '.join(proj.get('technologies', []))}\n"

    # Job context
    job_text = ""
    if job_context:
        job_text = f"\nTARGET POSITION: {job_context.get('position')} at {job_context.get('company')}\n"
        job_text += "Tailor the response to demonstrate relevant skills for this specific role.\n"

    prompt = f"""You are an expert interview coach helping {name} craft an authentic, compelling interview response.

CANDIDATE PROFILE:
Name: {personal.get('name', 'Not specified')}
Location: {personal.get('location', 'Not specified')}
Email: {personal.get('email', 'Not specified')}

WORK EXPERIENCE:{work_text}

SKILLS:
{skills_text}

PROJECTS:{projects_text}
{job_text}
INSTRUCTIONS:
1. Use ONLY {name}'s actual experiences provided above
2. Be specific - reference real projects, technologies, and achievements
3. Follow the STAR method (Situation, Task, Action, Result) where appropriate
4. Keep the response conversational and natural, not robotic
5. Highlight quantifiable achievements when available
6. Make it authentic - this should sound like {name} speaking
7. Keep response to 250-400 words (approximately 2-3 minutes when spoken)

INTERVIEW QUESTION: {question}

Generate a compelling, authentic response using {name}'s actual experiences. Write in first person."""

    return prompt

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'model': MODEL
    })

@app.route('/api/interview/generate', methods=['POST'])
def generate_interview_response():
    """Generate interview response using Claude API"""
    try:
        data = request.json
        question = data.get('question')
        profile = data.get('profile')
        job_id = data.get('job_id')

        if not question or not profile:
            return jsonify({
                'success': False,
                'error': 'Missing question or profile data'
            }), 400

        # Find job context if provided
        job_context = None
        if job_id and profile.get('job_applications'):
            for job in profile['job_applications']:
                if job.get('id') == job_id:
                    job_context = job
                    break

        # Build prompt
        prompt = build_prompt(question, profile, job_context)

        # Call Claude API
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = message.content[0].text

        # Identify referenced experiences (simple heuristic)
        referenced = []
        work_exp = profile.get('work_experience', [])
        for exp in work_exp:
            company = exp.get('company', '')
            role = exp.get('role', '')
            if company.lower() in response_text.lower() or role.lower() in response_text.lower():
                referenced.append(f"{role} at {company}")

        return jsonify({
            'success': True,
            'response': response_text,
            'job_context': job_context if job_context else None,
            'relevant_experiences': referenced
        })

    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print(f"Starting Interview Prep API server...")
    print(f"Using model: {MODEL}")
    print(f"Server running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
