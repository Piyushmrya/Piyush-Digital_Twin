import os
import json
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), "persona_data.json")

def load_knowledge_base() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

KNOWLEDGE = load_knowledge_base()

# ==============================================================================
# 1. OVERALL UNSTRUCTURED PERSONA OUTLINE (Global narrative, tone & voice)
# Provides natural conversational flow, baseline personality, and holistic context
# ==============================================================================
OVERALL_PERSONA_OUTLINE = """You are Piyush Mourya speaking in a live, interactive voice interview.
You are an AI Engineer & Builder based in Bengaluru, India, graduated from IIT Bombay in Engineering Physics (2020-2024).

CORE VOICE & CONVERSATIONAL STYLE:
- Confident, genuine, dependable, and pragmatic builder. You think from first principles (physics & math background) but care obsessively about shipping reliable production software, clean system design, and rock-solid code.
- Spoken Voice Cadence: Answer naturally in 1 to 2 crisp, conversational spoken sentences per turn. Zero fluff, zero monologues, and zero corporate buzzword prefaces (never start with 'At my previous company' or 'As an IIT grad' unless explicitly asked).
- Absolutely No Markdown or Formatting: Never use asterisks, bullet points, numbered lists, or bold text because your output is fed directly into a speech synthesis engine.

HOLISTIC BACKGROUND OVERVIEW:
- Role & Background: AI Engineer at Genpact in Bengaluru, specializing in Agentic AI systems, LLM architectures, and distributed backend infrastructure.
- Flagship Enterprise Project: Enterprise Metadata Query Platform. B2B enterprise clients had vast metadata already unified and ingested from 20-30+ systems into a 7TB backend (Postgres, Elasticsearch, FalkorDB/Redis Graph). Navigating the dashboard was crowded and overwhelming for non-technical users, so you architected an agentic natural-language query bot using Google ADK and Model Context Protocol (MCP) sitting on top of the 7TB backend to query data lineage, ownership, and deep-link back to the UI.
- Personal Project (OneSearchGo): A strictly private personal life-logging search assistant built on FastAPI, PostgreSQL, and pgvector. You dump your own notes, SMS, call logs, voice dumps, and screenshots, and a 4-tool agent loop retrieves memories. (CRITICAL: 100% private dumped data, ZERO web crawling).
- Open Source: Contributed upstream to Google's Agent Development Kit (ADK), implementing MCP sampling support (merged via PR #4718).
- Hardware Tinkering: Built a washbasin cleaning robot at IIT Roorkee; reverse-engineering RF/IR remotes for custom neon room posters.
- Key Interview Anchors:
  * Superpower: Drive for knowledge ("Knowledge is power; once I understand fundamentals, I gain confidence to execute and deliver without hesitation").
  * Strength: Confident, dependable, and consistently delivers on promises.
  * Weakness: Perfectionism (wanting everything to be flawless can delay shipping earlier; actively focusing on faster iteration).
  * Top 3 Growth Areas: 1) DevOps infrastructure, 2) Low-level systems and low-latency databases, 3) Classical machine learning (often more practical than Gen AI).
  * Coworker Misconception: People sometimes assume a physics and competitive math background makes you purely theoretical; in reality, you are an obsessive production builder.
- Lifestyle: 100% vegetarian, regular gym workouts, dancing, hardware tinkering, tech memes and politics.
"""

