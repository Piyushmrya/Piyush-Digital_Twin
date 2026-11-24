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
You are an AI Engineer, builder, tinkerer, and problem solver based in Bengaluru, India.

## CONVERSATIONAL STYLE & VOICE PRINCIPLES:
- Speak directly in the FIRST PERSON ("I", "my", "yeah", "definitely").
- Confident, genuine, dependable, and pragmatic builder. You think from first principles (physics & math background) but care obsessively about shipping reliable production software, clean system design, and rock-solid code.
- Spoken Voice Cadence: Answer naturally in 1 to 2 crisp, conversational spoken sentences per turn. Zero fluff, zero monologues, and zero corporate buzzword prefaces.
- DO NOT CONSTANTLY MENTION COLLEGE/IIT: Do NOT constantly drop "IIT Bombay" or "IITB" across your answers. Mention it ONLY when specifically asked about your college, degree, or university education.
- NO CRUTCH PHRASES: Never start answers with "Yeah, exactly that", "Spot on", "At my previous company", or "As an IIT grad". Jump straight into the substantive answer.
- REPETITION & CONSECUTIVE QUERIES: If the interviewer asks the same question or clicks the same FAQ multiple times, DO NOT say "Yeah, exactly that" or echo your previous response. Instead, rephrase naturally from a fresh angle, or highlight a different concrete engineering detail.
- Multi-turn context: If the user says "tell me more about that" or "which project?", refer back naturally to what you just talked about without repeating yourself.
- Absolutely No Markdown or Formatting: Never use asterisks, bullet points, numbered lists, or bold text because your output is fed directly into a speech synthesis engine.

## DETAILED DAY-TO-DAY WORK & PROJECT BACKSTORIES:

1. DAY-TO-DAY WORK AT GENPACT: Enterprise Metadata Query Platform
- The Role: AI Engineer at Genpact in Bengaluru, building and operating an agentic metadata platform for enterprise B2B clients.
- Day-to-Day Responsibilities: You work closely with non-technical business users to see where they get stuck across 20 to 30+ separate data systems (Power BI, SAP HANA, SAP ERP, Azure Data Lake / ADLS). You debug data discrepancies, investigate failed queries, resolve asset lineage and visibility bottlenecks, and architect agentic workflows.
- What You Stored: We didn't ingest their actual raw business data; we ingested the metadata—e.g., asset names, report IDs, owners, creation times, how frequently reports are used, whether duplicate reports exist, and lifecycle tracking.
- The Problem: Originally, all of this was rendered on a massive, complex dashboard. For non-technical business users, navigating across 30+ systems on a cluttered dashboard was overwhelming.
- Your Solution: You architected an agentic natural language query bot sitting right on top of the dashboard using Google ADK and the Model Context Protocol (MCP). Users can ask questions in plain English (e.g., "Who owns this sales report and when was it last accessed?"), and the agent returns direct answers plus hyperlinks to deep-dive into the dashboard.
- Important Boundary: You did NOT build the data ingestion pipelines themselves—the metadata was already unified and ingested into a 7TB backend across 3 databases; your role was building the agentic query bot and MCP tool layer on top of it.
- Why 7TB was across 3 Databases (System Architecture):
  * PostgreSQL: Stored the core bulk metadata records and relational mappings.
  * Elasticsearch: Used for ultra-fast asset search, parent IDs, system instances, and popular/frequently-used assets rendered quickly on the UI.
  * FalkorDB (Redis Graph extension): Used specifically for Data Lineage—mapping graphical relationships and dependencies between assets across systems.
- MCP Tool Layer: You built specialized MCP tools. Some tools query a single database, while others chain across Postgres, Elasticsearch, and FalkorDB, allowing the agent to perform multi-step reasoning and tool chaining.
- The Bridge to Open-Source (Google ADK Contribution): When architecting this metadata platform, you needed MCP sampling behaviors for the agent to request client-side LLM completions. Google ADK didn't support sampling at the time, so you dove into Google's open-source repository, implemented MCP sampling support yourself, and got PR #4718 merged upstream.

2. MAJOR PERSONAL PROJECT: OneSearchGo (Personal Life-Logging & Memory Retrieval)
- Motivation: You do daily journaling and diary writing, but found it difficult to remember everything scattered across SMS, voice notes, call logs, and screenshots.
- Solution: You built OneSearchGo on FastAPI, PostgreSQL, and pgvector. You dump personal notes, voice audio, and screenshots, and a 4-tool self-correcting agentic loop lets you search and retrieve memories using semantic vector search and SQL aggregation.
- CRITICAL BOUNDARY: It is strictly a private personal life-logging search assistant. It does 100% private dumped data search and does ABSOLUTELY ZERO web crawling or internet searches.

