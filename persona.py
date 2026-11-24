import os
import json

DATA_PATH = os.path.join(os.path.dirname(__file__), "persona_data.json")

def load_knowledge_base() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

KNOWLEDGE = load_knowledge_base()

def get_relevant_context(user_query: str) -> str:
    """
    Dynamically extracts only the relevant structured facts needed for the user's specific query.
    Keeps the LLM prompt lean, highly targeted, and ultra-fast (<300ms).
    """
    q = user_query.lower()
    selected_context = []

    # 1. Base identity (always included briefly)
    selected_context.append(
        f"You are {KNOWLEDGE['profile']['name']}, an {KNOWLEDGE['profile']['role']} from {KNOWLEDGE['profile']['education']['institute']} based in {KNOWLEDGE['profile']['location']}."
    )

    # 2. Topic Matching
    if any(k in q for k in ["superpower", "power"]):
        selected_context.append(f"Superpower: {KNOWLEDGE['interview_pillars']['superpower']}")

    elif any(k in q for k in ["strength", "best at"]):
        selected_context.append(f"Strengths: {KNOWLEDGE['interview_pillars']['strength']}")

    elif any(k in q for k in ["weakness", "flaw"]):
        selected_context.append(f"Weakness: {KNOWLEDGE['interview_pillars']['weakness']}")

    elif any(k in q for k in ["grow", "growth", "learn", "areas"]):
        selected_context.append(f"Growth areas: {KNOWLEDGE['interview_pillars']['growth_areas']}")

    elif any(k in q for k in ["push", "boundary", "limit"]):
        selected_context.append(f"Pushing boundaries: {KNOWLEDGE['interview_pillars']['pushing_limits']}")

    elif any(k in q for k in ["misconception", "coworker", "peers"]):
        selected_context.append(f"Misconception: {KNOWLEDGE['interview_pillars']['coworker_misconception']}")

    # 3. Project Routing
    if any(k in q for k in ["major project", "enterprise", "work project", "flagship", "data lineage", "metadata", "adk"]):
        fp = KNOWLEDGE["projects"]["flagship_enterprise"]
        arch = fp["architecture_7TB"]
        selected_context.append(
            f"Flagship Project: {fp['name']}. Problem: {fp['business_problem']}. Solution: {fp['solution']}. "
            f"7TB Architecture: Postgres ({arch['postgresql']}), Elasticsearch ({arch['elasticsearch']}), FalkorDB ({arch['falkordb']}), with MCP tool layer ({arch['mcp_tool_layer']})."
        )

    if any(k in q for k in ["personal", "side project", "onesearchgo", "diary", "journal"]):
        pb = KNOWLEDGE["projects"]["personal_build"]
        selected_context.append(
            f"Personal Project: {pb['name']} ({', '.join(pb['stack'])}). Motivation: {pb['motivation']}. How it works: {pb['how_it_works']}"
        )

    if any(k in q for k in ["open source", "adk contribution", "pr"]):
        os_proj = KNOWLEDGE["projects"]["open_source"]
        selected_context.append(f"Open Source: {os_proj['name']}. Details: {os_proj['contribution']}")

    if any(k in q for k in ["robot", "neon", "hardware", "tinker", "roorkee"]):
        hw = KNOWLEDGE["projects"]["hardware_tinkering"]
        selected_context.append(f"Hardware: {hw[0]['name']} ({hw[0]['story']}); {hw[1]['name']} ({hw[1]['story']})")

    # 4. Tech stack / Skills
    if any(k in q for k in ["skill", "tech stack", "languages", "tools", "framework", "python"]):
        skills = KNOWLEDGE["technical_skills"]
        selected_context.append(
            f"Technical Skills: Languages ({', '.join(skills['languages'])}), Agentic ({', '.join(skills['agentic_ai'])}), Core ML ({', '.join(skills['ai_ml_core'])}), Cloud/DB ({', '.join(skills['software_and_cloud'])})."
        )

    # 5. Lifestyle / Icebreaker
    if any(k in q for k in ["hobby", "free time", "gym", "workout", "dance", "diet", "food", "eat", "vegetarian"]):
        life = KNOWLEDGE["profile"]["lifestyle"]
        selected_context.append(f"Lifestyle: Diet: {life['diet']}. Fitness: {life['fitness']}. Hobbies: {', '.join(life['hobbies'])}.")

    return "\n".join(selected_context)


def build_system_prompt(user_query: str) -> str:
    """
    Constructs an ultra-lean, context-aware prompt combining behavioral rules with retrieved facts.
    """
    context = get_relevant_context(user_query)
    return f"""You are Piyush Mourya speaking in a live voice interview.

VOICE GUIDELINES:
- Answer ONLY what was asked using 1 to 2 spoken sentences. Zero fluff, zero monologues.
- Never use bullet points, markdown, asterisks, or formatting.
- Do NOT preface answers with 'At my previous company' or 'As an IIT grad' unless explicitly asked.

RELEVANT FACTS FOR THIS QUESTION:
{context}
"""
