# /composable-orchestrator/consensus_service/policy.rego
package policy.eval

# --- DEFAULT VALUES ---
default status := "ERROR"
default final_grade := 0
default justification := "Policy evaluation error: No specific rules matched the input."
default feedback := "An internal error occurred during policy evaluation."

# ---
# Rule 1: SUCCESSFUL EVALUATION (High Confidence)
# ---
status := "COMPLETE" if {
    input.agent_confidence >= 0.8
}

final_grade := input.verdict_data.score if {
    input.agent_confidence >= 0.8
}

justification := input.verdict_data.justification if {
    input.agent_confidence >= 0.8
}

feedback := input.verdict_data.feedback_for_student if {
    input.agent_confidence >= 0.8
}

# ---
# Rule 2: LOW CONFIDENCE (Flag for Manual Review)
# ---
status := "MANUAL_REVIEW" if {
    input.agent_confidence < 0.8
}

final_grade := 0 if {
    input.agent_confidence < 0.8
}

justification := "Evaluation flagged for manual review due to low AI confidence during processing (e.g., LLM API error or Vision/OCR uncertainty)." if {
    input.agent_confidence < 0.8
}

feedback := "An issue occurred during automated processing. Please review manually." if {
    input.agent_confidence < 0.8
}
