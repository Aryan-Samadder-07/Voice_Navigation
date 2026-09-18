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

# Persistent async HTTP client with connection pooling for sub-second latency
http_client = httpx.AsyncClient(timeout=10.0)

class NavigationIntentEngine:
    """
    Optimized Multilingual Intent Classification & Voice Navigation Engine.
    Powered by SiliconFlow Qwen 2.5 7B with Groq fallback and local fuzzy cache.
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
        Calculates fast fuzzy match scores across keywords and trained utterances.
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
                    kw_score = 0.90 + (len(kw) / max(len(query), 1)) * 0.1
                    if kw_score > highest_score:
                        highest_score = min(kw_score, 0.99)
                        best_match = route

        if best_match and highest_score >= 0.85:
            return {"route": best_match, "score": highest_score, "match_type": "fast_cache"}

        return None

    async def _classify_with_qwen_or_groq(self, query: str, lang_code: str) -> Optional[Dict[str, Any]]:
        """
        Uses SiliconFlow Qwen 2.5 7B (or Groq Llama 3.3) for natural language reasoning & intent extraction.
        """
        routes_summary = [
            {"id": r["route_id"], "path": r["path"], "name": r.get(f"name_{lang_code}", r["name_en"]), "keywords": r.get(f"keywords_{lang_code}", [])}
            for r in self.routes_data
        ]

        system_prompt = f"""You are a low-latency Multilingual Navigation & Assistance AI.
Language: {lang_code} (English or Marathi / मराठी).
Task: Given a user voice command, determine whether the user wants to navigate to one of the application routes or is asking an informational/help question.

Available Routes:
{json.dumps(routes_summary, ensure_ascii=False)}

Rules:
1. If the user wants to navigate, return intent="NAVIGATE" and target_route_id=<route_id>.
2. If asking for help/question/problem, return intent="QUESTION" with a concise reply in the same language.
3. Respond ONLY with valid JSON with these keys:
{{"intent": "NAVIGATE" | "QUESTION" | "UNKNOWN", "target_route_id": "<id or null>", "reply_text": "<concise spoken reply in {lang_code}>", "confidence": <float between 0.0 and 1.0>}}
"""

        # 1. Try SiliconFlow Qwen 2.5 7B if key is available
        if settings.SILICONFLOW_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.SILICONFLOW_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 150,
                    "response_format": {"type": "json_object"}
                }
                resp = await http_client.post("https://api.siliconflow.cn/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    raw_content = resp.json()["choices"][0]["message"]["content"]
                    return json.loads(raw_content)
            except Exception as e:
                logger.warning(f"SiliconFlow Qwen 2.5 API error: {e}")

        # 2. Try Groq LLM API if key is available
        if settings.GROQ_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.GROQ_LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 150,
                    "response_format": {"type": "json_object"}
                }
                resp = await http_client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    raw_content = resp.json()["choices"][0]["message"]["content"]
                    return json.loads(raw_content)
            except Exception as e:
                logger.warning(f"Groq LLM API error: {e}")

        return None

    async def process_voice_command(self, query: str, lang_code: str = "en") -> Dict[str, Any]:
        """
        Optimized Low-Latency Processing Pipeline:
        1. Fast cache check
        2. Qwen 2.5 / Groq LLM Intent & Reasoning extraction
        3. Local Fuzzy Fallback
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

        # Step 1: Check fast exact/trained cache for instant sub-millisecond response
        fast_res = self._fuzzy_match(clean_query, lang_cfg.code)
        if fast_res and fast_res["score"] >= 0.92:
            route = fast_res["route"]
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
                "confidence": round(fast_res["score"], 3),
                "match_type": fast_res["match_type"],
                "engine": "fast_cache",
                "response_text": response_text
            }

        # Step 2: SiliconFlow Qwen 2.5 7B / Groq LLM Classification
        llm_res = await self._classify_with_qwen_or_groq(clean_query, lang_cfg.code)
        if llm_res:
            llm_intent = llm_res.get("intent", "").upper()
            target_route_id = llm_res.get("target_route_id")
            
            if llm_intent == "NAVIGATE" and target_route_id:
                matched_route = next((r for r in self.routes_data if r["route_id"] == target_route_id), None)
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
                        "confidence": float(llm_res.get("confidence", 0.95)),
                        "match_type": "qwen2.5_llm",
                        "engine": "SiliconFlow_Qwen2.5-7B" if settings.SILICONFLOW_API_KEY else "Groq_Llama3.3",
                        "response_text": llm_res.get("reply_text") or f"Navigating to {page_name}."
                    }
            
            elif llm_intent == "QUESTION":
                return {
                    "intent": "PROBLEM_SOLVING",
                    "action": "NONE",
                    "transcript": clean_query,
                    "language": lang_cfg.code,
                    "status": "answered_by_qwen",
                    "engine": "SiliconFlow_Qwen2.5-7B",
                    "confidence": float(llm_res.get("confidence", 0.95)),
                    "response_text": llm_res.get("reply_text", "")
                }

        # Step 3: Check Problem Solver heuristic if LLM key wasn't active
        if problem_solver.is_problem_query(clean_query, lang_cfg.code):
            return await problem_solver.solve_or_explain(clean_query, lang_cfg.code)

        # Step 4: Fuzzy Fallback (lower threshold 0.60)
        if fast_res and fast_res["score"] >= 0.60:
            route = fast_res["route"]
            page_name = route.get(f"name_{lang_cfg.code}", route["name_en"])
            ack_template = random.choice(lang_cfg.nav_ack_templates)
            return {
                "intent": "NAVIGATE",
                "action": "NAVIGATE",
                "transcript": clean_query,
                "language": lang_cfg.code,
                "route_id": route["route_id"],
                "target_path": route["path"],
                "target_name": page_name,
                "confidence": round(fast_res["score"], 3),
                "match_type": "fuzzy_fallback",
                "response_text": ack_template.format(page_name=page_name)
            }

        # Step 5: Unknown
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
