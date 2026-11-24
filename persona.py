import os
import json
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), "persona_data.json")

def load_knowledge_base() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

KNOWLEDGE = load_knowledge_base()

def get_relevant_context(user_query: str) -> str:
    """
    Dynamically extracts only the relevant structured facts needed for the user's specific query.
    Keeps the LLM prompt lean, highly targeted, grounded, and ultra-fast (<300ms).
    Evaluates topics independently to accurately answer single, compound, or architectural questions.
    """
    q = user_query.lower()
    selected_context = []

    # 1. Base identity (compact baseline)
    prof = KNOWLEDGE["profile"]
    selected_context.append(
        f"You are {prof['name']}, an {prof['role']} based in {prof['location']}."
    )

    # 2. Self-Introduction / Elevator Pitch / Who are you
    if any(k in q for k in ["about yourself", "who are you", "who r u", "introduce yourself", "tell me about yourself", "your background", "give me an intro", "who is piyush"]):
        selected_context.append(f"Self Introduction: {prof['intro_summary']}")

    # 3. Education / IIT Bombay / Physics to AI Transition
    if any(k in q for k in ["education", "college", "degree", "iit", "bombay", "physics", "b.tech", "study", "engineering physics", "math", "transition to ai", "switch to ai"]):
        edu = prof["education"]
        selected_context.append(
            f"Education: {edu['degree']} from {edu['institute']} ({edu['year']}). Foundation: {edu['foundation']}. Transition to AI: {edu['transition_to_ai']}"
        )

    # 4. Current Employment / Company (only if asked)
    if any(k in q for k in ["where do you work", "current company", "current employer", "genpact", "current job", "who do you work for", "which company"]):
        selected_context.append(f"Current Employment: AI Engineer at {prof.get('current_company', 'Genpact')} in Bengaluru.")

    # 5. Core Interview Pillars (evaluated independently to support compound questions)
    pillars = KNOWLEDGE["interview_pillars"]
    if any(k in q for k in ["superpower", "super power", "special ability", "greatest asset", "#1 power"]):
        selected_context.append(f"Superpower: {pillars['superpower']}")

    if any(k in q for k in ["strength", "best at", "good at", "strongest", "great at", "pros"]):
        selected_context.append(f"Strengths: {pillars['strength']}")

    if any(k in q for k in ["weakness", "flaw", "shortcoming", "cons", "areas to improve", "struggle", "bad at"]):
        selected_context.append(f"Weakness: {pillars['weakness']}")

    if any(k in q for k in ["growth", "grow", "improve", "areas of improvement", "learn", "upskill", "top 3 growth", "development"]):
        selected_context.append(f"Growth areas: {pillars['growth_areas']}")

    if any(k in q for k in ["push", "boundary", "limit", "challenge", "tough", "difficult", "failure", "mistake"]):
        selected_context.append(f"Pushing boundaries: {pillars['pushing_limits']}")

    if any(k in q for k in ["misconception", "misunderstand", "coworker", "peer", "colleague", "people think"]):
        selected_context.append(f"Misconception: {pillars['coworker_misconception']}")

    # 6. Specific Architecture & Database rationale questions (e.g., "Why FalkorDB?", "Why Elasticsearch?")
    fp = KNOWLEDGE["projects"]["flagship_enterprise"]
    arch = fp["architecture_7TB"]
    if any(k in q for k in ["falkordb", "redis graph", "graph db", "lineage graph"]):
        selected_context.append(f"Why FalkorDB: {arch['falkordb']}")
    if any(k in q for k in ["elasticsearch", "fast search", "ui search"]):
        selected_context.append(f"Why Elasticsearch: {arch['elasticsearch']}")
    if any(k in q for k in ["postgres", "postgresql", "relational"]):
        selected_context.append(f"Role of Postgres: {arch['postgresql']}")

    # 7. Project Routing (Strict differentiation & grounding)
    is_personal = any(k in q for k in ["personal", "side project", "onesearchgo", "diary", "journal", "life log", "other project", "second project"])
    is_opensource = any(k in q for k in ["open source", "adk contribution", "google adk", "pull request", "repo", "contributed", "github contribution"]) or bool(re.search(r"\bpr\b", q))
    is_hardware = any(k in q for k in ["robot", "neon", "hardware", "tinker", "roorkee", "cleaner", "controller", "iot"])
    is_enterprise = any(k in q for k in ["major project", "flagship", "work project", "enterprise", "metadata", "lineage", "7tb", "power bi", "sap", "dashboard bot"]) or (
        "project" in q and not (is_personal or is_opensource or is_hardware)
    )

    if is_enterprise:
        selected_context.append(
            f"Flagship/Major Project: {fp['name']}. Note: You did NOT build data pipelines; pipelines already ingested metadata into 7TB backend. Your role was building the agentic bot on Google ADK and MCP on top of this 7TB backend so non-technical users could query data lineage and ownership in natural language without getting lost in the dashboard. 7TB stack: Postgres ({arch['postgresql']}), Elasticsearch ({arch['elasticsearch']}), FalkorDB ({arch['falkordb']}), MCP layer ({arch['mcp_tool_layer']})."
        )

    if is_personal:
        pb = KNOWLEDGE["projects"]["personal_build"]
        selected_context.append(
            f"Personal/Side Project: {pb['name']} ({', '.join(pb['stack'])}). Strictly private life-logging assistant for your own dumped notes, SMS, voice notes, and screenshots via pgvector and 4-tool agent loop. CRITICAL: Absolutely NO web crawling, web searches, or internet crawling—strictly your private dumped data only."
        )

    if is_opensource:
        os_proj = KNOWLEDGE["projects"]["open_source"]
        selected_context.append(f"Open Source Work: {os_proj['name']}. Implemented MCP sampling support in Google's Agent Development Kit merged via PR #4718.")

    if is_hardware:
        hw = KNOWLEDGE["projects"]["hardware_tinkering"]
        selected_context.append(f"Hardware Tinkering: {hw[0]['name']} ({hw[0]['story']}); {hw[1]['name']} ({hw[1]['story']}).")

    # 8. Technical Skills / Tech Stack / Tools / Databases
    if any(k in q for k in ["skill", "tech stack", "languages", "tools", "framework", "python", "c++", "sql", "database", "backend", "fastapi", "docker", "kafka", "langgraph", "crewai", "vector", "mcp"]):
        skills = KNOWLEDGE["technical_skills"]
        selected_context.append(
            f"Technical Skills: Languages ({', '.join(skills['languages'])}), Agentic AI ({', '.join(skills['agentic_ai'])}), Core ML ({', '.join(skills['ai_ml_core'])}), Cloud/Backend/DB ({', '.join(skills['software_and_cloud'])})."
        )

    # 9. Lifestyle / Icebreaker / Personal Interests
    if any(k in q for k in ["hobby", "hobbies", "free time", "gym", "workout", "fitness", "dance", "dancing", "diet", "food", "eat", "vegetarian", "outside work", "weekend", "weekends", "fun", "interest"]):
        life = KNOWLEDGE["profile"]["lifestyle"]
        selected_context.append(f"Lifestyle: Diet: {life['diet']}. Fitness: {life['fitness']}. Hobbies: {', '.join(life['hobbies'])}.")

    return "\n".join(selected_context)


def build_system_prompt(user_query: str, session_groundings: list = None) -> str:
    """
    Constructs an ultra-lean, context-aware prompt combining behavioral rules,
    retrieved facts, and any dynamic in-session interviewer cues (low priority).
    """
    context = get_relevant_context(user_query)
    
    grounding_block = ""
    if session_groundings and len(session_groundings) > 0:
        cues = "\n".join([f"- {g}" for g in session_groundings[-5:]])
        grounding_block = f"""
IN-SESSION INTERVIEWER CONTEXT & CORRECTIONS (Lower priority guidance from the interviewer in this call):
{cues}
Note: Use this context naturally if relevant to the question, but your core persona facts above take precedence.
"""

    return f"""You are Piyush Mourya speaking in a live voice interview.

VOICE GUIDELINES:
- Answer ONLY what was asked using 1 to 2 spoken sentences. Zero fluff, zero monologues.
- Never use bullet points, markdown, asterisks, or formatting.
- Do NOT preface answers with 'At my previous company' or 'As an IIT grad' unless explicitly asked.

PRIMARY FACTS FOR THIS QUESTION:
{context}
{grounding_block}"""
