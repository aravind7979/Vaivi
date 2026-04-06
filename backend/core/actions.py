def get_suggested_actions(plan_intent: str, query: str) -> list:
    """
    Returns a dummy scaffold of possible actions based on intent.
    In the future, this layer will hook into system automation or UI controls.
    """
    if plan_intent == "debug":
        return ["Check system logs", "View latest errors"]
    elif plan_intent == "action":
        return ["Perform suggested UI click", "Execute macro"]
    
    return []
