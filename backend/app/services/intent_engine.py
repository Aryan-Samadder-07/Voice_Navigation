import json
import os
import random
import logging
import time
import httpx
from typing import Dict, Any, List, Optional
from rapidfuzz import fuzz
from app.core.config import settings
from app.core.languages import get_language_config, SUPPORTED_LANGUAGES
from app.services.problem_solver import problem_solver
from app.services.rate_limiter import rate_tracker

logger = logging.getLogger(__name__)

INTENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "training_intents.json")

class NavigationIntentEngine:
    """
    Real-world Multilingual Intent & Navigation Engine.
    Handles noisy STT acoustic misrecognitions, phonetic transliterations, and live Groq AI reasoning.
    """

    def __init__(self):
        self.routes_data: List[Dict[str, Any]] = []
        self.load_training_data()

    def load_training_data(self) -> None:
        """Loads the registered routes catalog."""
        try:
            if os.path.exists(INTENTS_FILE_PATH):
                with open(INTENTS_FILE_PATH, "r", encoding="utf-8") as f:
                    self.routes_data = json.load(f)
            else:
                self.routes_data = []
        except Exception as e:
            logger.error(f"Failed to load routes catalog: {e}")
            self.routes_data = []

    def save_training_data(self) -> bool:
        """Persists trained phrases to JSON catalog."""
        try:
            with open(INTENTS_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.routes_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to persist training catalog: {e}")
            return False

    def get_all_routes(self) -> List[Dict[str, Any]]:
        """Returns all registered application routes."""
        return self.routes_data

    def train_utterance(self, route_id: str, utterance: str, lang_code: str = "en") -> Dict[str, Any]:
        """
        Dynamically registers custom voice command in real time.
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
            "message": f"Utterance '{cleaned}' already registered for route '{route_id}'.",
            "route_id": route_id
        }

    def find_fuzzy_phonetic_match(self, query: str, lang_code: str = "en") -> Optional[Dict[str, Any]]:
        """
        Phonetic & fuzzy acoustic matcher that recovers words misheard due to microphone noise or accent.
        E.g. "there's wood" -> Dashboard, "analytix" / "analysis" -> Analytics, "pro file" -> Profile.
        """
        q = query.lower().strip()
        best_match = None
        best_score = 0.0

        for route in self.routes_data:
            route_id = route["route_id"]
            keywords = route.get("keywords_en", []) + route.get("keywords_mr", [])
            utterances = route.get("utterances_en", []) + route.get("utterances_mr", [])
            all_candidates = keywords + utterances + [route.get("name_en", "").lower(), route.get("name_mr", "").lower()]

            for cand in all_candidates:
                cand_lower = cand.lower()
                # 1. Exact or substring match
                if q == cand_lower or cand_lower in q:
                    return {"route": route, "score": 98.0, "matched_candidate": cand}

                # 2. Token Sort / Token Set Ratio
                score_sort = fuzz.token_sort_ratio(q, cand_lower)
                score_set = fuzz.token_set_ratio(q, cand_lower)
                score_partial = fuzz.partial_ratio(q, cand_lower)
                max_cand_score = max(score_sort, score_set, score_partial)

                if max_cand_score > best_score:
                    best_score = max_cand_score
                    best_match = {"route": route, "score": max_cand_score, "matched_candidate": cand}

        if best_match and best_score >= 70.0:
            return best_match

        return None

    async def _classify_with_groq_ai(self, query: str, lang_code: str) -> Optional[Dict[str, Any]]:
        """
        Pure AI intent extraction through live Groq inference with robust phonetic noise handling.
        """
        routes_summary = [
            {
                "id": r["route_id"],
                "path": r["path"],
                "name": r.get(f"name_{lang_code}", r["name_en"]),
                "description": r.get("description", ""),
                "keywords": r.get(f"keywords_{lang_code}", []) + r.get("keywords_en", [])
            }
            for r in self.routes_data
        ]

        system_prompt = f"""You are an intelligent Multilingual Voice Navigation AI Assistant for a web application.
Language of user input: {lang_code} (English or Marathi / मराठी).

Application Routes Catalog:
{json.dumps(routes_summary, ensure_ascii=False)}

CRITICAL ACOUSTIC & PHONETIC ERROR TOLERANCE:
Speech-to-Text (STT) models often mishear words due to microphone noise, room acoustics, or accents. You MUST match sound-alikes and misrecognitions to the intended route:
- "there's wood", "there is wood", "dash wood", "dash board", "deshboard", "tash board", "dish board", "home", "main", "start", "डॅशबोर्ड", "मुख्य पान" -> Route: home (/)
- "analysis", "analyst", "analytix", "allistics", "metrics", "charts", "stats", "reports", "एनालिसिस", "ॲनालिसिस", "आकडेवारी" -> Route: analytics (/analytics)
- "pro file", "pro-file", "pro fill", "brofile", "profile", "account", "details", "प्रोफाइल", "माझे खाते", "माझी माहिती" -> Route: profile (/profile)
- "set tings", "satting", "sitting", "set ins", "options", "config", "सेटिंग्ज", "मांडणी", "पर्याय" -> Route: settings (/settings)
- "diagnose", "diagnostic", "die agnostics", "day agnostic", "dog nostics", "health", "system check", "निदान", "चाचणी" -> Route: diagnostics (/diagnostics)
- "halp", "health support", "helpp", "support", "faq", "guide", "मदत", "मार्गदर्शक" -> Route: help (/help)

Instructions:
1. If the user intends to navigate (even if phonetically mispronounced or noisy), set intent="NAVIGATE" and target_route_id=<id>.
2. If asking an informational question/problem, set intent="QUESTION".
3. Provide a polite spoken reply_text in the exact language ({lang_code}). Plain speakable text only.
4. Output ONLY valid JSON:
{{"intent": "NAVIGATE" | "QUESTION" | "UNKNOWN", "target_route_id": "<id or null>", "reply_text": "<spoken reply>", "confidence": 0.98}}
"""

        if not settings.GROQ_API_KEY:
            return None

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": settings.GROQ_LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"User speech/text command: {query}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 150,
                    "response_format": {"type": "json_object"}
                }
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    raw_content = resp.json()["choices"][0]["message"]["content"]
                    return json.loads(raw_content)
                elif resp.status_code == 429:
                    logger.warning("Groq AI Rate limit reached")
                    return {"rate_limited": True}
        except Exception as e:
            logger.error(f"Live Groq AI API error: {e}")

        return None

    async def process_voice_command(self, query: str, lang_code: str = "en") -> Dict[str, Any]:
        """
        Processes voice command with live latency timing, rate limit checks, AI reasoning, and phonetic fault recovery.
        """
        start_time = time.perf_counter()
        clean_query = query.strip()
        lang_cfg = get_language_config(lang_code)

        # 1. Check Rate Limits
        limit_check = rate_tracker.check_rate_limit()
        if limit_check.get("is_limited"):
            return {
                "intent": "RATE_LIMITED",
                "action": "NONE",
                "transcript": clean_query,
                "language": lang_cfg.code,
                "response_text": "Rate limit threshold reached. Please wait a few seconds before giving another voice command." if lang_code != "mr" else "कमाल विनंती मर्यादा गाठली आहे. कृपया काही सेकंद थांबा.",
                "target_path": None,
                "confidence": 0.0,
                "telemetry": rate_tracker.get_telemetry()
            }

        if not clean_query:
            return {
                "intent": "UNKNOWN",
                "action": "NONE",
                "transcript": "",
                "language": lang_cfg.code,
                "response_text": lang_cfg.default_unknown_msg,
                "target_path": None,
                "confidence": 0.0,
                "telemetry": rate_tracker.get_telemetry()
            }

        # 2. Check if Question / Problem-solving query
        if problem_solver.is_problem_query(clean_query, lang_cfg.code):
            prob_res = await problem_solver.solve_or_explain(clean_query, lang_cfg.code)
            latency_ms = (time.perf_counter() - start_time) * 1000
            rate_tracker.record_request(latency_ms)
            prob_res["latency_ms"] = round(latency_ms, 2)
            prob_res["telemetry"] = rate_tracker.get_telemetry()
            return prob_res

        # 3. Live AI Intent Processing via Groq
        ai_res = await self._classify_with_groq_ai(clean_query, lang_cfg.code)
        latency_ms = (time.perf_counter() - start_time) * 1000
        rate_tracker.record_request(latency_ms)

        if ai_res and not ai_res.get("rate_limited"):
            ai_intent = ai_res.get("intent", "").upper()
            target_route_id = ai_res.get("target_route_id")
            
            if ai_intent == "NAVIGATE" and target_route_id:
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
                        "confidence": float(ai_res.get("confidence", 0.98)),
                        "match_type": "live_groq_ai",
                        "model": settings.GROQ_LLM_MODEL,
                        "latency_ms": round(latency_ms, 2),
                        "response_text": ai_res.get("reply_text") or f"Navigating to {page_name}.",
                        "telemetry": rate_tracker.get_telemetry()
                    }
            
            elif ai_intent == "QUESTION":
                return {
                    "intent": "PROBLEM_SOLVING",
                    "action": "NONE",
                    "transcript": clean_query,
                    "language": lang_cfg.code,
                    "status": "answered_by_ai",
                    "confidence": float(ai_res.get("confidence", 0.98)),
                    "latency_ms": round(latency_ms, 2),
                    "response_text": ai_res.get("reply_text", ""),
                    "telemetry": rate_tracker.get_telemetry()
                }

        # 4. Phonetic & Acoustic Fuzzy Recovery (Catches noisy STT like "there's wood", "analysis", "pro file", etc.)
        fuzzy_match = self.find_fuzzy_phonetic_match(clean_query, lang_cfg.code)
        if fuzzy_match:
            route = fuzzy_match["route"]
            page_name = route.get(f"name_{lang_cfg.code}", route["name_en"])
            reply = f"Navigating to {page_name}." if lang_cfg.code != "mr" else f"{page_name} पृष्ठावर नेत आहे."
            return {
                "intent": "NAVIGATE",
                "action": "NAVIGATE",
                "transcript": clean_query,
                "language": lang_cfg.code,
                "route_id": route["route_id"],
                "target_path": route["path"],
                "target_name": page_name,
                "confidence": round(fuzzy_match["score"] / 100.0, 2),
                "match_type": "phonetic_fuzzy_recovery",
                "model": "phonetic_noise_corrector",
                "latency_ms": round(latency_ms, 2),
                "response_text": reply,
                "telemetry": rate_tracker.get_telemetry()
            }

        # 5. Unknown Query Result
        return {
            "intent": "UNKNOWN",
            "action": "NONE",
            "transcript": clean_query,
            "language": lang_cfg.code,
            "target_path": None,
            "confidence": 0.0,
            "latency_ms": round(latency_ms, 2),
            "response_text": lang_cfg.default_unknown_msg,
            "telemetry": rate_tracker.get_telemetry()
        }

intent_engine = NavigationIntentEngine()

