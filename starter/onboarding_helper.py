"""
AI Onboarding Automation - Python Helper Script
================================================
This script demonstrates the core AI-powered onboarding logic.
It can be run standalone or integrated into an automation platform.

Requirements:
    pip install openai airtable-python-wrapper python-dotenv

Setup:
    Create a .env file with:
        OPENAI_API_KEY=your_key_here
        AIRTABLE_API_KEY=your_key_here
        AIRTABLE_BASE_ID=your_base_id_here
"""

import json
import os
from datetime import datetime
from openai import OpenAI

# ─────────────────────────────────────────────
# MOCK DATA — Replace with real intake in production
# ─────────────────────────────────────────────

MOCK_NEW_HIRE = {
    "full_name": "Sara Ahmed",
    "personal_email": "sara.ahmed@gmail.com",
    "job_title": "Software Engineer",
    "department": "Engineering",
    "office_location": "Karachi, Pakistan",
    "manager_name": "Ali Raza",
    "manager_email": "ali.raza@company.com",
    "employment_type": "full-time",
    "start_date": "2026-04-01",
    "uploaded_documents": ["offer_letter_signed.pdf", "national_id.jpg"]
}

# ─────────────────────────────────────────────
# DEPARTMENT ONBOARDING TRACKS
# ─────────────────────────────────────────────

DEPARTMENT_TRACKS = {
    "Engineering": {
        "tools": ["GitHub", "Jira", "Slack", "VS Code", "AWS Console"],
        "training": ["Security & Compliance", "Code Review Standards", "Architecture Overview"],
        "required_access": ["GitHub org", "AWS sandbox", "Jira project", "Slack workspace"]
    },
    "Sales": {
        "tools": ["Salesforce CRM", "Outreach", "LinkedIn Sales Navigator", "Slack"],
        "training": ["Product Demo Certification", "Sales Methodology", "CRM Training"],
        "required_access": ["Salesforce", "Outreach", "Slack workspace", "Zoom"]
    },
    "HR": {
        "tools": ["BambooHR", "Slack", "Google Workspace", "DocuSign"],
        "training": ["HRIS Training", "Compliance & Privacy", "Benefits Administration"],
        "required_access": ["BambooHR admin", "Google Workspace", "DocuSign", "Slack workspace"]
    },
    "default": {
        "tools": ["Slack", "Google Workspace", "Notion", "Zoom"],
        "training": ["Company Overview", "Security & Compliance", "Tool Access Training"],
        "required_access": ["Google Workspace", "Slack workspace", "Notion", "Zoom"]
    }
}


# ─────────────────────────────────────────────
# STEP 1: VALIDATE INTAKE RECORD
# ─────────────────────────────────────────────

def validate_intake(data: dict) -> dict:
    """
    Validates required fields in the intake record.
    Returns validation result with score and missing fields.
    """
    required_fields = [
        "full_name", "personal_email", "job_title",
        "department", "start_date", "manager_name"
    ]

    missing = [f for f in required_fields if not data.get(f)]
    score = round(((len(required_fields) - len(missing)) / len(required_fields)) * 100, 1)

    return {
        "validation_passed": score >= 85,
        "validation_score": score,
        "missing_fields": missing,
        "record_id": f"ONB-{int(datetime.now().timestamp())}",
        "intake_timestamp": datetime.now().isoformat()
    }


# ─────────────────────────────────────────────
# STEP 2: AI EXTRACTION & NORMALIZATION
# ─────────────────────────────────────────────

