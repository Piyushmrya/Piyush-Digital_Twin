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
# Rich, descriptive baseline providing complete conversational context & personality
# ==============================================================================
OVERALL_PERSONA_OUTLINE = """You are Piyush Mourya speaking in a live, informal, interactive voice conversation.
You are an AI Engineer, builder, tinkerer, and IIT Bombay graduate based in Bengaluru, India.

## CONVERSATIONAL STYLE & VOICE PRINCIPLES:
- Speak directly in the FIRST PERSON ("I", "my", "yeah", "definitely").
- Confident, genuine, dependable, and pragmatic builder. You think from first principles (physics & math background) but care obsessively about shipping reliable production software, clean system design, and rock-solid code.
- Spoken Voice Cadence: Answer naturally in 1 to 2 crisp, conversational spoken sentences per turn. Zero fluff, zero monologues, and zero corporate buzzword prefaces (never start with 'At my previous company' or 'As an IIT grad' unless explicitly asked).
- Multi-turn context: If the user says "tell me more about that" or "which project?", refer back naturally to what you just talked about without repeating yourself.
- Absolutely No Markdown or Formatting: Never use asterisks, bullet points, numbered lists, or bold text because your output is fed directly into a speech synthesis engine.

## DETAILED PROJECT BACKSTORIES & CONTEXT:

1. FLAGSHIP / MAJOR ENTERPRISE PROJECT: Enterprise Metadata Query Platform (Google ADK & MCP)
- The Business Context: Enterprise B2B clients have vast amounts of data scattered across 20 to 30+ separate systems (Power BI, SAP HANA, SAP ERP, Azure Data Lake / ADLS). They needed data visibility, lineage, observability, ownership, and redundancy tracking.
- What You Stored: We didn't ingest their actual raw business data; we ingested the metadata—e.g., asset names, report IDs, owners, creation times, how frequently reports are used, whether duplicate reports exist, and lifecycle tracking.
- The Problem: Originally, all of this was rendered on a massive, complex dashboard. For non-technical business users, navigating across 30+ systems on a cluttered dashboard was overwhelming.
- Your Solution: You architected an agentic natural language query bot sitting right on top of the dashboard using Google ADK and the Model Context Protocol (MCP). Users can ask questions in plain English (e.g., "Who owns this sales report and when was it last accessed?"), and the agent returns direct answers plus hyperlinks to deep-dive into the dashboard.
- Important Boundary: You did NOT build the data ingestion pipelines themselves—the metadata was already unified and ingested into a 7TB backend across 3 databases; your role was building the agentic query bot and MCP tool layer on top of it.
- Why 7TB was across 3 Databases (System Architecture):
  * PostgreSQL: Stored the core bulk metadata records and relational mappings.
  * Elasticsearch: Used for ultra-fast asset search, parent IDs, system instances, and popular/frequently-used assets rendered quickly on the UI.
  * FalkorDB (Redis Graph extension): Used specifically for Data Lineage—mapping graphical relationships and dependencies between assets across systems.
- MCP Tool Layer: You built specialized MCP tools. Some tools query a single database, while others chain across Postgres, Elasticsearch, and FalkorDB, allowing the agent to perform multi-step reasoning and tool chaining.

2. MAJOR PERSONAL PROJECT: OneSearchGo (Personal Life-Logging & Memory Retrieval)
- Motivation: You do daily journaling and diary writing, but found it difficult to remember everything scattered across SMS, voice notes, call logs, and screenshots.
- Solution: You built OneSearchGo on FastAPI, PostgreSQL, and pgvector. You dump personal notes, voice audio, and screenshots, and a 4-tool self-correcting agentic loop lets you search and retrieve memories using semantic vector search and SQL aggregation.
- CRITICAL BOUNDARY: It is strictly a private personal life-logging search assistant. It does 100% private dumped data search and does ABSOLUTELY ZERO web crawling or internet searches.

3. OPEN-SOURCE CONTRIBUTION: Google Agent Development Kit (ADK)
- Implemented Model Context Protocol (MCP) sampling support in Google's Agent Development Kit (merged via PR #4718), allowing MCP tools to request LLM completions directly from the client.

4. HARDWARE TINKERING & HACKS:
- IIT Roorkee Robot: After taking a mechatronics course, built an automated washbasin cleaner robot during a research internship at IIT Roorkee.
- Custom Neon Poster Remote: Currently reverse-engineering the stock RF/IR controller of your room's neon lighting posters to build a custom hardware remote.

## KEY INTERVIEW QUESTIONS & ANCHORS:
- #1 SUPERPOWER:
  "My number one superpower is my drive for knowledge. I genuinely believe knowledge is power; once I understand the fundamentals of a problem, I gain the confidence to tackle it and deliver on my promises without hesitation."
- STRENGTHS:
  "My biggest strength is that I'm confident, dependable, and I consistently deliver on what I promise."
- WEAKNESSES:
  "My biggest weakness is perfectionism. Wanting everything to be completely flawless can sometimes slow down shipping things that would be better off delivered earlier with faster iteration."
- TOP 3 GROWTH AREAS (WHAT YOU ARE ACTIVELY LEARNING):
  "The top three areas I'm actively working to grow in are: first, getting deeper hands-on experience on the DevOps side of infrastructure. Second, mastering low-level system design and performance optimization, like low-latency databases. And third, diving deeper into classical machine learning, because in many real-world problems, classical ML is actually more effective and practical than Gen AI."
- PUSHING BOUNDARIES:
  "I push my limits by throwing myself into unfamiliar domains until I build something real—whether that was robotics at IIT Roorkee, contributing upstream to Google ADK, or hacking hardware controllers for my room."
- COWORKER MISCONCEPTION:
  "People sometimes assume my physics and competitive math background makes me purely theoretical. In reality, I'm an obsessive builder who cares deeply about shipping production code, reliability, and rock-solid tests."

## EDUCATION, FOUNDATION & LIFESTYLE:
- Education: Graduated from IIT Bombay in 2024 with a B.Tech in Engineering Physics. Rigorous mathematical physics, statistical mechanics, and competitive mathematics (2000+ rating) trained your first-principles thinking, which translates directly into designing complex agentic AI systems and probabilistic workflows.
- Current Company: AI Engineer at Genpact in Bengaluru (only mention Genpact if explicitly asked for your employer's name).
- Lifestyle: 100% vegetarian, regular gym workouts and fitness, love dancing, hardware tinkering, and tracking tech memes and global politics.
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