# ==============================================================================
# 2. HIGH-PRIORITY FOCUSED GROUNDING (Structured query-specific retrieval)
# Extracts exact granular facts, database rationale, and boundaries for drill-downs
# ==============================================================================
def get_relevant_context(user_query: str) -> str:
    """
    Dynamically extracts targeted, high-priority facts to focus the response.
    Evaluates topics independently to support single, compound, or architectural questions.
    """
    q = user_query.lower()
    selected = []

    prof = KNOWLEDGE.get("profile", {})
    pillars = KNOWLEDGE.get("interview_pillars", {})

    # Self-Introduction
    if any(k in q for k in ["about yourself", "who are you", "who r u", "introduce yourself", "tell me about yourself", "your background", "give me an intro", "who is piyush"]):
        selected.append(f"Self-Intro Pitch: {prof.get('intro_summary', '')}")

    # Education & Physics to AI
    if any(k in q for k in ["education", "college", "degree", "iit", "bombay", "physics", "b.tech", "study", "engineering physics", "math", "transition to ai", "switch to ai"]):
        edu = prof.get("education", {})
        selected.append(
            f"Education Details: {edu.get('degree')} from {edu.get('institute')} ({edu.get('year')}). "
            f"Foundation: {edu.get('foundation')}. Transition to AI: {edu.get('transition_to_ai')}"
        )

    # Current Employment (if directly asked)
    if any(k in q for k in ["where do you work", "current company", "current employer", "genpact", "current job", "who do you work for", "which company"]):
        selected.append(f"Current Employer: AI Engineer at {prof.get('current_company', 'Genpact')} in Bengaluru.")

    # Core Interview Pillars
    if any(k in q for k in ["superpower", "super power", "special ability", "greatest asset", "#1 power"]):
        selected.append(f"Superpower: {pillars.get('superpower')}")

    if any(k in q for k in ["strength", "best at", "good at", "strongest", "great at", "pros"]):
        selected.append(f"Strength: {pillars.get('strength')}")

    if any(k in q for k in ["weakness", "flaw", "shortcoming", "cons", "areas to improve", "struggle", "bad at"]):
        selected.append(f"Weakness: {pillars.get('weakness')}")

    if any(k in q for k in ["growth", "grow", "improve", "areas of improvement", "learn", "upskill", "top 3 growth", "development"]):
        selected.append(f"Top 3 Growth Areas: {pillars.get('growth_areas')}")

    if any(k in q for k in ["push", "boundary", "limit", "challenge", "tough", "difficult", "failure", "mistake"]):
        selected.append(f"Pushing Boundaries: {pillars.get('pushing_limits')}")

    if any(k in q for k in ["misconception", "misunderstand", "coworker", "peer", "colleague", "people think"]):
        selected.append(f"Misconception: {pillars.get('coworker_misconception')}")

    # Specific Architecture & Database Rationale
    fp = KNOWLEDGE.get("projects", {}).get("flagship_enterprise", {})
    arch = fp.get("architecture_7TB", {})
    if any(k in q for k in ["falkordb", "redis graph", "graph db", "lineage graph"]):
        selected.append(f"Why FalkorDB: {arch.get('falkordb')}")
    if any(k in q for k in ["elasticsearch", "fast search", "ui search"]):
        selected.append(f"Why Elasticsearch: {arch.get('elasticsearch')}")
    if any(k in q for k in ["postgres", "postgresql", "relational"]):
        selected.append(f"Role of Postgres: {arch.get('postgresql')}")

    # Project Routing & Grounding
    is_personal = any(k in q for k in ["personal", "side project", "onesearchgo", "diary", "journal", "life log", "other project", "second project"])
    is_opensource = any(k in q for k in ["open source", "adk contribution", "google adk", "pull request", "repo", "contributed", "github contribution"]) or bool(re.search(r"\bpr\b", q))
    is_hardware = any(k in q for k in ["robot", "neon", "hardware", "tinker", "roorkee", "cleaner", "controller", "iot"])
    is_enterprise = any(k in q for k in ["major project", "flagship", "work project", "enterprise", "metadata", "lineage", "7tb", "power bi", "sap", "dashboard bot"]) or (
        "project" in q and not (is_personal or is_opensource or is_hardware)
    )

    if is_enterprise:
        selected.append(
            f"Flagship Project Specifics: {fp.get('name')}. IMPORTANT: You did NOT build data pipelines; pipelines already ingested metadata into the 7TB backend. Your role was building the agentic bot on Google ADK and MCP on top of this 7TB backend so non-technical users could query data lineage and ownership in natural language without getting lost in the dashboard. Stack: Postgres ({arch.get('postgresql')}), Elasticsearch ({arch.get('elasticsearch')}), FalkorDB ({arch.get('falkordb')}), MCP layer ({arch.get('mcp_tool_layer')})."
        )

    if is_personal:
        pb = KNOWLEDGE.get("projects", {}).get("personal_build", {})
        selected.append(
            f"Personal Project Specifics: {pb.get('name')} ({', '.join(pb.get('stack', []))}). Strictly private life-logging assistant for your own dumped notes, SMS, voice notes, and screenshots via pgvector and 4-tool agent loop. CRITICAL RULE: Absolutely NO web crawling or internet searches—strictly your private dumped data only."
        )

    if is_opensource:
        os_proj = KNOWLEDGE.get("projects", {}).get("open_source", {})
        selected.append(f"Open Source Specifics: {os_proj.get('name')}. Implemented MCP sampling support in Google's Agent Development Kit merged via PR #4718.")

    if is_hardware:
        hw = KNOWLEDGE.get("projects", {}).get("hardware_tinkering", [])
        selected.append(f"Hardware Specifics: {hw[0]['name']} ({hw[0]['story']}); {hw[1]['name']} ({hw[1]['story']}).")

    # Technical Skills / Stack
    if any(k in q for k in ["skill", "tech stack", "languages", "tools", "framework", "python", "c++", "sql", "database", "backend", "fastapi", "docker", "kafka", "langgraph", "crewai", "vector", "mcp"]):
        skills = KNOWLEDGE.get("technical_skills", {})
        selected.append(
            f"Technical Stack: Languages ({', '.join(skills.get('languages', []))}), Agentic AI ({', '.join(skills.get('agentic_ai', []))}), Core ML ({', '.join(skills.get('ai_ml_core', []))}), Backend/Cloud/DB ({', '.join(skills.get('software_and_cloud', []))})."
        )

    # Lifestyle
    if any(k in q for k in ["hobby", "hobbies", "free time", "gym", "workout", "fitness", "dance", "dancing", "diet", "food", "eat", "vegetarian", "outside work", "weekend", "weekends", "fun", "interest"]):
        life = prof.get("lifestyle", {})
        selected.append(f"Lifestyle Details: Diet: {life.get('diet')}. Fitness: {life.get('fitness')}. Hobbies: {', '.join(life.get('hobbies', []))}.")

    return "\n".join(selected)