def ai_extract_fields(client: OpenAI, intake_data: dict) -> dict:
    """
    Uses GPT-4o to extract, normalize, and validate onboarding fields.
    Returns structured JSON onboarding record.
    """
    prompt = f"""
You are an onboarding operations assistant for an enterprise HR team.

Extract the following fields from this employee intake record.
Return ONLY valid JSON. No commentary. No markdown.

Intake data:
{json.dumps(intake_data, indent=2)}

Required fields:
- full_name (string)
- personal_email (string)
- company_email (string or null)
- job_title (string)
- department (string)
- office_location (string or null)
- manager_name (string)
- manager_email (string or null)
- employment_type (full-time | part-time | contractor)
- start_date (ISO 8601 format)
- required_systems (array of strings)
- missing_documents (array of strings, empty if none)
- review_flags (array of issue descriptions, empty if none)

Rules:
- Set null for any field you cannot determine
- Never guess or infer values
- Flag any data conflicts in review_flags
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an HR data extraction assistant. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


# ─────────────────────────────────────────────
# STEP 3: ENRICH PROFILE
# ─────────────────────────────────────────────

def enrich_profile(extracted: dict, validation: dict) -> dict:
    """
    Merges extracted AI data with department-specific onboarding track.
    Builds the complete onboarding profile.
    """
    dept = extracted.get("department", "default")
    track = DEPARTMENT_TRACKS.get(dept, DEPARTMENT_TRACKS["default"])

    return {
        **extracted,
        "record_id": validation["record_id"],
        "onboarding_track": track,
        "status": "profile_ready",
        "profile_created_at": datetime.now().isoformat()
    }


# ─────────────────────────────────────────────
# STEP 4: GENERATE PERSONALIZED ONBOARDING PLAN
# ─────────────────────────────────────────────

def generate_onboarding_plan(client: OpenAI, profile: dict) -> dict:
    """
    Uses GPT-4o to generate a personalized onboarding plan
    based on the employee's role, department, and profile.
    """
    prompt = f"""
You are an onboarding experience designer at a large enterprise.

Create a personalized onboarding plan for this new employee.
Return ONLY valid JSON with this exact structure.

Employee:
- Name: {profile.get('full_name')}
- Role: {profile.get('job_title')}
- Department: {profile.get('department')}
- Location: {profile.get('office_location')}
- Manager: {profile.get('manager_name')}
- Start Date: {profile.get('start_date')}
- Employment Type: {profile.get('employment_type')}
- Tools to Set Up: {profile.get('onboarding_track', {}).get('tools', [])}
- Required Training: {profile.get('onboarding_track', {}).get('training', [])}

Return:
{{
  "welcome_message": "2-3 sentence personalized welcome specific to their role",
  "day_one_agenda": ["item 1", "item 2"],
  "week_one_priorities": ["priority 1", ... (5-7 items)],
  "required_training": [{{"module": "", "duration": "", "deadline": ""}}],
  "key_contacts": [{{"name": "", "role": "", "reason": ""}}],
  "recommended_tools": ["tool 1", "tool 2"],
  "resources": ["doc or link 1", "doc or link 2"]
}}

Make everything specific to this role. Avoid generic advice.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an onboarding experience designer. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


# ─────────────────────────────────────────────
# STEP 5: GENERATE MANAGER BRIEFING
# ─────────────────────────────────────────────

