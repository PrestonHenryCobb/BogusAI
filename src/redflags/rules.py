"""Red-flag taxonomy, patterns, explanations, severity, and feature names."""

RULES = [
    (
        "Upfront payment",
        r"(registration|training|application|processing|starter kit|equipment)\s+fee|pay\s+(a|an|the)?\s*\$?\d+.{0,20}(to (start|secure|begin)|upfront)",
        "Real employers don't charge you to get hired.",
        "high",
        "flag_upfront_payment",
    ),
    (
        "Check or money forwarding",
        r"(deposit|cash)\s+(the|a|this|it)?\s*check|send\s+(back\s+)?the\s+(remainder|rest|difference)|western union|moneygram|(?:buy|send|pay\s+for)\s+(?:the\s+)?gift cards?|gift card codes?|zelle|wire transfer",
        "Being sent a check and asked to forward part of it is the classic overpayment scam.",
        "high",
        "flag_check_overpayment",
    ),
    (
        "Off-platform chat",
        r"telegram|whatsapp|google (chat|hangouts)|signal app|text me (at|on)",
        "Moving the conversation to a chat app early avoids the job site's fraud checks.",
        "medium",
        "flag_off_platform_chat",
    ),
    (
        "Sensitive details too early",
        r"bank (details|account|information)|routing number|copy of your (id|passport|driver)|(?:(?:before|prior to|without)\s+(?:a\s+)?(?:formal\s+)?(?:job\s+)?(?:the\s+)?(?:offer|interview|hiring|onboarding).{0,60}(?:social security(?: number)?|\bssn\b)|(?:social security(?: number)?|\bssn\b).{0,60}(?:before|prior to|without)\s+(?:a\s+)?(?:formal\s+)?(?:job\s+)?(?:the\s+)?(?:offer|interview|hiring|onboarding)|(?:send|provide|share|submit|give|text)\s+(?:us\s+|me\s+|your\s+)?(?:social security(?: number)?|\bssn\b).{0,20}(?:before|prior to)\s+(?:a\s+)?(?:formal\s+)?(?:job\s+)?(?:the\s+)?(?:offer|interview|hiring|onboarding))",
        "Bank or ID details should only be requested after a formal offer, through HR systems.",
        "high",
        "flag_sensitive_details",
    ),
    (
        "Too easy, too fast",
        r"no (interview|experience)\s+(is\s+)?(required|needed|necessary)|hired immediately|start (today|immediately)|earn \$?\d[\d,]*\s*(\+)?\s*(a|per)?\s*(day|daily|week|weekly)",
        "High pay with no interview or experience is a common lure.",
        "medium",
        "flag_easy_fast",
    ),
    (
        "Task or crypto earnings",
        r"(?:complete|finish|perform)\s+(?:simple\s+)?(?:online\s+)?tasks?.{0,40}(?:earn|paid|payment).{0,20}(?:bitcoin|crypto|usdt|ethereum)|(?:earn|paid|payment).{0,20}(?:bitcoin|crypto|usdt|ethereum).{0,30}(?:task|click|like|rating)|recharge\s+(?:your\s+)?account|unlock\s+(?:your\s+)?withdrawals?",
        "Verify carefully before doing online tasks that promise payment in cryptocurrency.",
        "high",
        "flag_task_crypto",
    ),
    (
        "Reshipping or mystery shopping",
        r"(?:receive|accept|inspect)\s+(?:packages?|parcels?).{0,40}(?:reship|re-ship|forward)|(?:reship|re-ship|forward)\s+(?:packages?|parcels?)|mystery shopper.{0,40}(?:buy|purchase|gift cards?|reimburse)",
        "Verify the employer before receiving or forwarding packages or buying items for reimbursement.",
        "high",
        "flag_reshipping_mystery_shopping",
    ),
    (
        "Personal-email recruiter",
        r"(?:send|email|contact)\s+(?:your\s+)?(?:resume|application|me).{0,30}(?:gmail|yahoo|hotmail|outlook|aol)|(?:gmail|yahoo|hotmail|outlook|aol)\s+(?:account|email|address)",
        "Confirm a recruiter's identity through the employer's official contact channels.",
        "medium",
        "flag_personal_email_recruiter",
    ),
    (
        "Urgency or secrecy",
        r"(?:act|reply|respond)\s+(?:right\s+)?now|(?:offer|position).{0,20}(?:expires|only available for)\s+(?:today|24 hours?)|(?:keep|don't share|do not share).{0,20}(?:secret|private|confidential)|don't tell\s+(?:anyone|your family|the bank)",
        "Take time to verify urgent offers, especially when someone asks you to keep them secret.",
        "medium",
        "flag_urgency_secrecy",
    ),
    (
        "Vague duties with high pay",
        r"(?:simple|easy|basic)\s+(?:tasks?|work|duties).{0,40}(?:earn|make|paid).{0,20}\$?\d[\d,]*\s*(?:a|per)?\s*(?:day|daily|week|weekly)|(?:earn|make)\s+\$?\d[\d,]*\s*(?:a|per)?\s*(?:day|daily|week|weekly).{0,40}(?:simple|easy|basic)\s+(?:tasks?|work|duties)",
        "Ask for specific duties and independently verify unusually high pay for simple work.",
        "medium",
        "flag_vague_duties_high_pay",
    ),
]
