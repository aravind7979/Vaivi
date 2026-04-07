def suggest_actions(plan, response_text):
    """
    Parses the response or plan to scaffold UI actions.
    Future-ready for actual automations.
    """
    actions = []
    
    if plan.get("intent") == "debug":
        actions.append("Search documentation for this error")
        
    if plan.get("intent") == "action":
        actions.append("Execute suggested fix")

    return {
        "type": "suggestion",
        "actions": actions
    }
