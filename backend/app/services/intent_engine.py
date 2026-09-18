import json
import os
import random
import logging
import httpx
from typing import Dict, Any, List, Optional
from rapidfuzz import fuzz
from app.core.config import settings
from app.core.languages import get_language_config, SUPPORTED_LANGUAGES
from app.services.problem_solver import problem_solver

logger = logging.getLogger(__name__)

INTENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "training_intents.json")

class NavigationIntentEngine:
    """
    Trainable Multilingual Intent Classification & Voice Navigation Engine.
    Supports English, Marathi, and extensible local Indic languages.
    """

    def __init__(self):
        self.routes_data: List[Dict[str, Any]] = []
        self.load_training_data()

    def load_training_data(self) -> None:
        """Loads or reloads the trainable routes and utterances dataset."""
        try:
            if os.path.exists(INTENTS_FILE_PATH):
                with open(INTENTS_FILE_PATH, "r", encoding="utf-8") as f:
                    self.routes_data = json.load(f)
                logger.info(f"Loaded {len(self.routes_data)} routes with multilingual training intents.")
            else:
                self.routes_data = []
        except Exception as e:
            logger.error(f"Failed to load training intents: {e}")
            self.routes_data = []

    def save_training_data(self) -> bool:
        """Persists training routes and utterances to JSON file."""
        try:
            with open(INTENTS_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.routes_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to persist training intents: {e}")
            return False

    def get_all_routes(self) -> List[Dict[str, Any]]:
        """Returns the full list of trained routes and metadata."""
        return self.routes_data

    def train_utterance(self, route_id: str, utterance: str, lang_code: str = "en") -> Dict[str, Any]:
        """
        Trains the AI assistant with a new custom voice phrase for a route in real time.
        """
        lang = "mr" if "mr" in lang_code.lower() else "en"
        target_field = f"utterances_{lang}"
        
        route = next((r for r in self.routes_data if r["route_id"] == route_id), None)
        if not route:
            return {"success": False, "message": f"Route '{route_id}' not found."}

        if target_field not in route:
            route[target_field] = []

        cleaned = utterance.strip()
        if not cleaned:
            return {"success": False, "message": "Utterance cannot be empty."}

        if cleaned not in route[target_field]:
            route[target_field].append(cleaned)
            self.save_training_data()
            return {
                "success": True,
                "message": f"Successfully trained '{cleaned}' for route '{route_id}' ({lang}).",
                "route_id": route_id,
                "total_utterances": len(route[target_field])
            }
        
        return {
            "success": True,
            "message": f"Utterance '{cleaned}' already exists for route '{route_id}'.",
            "route_id": route_id
        }

    def _fuzzy_match(self, text: str, lang_code: str) -> Optional[Dict[str, Any]]:
        """
        Calculates fuzzy match scores across keywords and trained utterances.
        """
        query = text.strip().lower()
        best_match = None
        highest_score = 0.0

        lang_key = "mr" if "mr" in lang_code.lower() else "en"
        utterance_key = f"utterances_{lang_key}"
        keyword_key = f"keywords_{lang_key}"

        for route in self.routes_data:
            # 1. Exact or partial check on path or ID
            if query == route["path"] or query == route["route_id"]:
                return {"route": route, "score": 1.0, "match_type": "exact_id"}

            # 2. Check trained utterances
            for ut in route.get(utterance_key, []):
                score_ratio = fuzz.ratio(query, ut.lower()) / 100.0
                score_partial = fuzz.partial_ratio(query, ut.lower()) / 100.0
                score_token = fuzz.token_set_ratio(query, ut.lower()) / 100.0
                max_ut_score = max(score_ratio, score_partial * 0.95, score_token)

                if max_ut_score > highest_score:
                    highest_score = max_ut_score
                    best_match = route

            # 3. Check keywords
            for kw in route.get(keyword_key, []):
                if kw.lower() in query:
                    kw_score = 0.88 + (len(kw) / max(len(query), 1)) * 0.1
                    if kw_score > highest_score:
                        highest_score = min(kw_score, 0.98)
                        best_match = route

        if best_match and highest_score >= 0.60:
            return {"route": best_match, "score": highest_score, "match_type": "fuzzy_trained"}

        return None

    async def _classify_with_llm(self, query: str, lang_code: str) -> Optional[Dict[str, Any]]:
        """
        Uses cloud LLM API (Groq / Krutrim / OpenAI) if keys are provided to classify intent.
        """
        routes_summary = [
            {"id": r["route_id"], "path": r["path"], "name": r.get(f"name_{lang_code}", r["name_en"])}
            for r in self.routes_data
        ]

        prompt = f"""You are an AI navigation assistant for a web application.
Language of user input: {lang_code} (English or Marathi).
User Command: "{query}"

Available routes:
{json.dumps(routes_summary, ensure_ascii=False)}

Identify if the user wants to navigate to one of the above routes or is asking a general question.
Respond ONLY with JSON format:
{{
  "intent": "NAVIGATE" | "QUESTION" | "UNKNOWN",
  "target_route_id": "<route_id>" or null,
  "explanation": "brief reason",
  "reply_text": "polite response in the same language ({lang_code})"
}}
"""
        # If Groq API key is present
        if settings.GROQ_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.1,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        return json.loads(content)
            except Exception as e:
                logger.warning(f"Groq LLM intent classification failed: {e}")

        return None

    async def process_voice_command(self, query: str, lang_code: str = "en") -> Dict[str, Any]:
        """
        Main pipeline:
        1. Checks for empty input
        2. Detects if it's a Problem Solving / FAQ question
        3. Runs Trainable Fuzzy/Keyword Matcher
        4. Fallbacks to Cloud LLM API if available
        5. Formats multilingual response & TTS payload
        """
        clean_query = query.strip()
        lang_cfg = get_language_config(lang_code)

        if not clean_query:
            return {
                "intent": "UNKNOWN",
                "action": "NONE",
                "transcript": "",
                "language": lang_cfg.code,
                "response_text": lang_cfg.default_unknown_msg,
                "target_path": None,
                "confidence": 0.0
            }

        # Step 1: Check if this is a problem solving / informational query
        if problem_solver.is_problem_query(clean_query, lang_cfg.code):
            return await problem_solver.solve_or_explain(clean_query, lang_cfg.code)

        # Step 2: Trainable Fuzzy / Utterance Match
        fuzzy_res = self._fuzzy_match(clean_query, lang_cfg.code)
        if fuzzy_res:
            route = fuzzy_res["route"]
            score = fuzzy_res["score"]
            page_name = route.get(f"name_{lang_cfg.code}", route["name_en"])
            ack_template = random.choice(lang_cfg.nav_ack_templates)
            response_text = ack_template.format(page_name=page_name)

            return {
                "intent": "NAVIGATE",
                "action": "NAVIGATE",
                "transcript": clean_query,
                "language": lang_cfg.code,
                "route_id": route["route_id"],
                "target_path": route["path"],
                "target_name": page_name,
                "confidence": round(score, 3),
                "match_type": fuzzy_res["match_type"],
                "response_text": response_text
            }

        # Step 3: Cloud LLM fallback if configured
        llm_res = await self._classify_with_llm(clean_query, lang_cfg.code)
        if llm_res and llm_res.get("intent") == "NAVIGATE" and llm_res.get("target_route_id"):
            route_id = llm_res["target_route_id"]
            matched_route = next((r for r in self.routes_data if r["route_id"] == route_id), None)
            if matched_route:
                page_name = matched_route.get(f"name_{lang_cfg.code}", matched_route["name_en"])
                return {
                    "intent": "NAVIGATE",
                    "action": "NAVIGATE",
                    "transcript": clean_query,
                    "language": lang_cfg.code,
                    "route_id": matched_route["route_id"],
                    "target_path": matched_route["path"],
                    "target_name": page_name,
                    "confidence": 0.85,
                    "match_type": "cloud_llm",
                    "response_text": llm_res.get("reply_text") or f"Navigating to {page_name}."
                }

        # Step 4: Unknown / No matching route
        return {
            "intent": "UNKNOWN",
            "action": "NONE",
            "transcript": clean_query,
            "language": lang_cfg.code,
            "target_path": None,
            "confidence": 0.0,
            "response_text": lang_cfg.default_unknown_msg
        }

intent_engine = NavigationIntentEngine()
