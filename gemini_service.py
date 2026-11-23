"""
SheRise Gemini API Integration Service
Provides AI-powered Pitch Doctor, Investor Readiness Evaluation, and Personalized Investor Outreach Letters.
Uses Google Gemini API with smart fallback when API key is not configured.
"""

import os
import json
import urllib.request
import urllib.error
import re

# Default model configuration
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
DEFAULT_MODEL = "gemini-2.5-flash"
BACKUP_MODEL = "gemini-1.5-flash"

def get_api_key(custom_key: str = None) -> str:
    """Retrieve Gemini API key from explicit parameter or environment."""
    if custom_key and len(custom_key.strip()) > 10:
        return custom_key.strip()
    return os.environ.get("GEMINI_API_KEY", "").strip()

def call_gemini_api(prompt: str, api_key: str, system_instruction: str = None, model: str = DEFAULT_MODEL) -> str:
    """Invoke the Gemini REST API with prompt and returns generated text."""
    url = GEMINI_API_ENDPOINT.format(model=model, key=api_key)

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1500
        }
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"]
            return ""
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        # Try backup model if 404 or model not found
        if model != BACKUP_MODEL and (e.code == 404 or "not found" in error_body.lower()):
            return call_gemini_api(prompt, api_key, system_instruction, model=BACKUP_MODEL)
        raise RuntimeError(f"Gemini API Error {e.code}: {error_body}")
    except Exception as e:
        raise RuntimeError(f"Gemini API Request Failed: {str(e)}")

def evaluate_pitch_doctor(venture_data: dict, api_key: str = None) -> dict:
    """
    Evaluates a female-led startup pitch across investor viability, problem-solution fit,
    unit economics, and returns an Investor Readiness Score + Actionable Feedback.
    """
    title = venture_data.get("title", "Untitled Startup")
    category = venture_data.get("category", "General Tech")
    stage = venture_data.get("stage", "Seed")
    target_funding = venture_data.get("target_funding", 100000)
    problem = venture_data.get("problem", "")
    solution = venture_data.get("solution", "")
    market = venture_data.get("target_market", "")
    traction = venture_data.get("traction", "Initial development stage")

    key = get_api_key(api_key)

    if key:
        system_instruction = (
            "You are SheRise AI Pitch Doctor, an elite venture capitalist and startup advisor "
            "dedicated to helping female founders raise capital and build enduring, high-growth businesses. "
            "Provide rigorous, constructive, and empowering feedback in strict JSON format."
        )

        prompt = f"""
Evaluate the following female-founded startup pitch for investor readiness:

Startup Name: {title}
Category: {category}
Stage: {stage}
Target Funding Goal: ${target_funding:,}
Problem Statement: {problem}
Proposed Solution: {solution}
Target Market: {market}
Current Traction / Validation: {traction}

Respond ONLY with a valid JSON object matching this exact schema:
{{
  "score": <integer between 70 and 98>,
  "readiness_level": "<High Investor Readiness | Strong Investment Potential | Promising Seed Stage>",
  "executive_pitch": "<a polished, razor-sharp 2-3 sentence elevator pitch suitable for angel syndicates>",
  "strengths": [
    "<strongest value proposition 1>",
    "<strongest value proposition 2>",
    "<strongest value proposition 3>"
  ],
  "growth_areas": [
    "<actionable suggestion to improve investor defensibility 1>",
    "<actionable suggestion to improve investor defensibility 2>"
  ],
  "investor_questions": [
    "<tough question an angel or VC will ask during diligence 1>",
    "<tough question an angel or VC will ask during diligence 2>"
  ]
}}
"""
        try:
            raw_response = call_gemini_api(prompt, key, system_instruction)
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)
            parsed = json.loads(cleaned)
            parsed["ai_engine"] = "Google Gemini Live API"
            return parsed
        except Exception as e:
            # Fall back smoothly if network or quota issue occurs
            fallback = generate_intelligent_heuristic_review(venture_data)
            fallback["notice"] = f"Using SheRise Heuristic Engine (Gemini Notice: {str(e)[:90]}...)"
            return fallback

    # Offline / Heuristic fallback when no key is entered
    return generate_intelligent_heuristic_review(venture_data)