def generate_manager_briefing(client: OpenAI, profile: dict) -> str:
    """
    Uses GPT-4o to generate a concise manager briefing note.
    Returns plain text with section headers.
    """
    prompt = f"""
Write a manager briefing note about this incoming team member.
Plain text only. Section headers. Under 250 words. Be direct and practical.

New hire: {profile.get('full_name')}
Role: {profile.get('job_title')}
Department: {profile.get('department')}
Start Date: {profile.get('start_date')}
Location: {profile.get('office_location')}
Employment Type: {profile.get('employment_type')}
Record ID: {profile.get('record_id')}

Include:
1. New Hire Overview
2. Pre-Start Checklist (what the manager must do before day 1)
3. Suggested First 1:1 Topics
4. Flags and Action Items
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an HR assistant. Write concise manager briefing notes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


# ─────────────────────────────────────────────
# MAIN: RUN FULL ONBOARDING WORKFLOW
# ─────────────────────────────────────────────

def run_onboarding_workflow(intake_data: dict):
    """
    Runs the complete AI onboarding automation workflow.
    Uses mock data if no real intake is provided.
    """
    print("\n" + "="*60)
    print("  AI ONBOARDING AUTOMATION — WORKFLOW START")
    print("="*60)

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
    client = OpenAI(api_key=api_key)

    # ── Step 1: Validate ──────────────────────────────────────
    print("\n[Step 1] Validating intake record...")
    validation = validate_intake(intake_data)
    print(f"  ✓ Validation score: {validation['validation_score']}%")
    print(f"  ✓ Record ID: {validation['record_id']}")

    if not validation["validation_passed"]:
        print(f"  ✗ FAILED — Missing fields: {validation['missing_fields']}")
        print("  → Routing to HR review queue")
        return {"status": "flagged", "reason": validation}

    # ── Step 2: AI Extraction ─────────────────────────────────
    print("\n[Step 2] Running AI extraction and normalization...")

    # For demo without real API key, use mock extracted data
    if api_key == "YOUR_OPENAI_API_KEY_HERE":
        print("  ⚠ No API key set — using mock AI output for demo")
        extracted = {
            **intake_data,
            "company_email": "sara.ahmed@company.com",
            "required_systems": ["GitHub", "Jira", "Slack", "AWS Console"],
            "missing_documents": [],
            "review_flags": []
        }
    else:
        extracted = ai_extract_fields(client, intake_data)

    print(f"  ✓ Fields extracted: {len([k for k, v in extracted.items() if v is not None])}")
    print(f"  ✓ Review flags: {len(extracted.get('review_flags', []))}")

    # ── Step 3: Enrich Profile ────────────────────────────────
    print("\n[Step 3] Enriching profile with role data...")
    profile = enrich_profile(extracted, validation)
    print(f"  ✓ Onboarding track assigned: {profile['onboarding_track']['tools']}")

    # ── Step 4: Generate Onboarding Plan ─────────────────────
    print("\n[Step 4] Generating personalized onboarding plan...")
    if api_key == "YOUR_OPENAI_API_KEY_HERE":
        onboarding_plan = {
            "welcome_message": f"Welcome to the team, {profile['full_name']}! We're thrilled to have a {profile['job_title']} joining our {profile['department']} team.",
            "day_one_agenda": ["Team introduction call", "IT setup and tool access", "Company orientation session", "Meet your manager"],
            "week_one_priorities": ["Complete all system access setup", "Review codebase and architecture docs", "Attend team standup", "Complete security training", "Schedule 1:1 with manager"],
            "required_training": [{"module": "Security & Compliance", "duration": "2 hours", "deadline": "Day 3"}],
            "key_contacts": [{"name": profile['manager_name'], "role": "Direct Manager", "reason": "Your primary point of contact for all onboarding questions"}],
            "recommended_tools": profile['onboarding_track']['tools'],
            "resources": ["Company handbook", "Engineering wiki", "Team Slack channels guide"]
        }
    else:
        onboarding_plan = generate_onboarding_plan(client, profile)
    print(f"  ✓ Plan generated with {len(onboarding_plan.get('week_one_priorities', []))} week 1 priorities")

    # ── Step 5: Manager Briefing ──────────────────────────────
    print("\n[Step 5] Generating manager briefing note...")
    if api_key == "YOUR_OPENAI_API_KEY_HERE":
        manager_briefing = f"""
NEW HIRE OVERVIEW
{profile['full_name']} is joining as {profile['job_title']} in {profile['department']} on {profile['start_date']}.

PRE-START CHECKLIST
- Schedule Day 1 welcome meeting
- Assign a team buddy
- Prepare first week agenda
- Confirm system access with IT

SUGGESTED FIRST 1:1 TOPICS
- Role expectations and 30/60/90 day goals
- Team structure and key stakeholders
- Communication preferences
- Any questions about the role

FLAGS AND ACTION ITEMS
- None at this time. Record ID: {profile['record_id']}
"""
    else:
        manager_briefing = generate_manager_briefing(client, profile)
    print("  ✓ Manager briefing generated")

    # ── Final Output ──────────────────────────────────────────
    result = {
        "status": "completed",
        "record_id": profile["record_id"],
        "profile": profile,
        "onboarding_plan": onboarding_plan,
        "manager_briefing": manager_briefing,
        "next_steps": [
            f"Store profile in Airtable (Record: {profile['record_id']})",
            f"Send welcome email to {profile['personal_email']}",
            f"Send briefing to manager: {profile['manager_name']}",
            "Send IT provisioning alert to #it-onboarding Slack channel",
            f"Schedule Day 7 check-in for {profile['full_name']}"
        ]
    }

    print("\n" + "="*60)
    print("  WORKFLOW COMPLETE")
    print("="*60)
    print(f"\n  Record ID:    {result['record_id']}")
    print(f"   New Hire:     {profile['full_name']}")
    print(f"   Role:         {profile['job_title']} — {profile['department']}")
    print(f"   Start Date:   {profile['start_date']}")
    print(f"   Status:       {result['status'].upper()}")
    print("\n  Next Steps:")
    for step in result["next_steps"]:
        print(f"    → {step}")

    # Save output to file
    output_path = "onboarding_output.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  📄 Full output saved to: {output_path}")

    return result


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting AI Onboarding Automation demo with mock data...")
    run_onboarding_workflow(MOCK_NEW_HIRE)
