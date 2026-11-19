"""
Unified Request Enforcement Pipeline.
Executes the 6-step control-panel architecture (Slide 8):
1. Authenticate (Module 1)
2. Build Filters (Module 2)
3. Retrieve (Module 2)
4. Render Prompt (Module 3)
5. Check Output (Module 3 - Algorithm 1)
6. Cryptographic Audit Log (Module 3 - Algorithm 2)
"""

import time
import re
from typing import Dict, Any, Optional
from src.module1_identity_policy.tokens import verify_token, AuthenticationError
from src.module1_identity_policy.policy_engine import PolicyEngine, PolicyViolationError
from src.module2_enforced_retrieval.database import HospitalRepository
from src.module2_enforced_retrieval.filter_builder import FilterBuilder, FilterBuilderError
from src.module2_enforced_retrieval.vector_store import PreFilteredVectorStore
from src.module2_enforced_retrieval.field_masker import FieldMasker
from src.module3_generation_audit.prompt_renderer import PromptRenderer
from src.module3_generation_audit.llm_client import LLMClient
from src.module3_generation_audit.output_guard import OutputGuard
from src.module3_generation_audit.audit_logger import HashChainedAuditLogger


class RequestEnforcementPipeline:
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.repository = HospitalRepository()
        self.filter_builder = FilterBuilder(self.policy_engine, self.repository)
        self.vector_store = PreFilteredVectorStore()
        self.prompt_renderer = PromptRenderer()
        self.llm_client = LLMClient()
        self.output_guard = OutputGuard()
        self.audit_logger = HashChainedAuditLogger()

    def process_query(self, query: str, token: Optional[str]) -> Dict[str, Any]:
        """
        Executes the 6-step request enforcement pipeline.
        Returns the finalized answer and full telemetry for each step.
        """
        start_time = time.time()
        pipeline_telemetry = {
            "query": query,
            "step1_auth": {},
            "step2_filters": {},
            "step3_retrieval": {},
            "step4_prompt": {},
            "step5_guard": {},
            "step6_audit": {},
            "status": "PROCESSING",
            "execution_ms": 0
        }

        # --- STEP 1: AUTHENTICATE ---
        try:
            claims = verify_token(token)
            role = claims.get("role")
            user_id = claims.get("user_id")
            level = claims.get("level")

            # Check separation of duties: Admin refused data queries
            self.policy_engine.validate_clinical_query_authorization(claims)

            pipeline_telemetry["step1_auth"] = {
                "success": True,
                "user_id": user_id,
                "role": role,
                "level": level,
                "department": claims.get("department"),
                "ward": claims.get("assigned_ward"),
                "is_break_glass": claims.get("is_break_glass", False)
            }
        except (AuthenticationError, PolicyViolationError) as e:
            error_msg = str(e)
            pipeline_telemetry["step1_auth"] = {"success": False, "error": error_msg}
            pipeline_telemetry["status"] = "REFUSED_AT_AUTH"

            # Log blocked query in audit chain
            audit_rec = self.audit_logger.log_event(
                user_id="UNAUTHENTICATED" if "token" in error_msg.lower() else "ADMIN_SYS",
                role="UNKNOWN" if "token" in error_msg.lower() else "System Administrator",
                policy_version=self.policy_engine.get_policy_version(),
                template_version=self.prompt_renderer.template_version,
                filters_applied={"reason": "Step 1 Authentication / Authorization failure"},
                document_ids=[],
                outcome="BLOCKED",
                query_text=query,
                extra_telemetry={"step_failed": 1, "error": error_msg}
            )
            pipeline_telemetry["step6_audit"] = audit_rec
            pipeline_telemetry["execution_ms"] = round((time.time() - start_time) * 1000, 2)
            return {
                "answer": f"REFUSAL: {error_msg}",
                "outcome": "BLOCKED",
                "telemetry": pipeline_telemetry
            }

        # --- STEP 2: BUILD FILTERS ---
        try:
            filters = self.filter_builder.build_filters(claims)
            pipeline_telemetry["step2_filters"] = {
                "success": True,
                "allowed_categories": filters["allowed_categories"],
                "allowed_patient_ids": filters["allowed_patient_ids"],
                "department_scope": filters["department"],
                "ward_scope": filters["ward"],
                "scope_desc": filters["scope_desc"],
                "field_masks": filters["field_masks"]
            }
        except (FilterBuilderError, PolicyViolationError) as e:
            error_msg = str(e)
            pipeline_telemetry["step2_filters"] = {"success": False, "error": error_msg}
            pipeline_telemetry["status"] = "REFUSED_AT_FILTER_BUILD"

            audit_rec = self.audit_logger.log_event(
                user_id=user_id,
                role=role,
                policy_version=self.policy_engine.get_policy_version(),
                template_version=self.prompt_renderer.template_version,
                filters_applied={"reason": "Step 2 Filter Build failure"},
                document_ids=[],
                outcome="BLOCKED",
                query_text=query,
                extra_telemetry={"step_failed": 2, "error": error_msg}
            )
            pipeline_telemetry["step6_audit"] = audit_rec
            pipeline_telemetry["execution_ms"] = round((time.time() - start_time) * 1000, 2)
            return {
                "answer": f"REFUSAL: {error_msg}",
                "outcome": "BLOCKED",
                "telemetry": pipeline_telemetry
            }

        # --- STEP 3: ENFORCED RETRIEVAL ---
        # Detect if query targets specific patient IDs (e.g., "P-1042", "P-3307")
        direct_mentions = re.findall(r"P-\d{4}", query.upper())
        target_patients = []
        retrieved_docs = []
        is_target_out_of_scope = False

        if direct_mentions:
            for pid in direct_mentions:
                # Check if patient ID is within allowed scope
                if filters["allowed_patient_ids"] is not None and pid not in filters["allowed_patient_ids"]:
                    is_target_out_of_scope = True
                    continue

                pt_rec = self.repository.get_patient_by_id(pid)
                if not pt_rec:
                    continue

                # Verify department constraint
                if filters["department"] and pt_rec["department"] != filters["department"]:
                    is_target_out_of_scope = True
                    continue

                # Verify ward constraint
                if filters["ward"] and pt_rec["ward"] != filters["ward"]:
                    is_target_out_of_scope = True
                    continue

                target_patients.append(pid)

            if target_patients:
                retrieved_docs = self.vector_store.search(
                    query=query,
                    allowed_patient_ids=target_patients,
                    allowed_categories=filters["allowed_categories"],
                    department=filters["department"],
                    ward=filters["ward"],
                    top_k=3
                )
        else:
            # Broad/general clinical query
            retrieved_docs = self.vector_store.search(
                query=query,
                allowed_patient_ids=filters["allowed_patient_ids"],
                allowed_categories=filters["allowed_categories"],
                department=filters["department"],
                ward=filters["ward"],
                top_k=3
            )
            target_patients = list(dict.fromkeys([d["patient_id"] for d in retrieved_docs]))

        # Format context and apply field-level masking
        raw_context_parts = []
        doc_ids = [d["doc_id"] for d in retrieved_docs]
        role_pol = self.policy_engine.get_role_policy(role)

        for pid in target_patients:
            pt_record = self.repository.get_patient_by_id(pid)
            if pt_record:
                masked_pt = FieldMasker.mask_patient_record(pt_record, filters["field_masks"], role)
                pt_context = FieldMasker.format_patient_context(masked_pt, role_pol, role)
                raw_context_parts.append(pt_context)
                doc_ids.append(f"PATIENT_RECORD_{pid}")

        for d in retrieved_docs:
            raw_context_parts.append(f"[Document {d['doc_id']} | Cat: {d['category']}]: {d['text']}")

        final_context = "\n\n".join(raw_context_parts) if raw_context_parts else ""

        pipeline_telemetry["step3_retrieval"] = {
            "documents_found": len(retrieved_docs),
            "patients_in_scope": target_patients,
            "document_ids": doc_ids,
            "context_characters": len(final_context),
            "context_preview": final_context[:300] + "..." if len(final_context) > 300 else final_context
        }

        # --- STEP 4: RENDER SYSTEM PROMPT ---
        rendered_prompt = self.prompt_renderer.render(
            role_name=role,
            role_level=level,
            allowed_categories=filters["allowed_categories"],
            patient_scope=filters["scope_desc"],
            retrieved_context=final_context,
            user_query=query
        )
        pipeline_telemetry["step4_prompt"] = {
            "template_version": self.prompt_renderer.template_version,
            "prompt_length": len(rendered_prompt),
            "role_injected": role,
            "untrusted_boundary_enforced": True
        }

        # Call LLM client
        raw_answer = self.llm_client.generate(rendered_prompt, final_context, query, role)

        # --- STEP 5: OUTPUT CHECKS (ALGORITHM 1) ---
        is_allowed, final_answer, guard_telemetry = self.output_guard.verify_output(
            answer=raw_answer,
            role=role,
            allowed_categories=filters["allowed_categories"],
            patient_scope=filters["scope_desc"],
            context=final_context
        )
        outcome = "ALLOWED" if is_allowed else "BLOCKED"
        pipeline_telemetry["step5_guard"] = guard_telemetry

        # --- STEP 6: CRYPTOGRAPHIC AUDIT LOG (ALGORITHM 2) ---
        audit_record = self.audit_logger.log_event(
            user_id=user_id,
            role=role,
            policy_version=self.policy_engine.get_policy_version(),
            template_version=self.prompt_renderer.template_version,
            filters_applied={
                "scope_desc": filters["scope_desc"],
                "allowed_categories": filters["allowed_categories"],
                "field_masks": filters["field_masks"],
                "is_break_glass": filters["is_break_glass"]
            },
            document_ids=doc_ids,
            outcome=outcome,
            query_text=query,
            extra_telemetry={
                "ids_ok": guard_telemetry["ids_ok"],
                "cats_ok": guard_telemetry["cats_ok"],
                "grounded": guard_telemetry["grounded"],
                "patients_scoped": target_patients
            }
        )
        pipeline_telemetry["step6_audit"] = {
            "entry_index": audit_record["entry"]["entry_index"],
            "hash": audit_record["current_hash"],
            "prev_hash": audit_record["prev_hash"],
            "outcome": outcome,
            "timestamp": audit_record["entry"]["timestamp"]
        }

        pipeline_telemetry["status"] = outcome
        pipeline_telemetry["execution_ms"] = round((time.time() - start_time) * 1000, 2)

        return {
            "answer": final_answer,
            "outcome": outcome,
            "telemetry": pipeline_telemetry
        }