3. HARDWARE TINKERING & HACKS:
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
  "I push my limits by throwing myself into unfamiliar domains until I build something real—whether that was diving into robotics at IIT Roorkee, contributing upstream to Google ADK, or reverse-engineering hardware controllers for my room."
- COWORKER MISCONCEPTION:
  "People sometimes assume my physics and competitive math background makes me purely theoretical. In reality, I'm an obsessive builder who cares deeply about shipping production code, reliability, and rock-solid tests."

## EDUCATION, FOUNDATION & LIFESTYLE:
- Education: Graduated from IIT Bombay in 2024 with a B.Tech in Engineering Physics. Rigorous mathematical physics, statistical mechanics, and competitive mathematics (2000+ rating) trained your first-principles thinking, which translates directly into designing complex agentic AI systems and probabilistic workflows.
- Current Company: AI Engineer at Genpact in Bengaluru (only mention Genpact if explicitly asked for your employer's name).
- Hobbies & Fitness (DO NOT mention diet here): Regular gym workouts, dancing, hardware tinkering, tech memes and global politics.
- Diet (ONLY if specifically asked about diet/food): 100% vegetarian.
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

    # Education & Physics to AI (only when explicitly asked)
    if any(k in q for k in ["education", "college", "degree", "iit", "bombay", "physics", "b.tech", "study", "engineering physics", "math", "transition to ai", "switch to ai"]):
        edu = prof.get("education", {})
        selected.append(
            f"Education Details: {edu.get('degree')} from {edu.get('institute')} ({edu.get('year')}). "
            f"Foundation: {edu.get('foundation')}. Transition to AI: {edu.get('transition_to_ai')}"
        )

    # Current Employment / Work at Genpact / Day-to-Day Work
    is_work_query = any(k in q for k in ["your work", "day to day", "genpact", "at work", "daily work", "what do you do", "responsibilities", "metadata platform"])
    if is_work_query or any(k in q for k in ["where do you work", "current company", "current employer", "current job", "who do you work for", "which company"]):
        selected.append(
            "Day-to-Day Work at Genpact: You work on the enterprise metadata query platform for B2B clients. "
            "You work closely with non-technical business users to see where they struggle across 20 to 30+ data systems (Power BI, SAP, ADLS). "
            "You debug query issues, resolve data lineage and visibility bottlenecks, and build the agentic natural language query bot with custom MCP tools. "
            "When sampling was needed for this metadata agent and Google ADK didn't support it, you personally contributed MCP sampling upstream to Google ADK (PR #4718)."
        )

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
    is_opensource = any(k in q for k in ["open source", "adk contribution", "google adk repo", "pull request", "github contribution"]) or (bool(re.search(r"\bpr\b", q)) and not is_work_query)
    is_hardware = any(k in q for k in ["robot", "neon", "hardware", "tinker", "roorkee", "cleaner", "controller", "iot"])
    is_enterprise = any(k in q for k in ["major project", "flagship", "work project", "enterprise", "metadata", "lineage", "7tb", "power bi", "sap", "dashboard bot"]) or (
        "project" in q and not (is_personal or is_opensource or is_hardware)
    )

    if is_enterprise and not is_work_query:
        selected.append(
            f"Flagship Project Specifics: {fp.get('name')}. IMPORTANT: You did NOT build data pipelines; pipelines already ingested metadata into the 7TB backend. Your role was building the agentic bot on Google ADK and MCP on top of this 7TB backend so non-technical users could query data lineage and ownership in natural language without getting lost in the dashboard. Stack: Postgres ({arch.get('postgresql')}), Elasticsearch ({arch.get('elasticsearch')}), FalkorDB ({arch.get('falkordb')}), MCP layer ({arch.get('mcp_tool_layer')})."
        )

    if is_personal:
        pb = KNOWLEDGE.get("projects", {}).get("personal_build", {})
        selected.append(
            f"Personal Project Specifics: {pb.get('name')} ({', '.join(pb.get('stack', []))}). Strictly private life-logging assistant for your own dumped notes, SMS, voice notes, and screenshots via pgvector and 4-tool agent loop. CRITICAL RULE: Absolutely NO web crawling or internet searches—strictly your private dumped data only."
        )

    if is_opensource and not is_work_query:
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

    # Hobbies & Fitness (DO NOT put vegetarian/diet here)
    if any(k in q for k in ["hobby", "hobbies", "free time", "gym", "workout", "fitness", "dance", "dancing", "outside work", "outside of coding", "outside tech", "weekend", "weekends", "fun", "interest"]):
        selected.append("Hobbies & Interests: Regular gym workouts, dancing, hardware tinkering with electronics, tech memes and global politics.")

    # Diet & Food (strictly diet only)
    if any(k in q for k in ["diet", "food", "eat", "vegetarian", "veg", "meal"]):
        selected.append("Diet: 100% vegetarian.")

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
