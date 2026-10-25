def build_query(disease: str, intent: str = "diagnosis"):
    """
    Simple dynamic query builder.
    You can later make this more advanced.
    """

    if intent == "diagnosis":
        return f"""
        {disease} symptoms signs clinical features diagnosis criteria,
        {disease} diagnostic approach history examination evaluation,
        {disease} differential diagnosis and clinical findings
        """

    elif intent == "treatment":
        return f"""
        {disease} treatment management medications therapy protocol,
        {disease} first line treatment and supportive care
        """

    else:
        return disease