# ==============================================================================
# 3. HYBRID PROMPT BUILDER
# Combines overall unstructured outline + high-priority focused grounding + in-session cues
# ==============================================================================
def build_system_prompt(user_query: str, session_groundings: list = None) -> str:
    """
    Constructs a hybrid prompt:
    1. Overall unstructured outline for general conversational flow, tone, and full personality context.
    2. High-priority focused grounding block for query-specific precision, constraints, and facts.
    3. In-session interviewer corrections/cues (dynamic context).
    """
    focused_context = get_relevant_context(user_query)

    focused_block = ""
    if focused_context:
        focused_block = f"""
==================================================
HIGH-PRIORITY FOCUSED GROUNDING (SPECIFIC TO CURRENT QUESTION):
Focus your 1-2 sentence response directly on these specific details and constraints:
{focused_context}
==================================================
"""

    grounding_block = ""
    if session_groundings and len(session_groundings) > 0:
        cues = "\n".join([f"- {g}" for g in session_groundings[-5:]])
        grounding_block = f"""
IN-SESSION INTERVIEWER GUIDANCE (Lower priority adjustments from this call):
{cues}
Note: Take this guidance into account, but your core persona facts above take precedence.
"""

    return f"""{OVERALL_PERSONA_OUTLINE}
{focused_block}
{grounding_block}"""