def generate_intelligent_heuristic_review(data: dict) -> dict:
    """Heuristic AI analysis providing rich, realistic startup evaluation."""
    title = data.get("title", "Your Venture")
    category = data.get("category", "Tech")
    stage = data.get("stage", "Seed")
    problem = data.get("problem", "")
    solution = data.get("solution", "")
    traction = data.get("traction", "")
    funding = data.get("target_funding", 100000)

    # Calculate dynamic readiness score based on length & depth of inputs
    base_score = 84
    if len(problem) > 80: base_score += 3
    if len(solution) > 80: base_score += 3
    if len(traction) > 40: base_score += 4
    if funding > 500000: base_score += 1
    score = min(96, max(75, base_score))

    readiness = "High Investor Readiness" if score >= 90 else "Strong Investment Potential"

    exec_pitch = (
        f"{title} is solving a critical problem in {category} by {solution[:120].rstrip('.')}... "
        f"With clear early validation, the team is raising ${int(funding):,} at {stage} stage to accelerate commercialization."
    )

    strengths = [
        f"Crisp problem articulation addressing an underserved need in {category}.",
        "Clear value proposition with scalable technology and recurring monetization potential.",
        f"Demonstrated focus on execution with measurable traction signals ({traction[:60]}...)."
    ]

    growth_areas = [
        f"Quantify customer acquisition cost (CAC) vs lifetime value (LTV) assumptions in the {category} landscape.",
        "Add defensibility details regarding intellectual property, data flywheels, or partnership exclusivity."
    ]

    investor_questions = [
        f"What is your primary go-to-market distribution moat compared to established incumbents?",
        f"How will this ${int(funding):,} raise sustain runway to reach your next key milestone or valuation inflection point?"
    ]

    return {
        "score": score,
        "readiness_level": readiness,
        "executive_pitch": exec_pitch,
        "strengths": strengths,
        "growth_areas": growth_areas,
        "investor_questions": investor_questions,
        "ai_engine": "SheRise Intelligence Core (Add your Gemini API Key in Settings for live model)"
    }

def generate_investor_pitch(venture: dict, investor: dict, api_key: str = None) -> dict:
    """
    Generates a personalized, tailored cold pitch email from the founder to a specific investor,
    referencing the investor's exact thesis, sectors, and ticket size.
    """
    v_title = venture.get("title", "Our Startup")
    v_cat = venture.get("category", "Tech")
    v_stage = venture.get("stage", "Seed")
    v_sol = venture.get("solution", "")
    v_prob = venture.get("problem", "")
    v_trac = venture.get("traction", "Early customer validation")
    v_founder = venture.get("founder_name", "Founder")

    inv_name = investor.get("name", "Investor")
    inv_firm = investor.get("firm", "Venture Partner")
    inv_thesis = investor.get("thesis", "Early stage tech investments")

    key = get_api_key(api_key)

    if key:
        prompt = f"""
Write a high-converting, personalized investor outreach pitch email from a female founder to an investor:

Founder: {v_founder}
Startup: {v_title} ({v_cat}, {v_stage} stage)
Problem: {v_prob}
Solution: {v_sol}
Traction: {v_trac}

Recipient: {inv_name} at {inv_firm}
Investor Thesis: {inv_thesis}

Requirements:
- Professional, respectful, confident, and concise (under 250 words).
- Explicitly connect why the startup aligns directly with {inv_firm}'s investment thesis.
- Include a clear, low-friction call-to-action (e.g. 15-minute introductory call or reviewing deck).
- Return format: Subject Line followed by the Email Body.
"""
        try:
            raw = call_gemini_api(prompt, key, "You are a master pitch writer for female venture founders.")
            return {
                "pitch_text": raw.strip(),
                "investor_name": inv_name,
                "venture_title": v_title,
                "ai_engine": "Google Gemini Live API"
            }
        except Exception:
            pass

    # Heuristic template
    email_text = f"""Subject: {v_title} ({v_stage}) x {inv_firm}: Tailored Opportunity in {v_cat}

Dear {inv_name},

I hope this note finds you well. I’ve been following {inv_firm}’s impactful investments in {v_cat}, particularly your thesis on backing technical founders building high-moat solutions.

I’m {v_founder}, founder of {v_title}. We are addressing a critical market gap: {v_prob[:140]}...

To solve this, {v_title} has developed: {v_sol[:150]}...

Key Traction & Highlights:
• Stage: {v_stage}
• Validation: {v_trac}
• Market Opportunity: High-growth segment with strong tailwinds aligned with your focus areas.

Given your deep experience with portfolio companies in this space, I would be honored to share our 10-slide deck and see if this aligns with {inv_firm}’s current pipeline.

Would you be open to a 15-minute intro chat next Tuesday or Thursday?

Warm regards,

{v_founder}
Founder, {v_title}
"""
    return {
        "pitch_text": email_text.strip(),
        "investor_name": inv_name,
        "venture_title": v_title,
        "ai_engine": "SheRise Intelligence Core"
    }
