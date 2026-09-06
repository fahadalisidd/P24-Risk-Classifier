"""AI Risk Advisor powered by xAI Grok, Local Ollama, and Embedded Semantic Analyzer.

Supports xAI Grok (grok-2-latest, grok-beta), Local Ollama, and embedded offline Semantic NLP.
"""
import os
import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.domain.enums import RiskCategory, Scope, Reversibility, Persistence
from app.schemas.ai import AIRiskAssessment
from app.schemas.operation import OperationPayload

logger = logging.getLogger(__name__)


class AIRiskAdvisor:
    """AI-powered risk assistant supporting Grok (xAI), Ollama, and local Semantic NLP."""

    def __init__(
        self,
        grok_api_key: Optional[str] = None,
        grok_model: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        use_ollama: Optional[bool] = None,
    ):
        self.grok_api_key = grok_api_key or settings.GROK_API_KEY or settings.XAI_API_KEY or os.environ.get("GROK_API_KEY") or os.environ.get("XAI_API_KEY")
        self.grok_model = grok_model or settings.GROK_MODEL
        self.grok_base_url = settings.GROK_BASE_URL

        self.ollama_base_url = ollama_base_url or settings.OLLAMA_BASE_URL
        self.ollama_model = ollama_model or settings.OLLAMA_MODEL
        self.use_ollama = use_ollama if use_ollama is not None else settings.USE_OLLAMA

    def analyze(self, operation: OperationPayload, rule_category: Optional[int] = None) -> AIRiskAssessment:
        """Perform AI risk assessment and semantic justification analysis."""
        # 1. Option A: Use Grok API if key is provided
        if self.grok_api_key:
            try:
                assessment = self._call_grok_api(operation, rule_category)
                if assessment:
                    return assessment
            except Exception as e:
                logger.warning(f"Grok API call failed ({e}). Falling back to local Ollama / Semantic Analyzer.")

        # 2. Option B: Use Local Ollama instance if available
        if self.use_ollama and self.ollama_base_url:
            try:
                assessment = self._call_ollama_api(operation, rule_category)
                if assessment:
                    return assessment
            except Exception as e:
                logger.info(f"Ollama local instance not reachable ({e}). Using embedded Semantic Model.")

        # 3. Option C: Embedded Local Semantic Risk & NLP Model (100% offline, zero-dependency)
        return self._evaluate_semantic_engine(operation, rule_category)

    def _call_grok_api(self, operation: OperationPayload, rule_category: Optional[int]) -> Optional[AIRiskAssessment]:
        """Call xAI Grok API endpoint."""
        url = f"{self.grok_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.grok_api_key}",
            "Content-Type": "application/json"
        }
        prompt = self._build_prompt(operation, rule_category)
        
        payload = {
            "model": self.grok_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert Production Reliability and Cybersecurity Risk Auditor. Always return your response strictly as valid, raw JSON without markdown formatting or conversational filler."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["choices"][0]["message"]["content"]
                
                # Strip potential markdown code block markers
                clean_json = re.sub(r"^```json\s*", "", raw_text.strip())
                clean_json = re.sub(r"\s*```$", "", clean_json.strip())
                parsed = json.loads(clean_json)

                return AIRiskAssessment(
                    aiModelUsed=f"xAI Grok ({self.grok_model})",
                    aiConfidenceScore=float(parsed.get("aiConfidenceScore", 0.98)),
                    executiveSummary=parsed.get(
                        "executiveSummary",
                        f"xAI Grok assessed {operation.operationType} operation as Category {rule_category or 3}."
                    ),
                    justificationQuality=str(parsed.get("justificationQuality", "HIGH")).upper(),
                    rollbackPlanQuality=str(parsed.get("rollbackPlanQuality", "ADEQUATE")).upper(),
                    semanticRedFlags=parsed.get("semanticRedFlags", []),
                    suggestedMitigations=parsed.get("suggestedMitigations", []),
                    recommendedCategory=int(parsed.get("recommendedCategory", rule_category or 3)),
                )
            else:
                logger.warning(f"Grok API error: {resp.status_code} - {resp.text}")
        return None

    def _call_ollama_api(self, operation: OperationPayload, rule_category: Optional[int]) -> Optional[AIRiskAssessment]:
        """Call Local Ollama LLM endpoint (POST /api/generate)."""
        url = f"{self.ollama_base_url.rstrip('/')}/api/generate"
        prompt = self._build_prompt(operation, rule_category)
        
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            }
        }

        with httpx.Client(timeout=6.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                raw_response = data.get("response", "{}")
                parsed = json.loads(raw_response)

                return AIRiskAssessment(
                    aiModelUsed=f"Ollama ({self.ollama_model})",
                    aiConfidenceScore=float(parsed.get("aiConfidenceScore", 0.95)),
                    executiveSummary=parsed.get(
                        "executiveSummary",
                        f"Local Ollama ({self.ollama_model}) assessed {operation.operationType} operation as Category {rule_category or 3}."
                    ),
                    justificationQuality=str(parsed.get("justificationQuality", "HIGH")).upper(),
                    rollbackPlanQuality=str(parsed.get("rollbackPlanQuality", "ADEQUATE")).upper(),
                    semanticRedFlags=parsed.get("semanticRedFlags", []),
                    suggestedMitigations=parsed.get("suggestedMitigations", []),
                    recommendedCategory=int(parsed.get("recommendedCategory", rule_category or 3)),
                )
        return None

    def _build_prompt(self, operation: OperationPayload, rule_category: Optional[int]) -> str:
        return f"""Analyze the following technical operation and return a strictly valid JSON response.

Operation:
- ID: {operation.operationId}
- Type: {operation.operationType}
- Scope: {operation.scope.value}
- Reversibility: {operation.reversibility.value}
- Persistence: {operation.persistence.value}
- Payload Details: {json.dumps(operation.payload)}
- Rule Engine Base Category: {rule_category or 'N/A'}

Respond strictly in JSON format with these exact keys:
{{
  "aiConfidenceScore": 0.98,
  "executiveSummary": "Concise plain English operational risk summary",
  "justificationQuality": "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT",
  "rollbackPlanQuality": "STRONG" | "ADEQUATE" | "WEAK" | "MISSING",
  "semanticRedFlags": ["list of detected safety concerns"],
  "suggestedMitigations": ["actionable pre-execution advice"],
  "recommendedCategory": 1 | 2 | 3 | 4
}}
"""

    def _evaluate_semantic_engine(self, operation: OperationPayload, rule_category: Optional[int]) -> AIRiskAssessment:
        """Embedded Local Semantic NLP Model based on lexical analysis and safety patterns."""
        red_flags: List[str] = []
        mitigations: List[str] = []

        payload = operation.payload or {}
        justification = str(payload.get("justification") or "").strip().lower()
        rollback = str(payload.get("rollbackPlan") or "").strip().lower()
        env = str(payload.get("environment") or "").upper()

        # 1. Analyze Justification Quality
        if not justification:
            just_quality = "INSUFFICIENT"
            red_flags.append("No justification was provided for this operation.")
        elif len(justification) < 10 or justification in ("test", "asdf", "fix", "update", "temp"):
            just_quality = "LOW"
            red_flags.append("Justification is too brief and lacks specific context.")
        elif any(w in justification for w in ["emergency", "hotfix", "critical", "incident", "bypass"]):
            just_quality = "HIGH"
            mitigations.append("Ensure post-incident review ticket is linked to emergency justification.")
        else:
            just_quality = "HIGH" if len(justification) > 25 else "MEDIUM"

        # 2. Analyze Rollback Plan Quality
        if not rollback:
            rollback_quality = "MISSING"
            if operation.reversibility == Reversibility.IRREVERSIBLE or operation.scope == Scope.GLOBAL:
                red_flags.append("Missing rollback plan for irreversible/global operation.")
        elif any(w in rollback for w in ["snapshot", "backup", "restore", "point-in-time", "revert commit"]):
            rollback_quality = "STRONG"
            mitigations.append("Validate that snapshot/backup restore has been verified prior to execution.")
        elif any(w in rollback for w in ["manual", "recreate", "retry", "none", "n/a"]):
            rollback_quality = "WEAK"
            red_flags.append("Rollback strategy relies on manual reconstruction rather than automated snapshots.")
        else:
            rollback_quality = "ADEQUATE"

        # 3. Environment & Scope Red Flags
        if env == "PRODUCTION":
            if operation.reversibility == Reversibility.IRREVERSIBLE:
                red_flags.append("Irreversible modifications in PRODUCTION carry immediate blast radius risk.")
            if operation.persistence == Persistence.PERMANENT:
                mitigations.append("Execute during scheduled off-peak maintenance window with active telemetry monitoring.")

        # 4. Determine AI Recommended Category & Summary
        rec_category = rule_category if rule_category else (
            4 if (operation.scope == Scope.GLOBAL and operation.reversibility == Reversibility.IRREVERSIBLE) else 2
        )

        summary = (
            f"AI Risk Advisor: {operation.operationType} operation with {operation.scope.value} scope "
            f"and {operation.reversibility.value} reversibility ({'in ' + env if env else 'general environment'}). "
            f"Safety obligations evaluated: Justification ({just_quality}), Rollback ({rollback_quality})."
        )

        return AIRiskAssessment(
            aiModelUsed=f"AI Risk Advisor (Grok/Ollama-Ready Semantic NLP Engine)",
            aiConfidenceScore=0.96 if len(red_flags) == 0 else 0.88,
            executiveSummary=summary,
            justificationQuality=just_quality,
            rollbackPlanQuality=rollback_quality,
            semanticRedFlags=red_flags,
            suggestedMitigations=mitigations if mitigations else ["Follow standard staging-to-production deployment checklist."],
            recommendedCategory=rec_category,
        )
