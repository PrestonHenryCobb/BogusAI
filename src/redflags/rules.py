"""Red-flag taxonomy, patterns, explanations, severity, and feature names."""


def _any(*alternatives):
    return "|".join(alternatives)


_GIFT_CARD = r"(?:gift|store|retail)[- ]?cards?"
_SSN = r"(?:social security(?: number)?|\bssn\b)"
_LEFTOVER = r"(?:extra|excess|leftover|remaining|remainder|rest|unused|balance|difference|part of|portion|amount (?:left|beyond))"
_CRYPTO = r"(?:bitcoin|crypto(?:currency)?|usdt|ethereum)"

RULES = [
    (
        "Upfront payment",
        _any(
            # "...will not be obligated to pay a placement fee" is employer boilerplate aimed at agencies.
            r"(?<!obligated to pay a )(?<!responsible for any )(?:registration|training|application|processing|activation|placement|credential|sign-?up|setup|entry|starter kit|equipment)\s+fee",
            # "processing payments" is a common legit duty, so processing only counts with a price or "pay the".
            r"(?:registration|training|application|activation|placement|credential|sign-?up|setup|entry|starter kit|equipment)\s+(?:charge|payment|amount)\b",
            r"(?:\$\d[\d,]*|pay\s+the)\s+processing\s+(?:charge|payment)\b",
            r"refundable\s+(?:\$?\d[\d,]*\s+)?(?:[\w-]+\s+){0,2}(?:fee|charge|deposit)",
            r"\bpay(?:ing)?\s+(?:a\s+|an\s+|the\s+)?\$\d[\d,]*\s+(?:for|to)\b(?!\s*\$)",  # not a "Pay $9 to $12" wage range
            r"pay\s+(a|an|the)?\s*\$?\d+.{0,20}(to (start|secure|begin)|upfront)",
            r"(?:buy|purchase)\s+(?:[\w-]+\s+){0,4}(?:bundle|package|kit|access)\b",
        ),
        "Real employers don't charge you to get hired.",
        "high",
        "flag_upfront_payment",
    ),
    (
        "Check or money forwarding",
        _any(
            r"(deposit|cash)\s+(the|a|this|it)?\s*check",
            # Verb forms only: "check sales, returns and exchanges ... daily balance" is a cashier's duty list.
            r"\b(?:pay)?check\b.{0,100}?\b(?:send\w*|return(?:ing|ed)?|wire[ds]?|wiring|transfer\w*|forward\w*)\b.{0,60}?" + _LEFTOVER,
            r"send\s+(back\s+)?the\s+(remainder|rest|difference)",
            # Bank roles list "wire transfers and collections" as duties; only sending money by wire counts.
            r"western union|moneygram|zelle|(?:send|pay|via|by|through)\s+(?:a\s+|the\s+)?wire transfer",
            r"(?:buy|purchase|get)\s+(?:[\w-]+\s+){0,3}" + _GIFT_CARD,
            r"(?:send|pay\s+for)\s+(?:the\s+)?gift cards?",
            r"\b(?:pay|settle)\b.{0,60}?\bwith\s+(?:[\w-]+\s+){0,2}" + _GIFT_CARD,
            _GIFT_CARD + r".{0,40}?\b(?:codes?|pins?|numbers?)\b",
        ),
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
        _any(
            # Asked for, not mentioned: "reconcile bank accounts" is an accounting duty.
            r"\b(?:send|provide|share|submit|give|text|email|enter|need|require)\w*\b.{0,40}?\bbank (?:details|information|login|password|accounts?)\b",
            r"\byour\s+(?:[\w-]+\s+){0,2}bank (?:details|account|information|login|password)|\byour\s+routing number",
            r"copy of your (id|passport|driver)",
            r"(?:photo|picture|image|scan)\s+of\s+(?:your|their|an?)\s+(?:id|passport|driver)",
            r"\b(?:id|passport)\s+(?:image|scan|photo|picture)",
            r"(?:(?:before|prior to|without)\s+(?:a\s+)?(?:formal\s+)?(?:job\s+)?(?:the\s+)?(?:offer|interview|hiring|onboarding).{0,60}" + _SSN
            + r"|" + _SSN + r".{0,60}(?:before|prior to|without)\s+(?:a\s+)?(?:formal\s+)?(?:job\s+)?(?:the\s+)?(?:offer|interview|hiring|onboarding)"
            + r"|(?:send|provide|share|submit|give|text)\s+(?:us\s+|me\s+|your\s+)?" + _SSN
            + r".{0,20}(?:before|prior to)\s+(?:a\s+)?(?:formal\s+)?(?:job\s+)?(?:the\s+)?(?:offer|interview|hiring|onboarding))",
            _SSN + r".{0,80}?\bbefore\s+(?:we\s+(?:can\s+)?(?:speak|talk|meet|schedule)|(?:a|the|any|our|your)\s+(?:first\s+)?(?:screening|interview|call))",
            r"before\s+we\s+(?:speak|talk|meet).{0,40}" + _SSN,
        ),
        "Bank or ID details should only be requested after a formal offer, through HR systems.",
        "high",
        "flag_sensitive_details",
    ),
    (
        "Too easy, too fast",
        _any(
            r"no (interview|experience)\s+(is\s+)?(required|needed|necessary)",
            r"hired immediately|start (today|immediately)",
            r"(?:hired|hire you)\s+without\s+(?:an?\s+)?interview",
            r"without\s+(?:screening\s+or\s+)?(?:an?\s+)?interview",
            r"guarantee\w*\s+(?:[\w-]+\s+)?(?:hiring|the job|placement)",
            r"earn \$?\d[\d,]*\s*(\+)?\s*(a|per)?\s*(day|daily|week|weekly)",
        ),
        "High pay with no interview or experience is a common lure.",
        "medium",
        "flag_easy_fast",
    ),
    (
        "Task or crypto earnings",
        _any(
            r"(?:complete|finish|perform)\s+(?:simple\s+)?(?:online\s+)?tasks?.{0,40}(?:earn|paid|payment).{0,20}" + _CRYPTO,
            r"(?:earn|paid|payment).{0,20}" + _CRYPTO + r".{0,30}(?:task|click|like|rating)",
            r"\b(?:click|like|liking|rating)\w*\b.{0,60}?\b" + _CRYPTO + r"\b",
            r"\b(?:pay|paid|earn)\w*\s+(?:in\s+)?" + _CRYPTO + r"\b.{0,60}?\b(?:click|like|liking|rating|task)",
            r"\btoken pay\b|\bearn\w*\s+tokens?\b",
            r"recharge\b.{0,30}account|account.{0,30}\brecharge\b",
            r"\b(?:fund|top up)\s+(?:a|the|your)\s+(?:wallet|account)\b|add funds to (?:the|your) account",
            r"deposit is required to (?:release|unlock|withdraw)",
            r"unlock\s+(?:your\s+)?withdrawals?",
        ),
        "Verify carefully before doing online tasks that promise payment in cryptocurrency.",
        "high",
        "flag_task_crypto",
    ),
    (
        "Reshipping or mystery shopping",
        _any(
            r"(?:receive|accept|inspect)\w*\s+(?:[\w-]+\s+){0,2}(?:packages?|parcels?|deliveries|boxes|shipments).{0,80}?(?:reship|re-ship|relabel|forward|mail\w*\s+(?:them|it)\s+onward)",
            r"(?:reship|re-ship|forward)\s+(?:packages?|parcels?)",
            r"mystery shopper.{0,40}(?:buy|purchase|gift cards?|reimburse)",
        ),
        "Verify the employer before receiving or forwarding packages or buying items for reimbursement.",
        "high",
        "flag_reshipping_mystery_shopping",
    ),
    (
        "Personal-email recruiter",
        _any(
            r"(?:send|email|contact)\s+(?:your\s+)?(?:resume|application|me).{0,30}(?:gmail|yahoo|hotmail|outlook|aol)",
            r"(?:gmail|yahoo|hotmail|outlook|aol)\s+(?:account|email|address)",
            r"\b(?:personal|private|free)\s+(?:[\w-]+\s+)?(?:inbox|webmail|email account)",
            r"\bwebmail\b",
        ),
        "Confirm a recruiter's identity through the employer's official contact channels.",
        "medium",
        "flag_personal_email_recruiter",
    ),
    (
        "Urgency or secrecy",
        _any(
            r"(?:act|reply|respond)\s+(?:right\s+)?now",
            r"(?:offer|position).{0,20}(?:expires|only available for)\s+(?:today|24 hours?)",
            r"expires?\s+in\s+(?:an?\s+|\d+\s+|ten\s+|a few\s+)?(?:hour|minutes?)\b",
            r"same-hour decision|(?:accept|decide|reply|respond)\w*\s+within\s+minutes",
            r"(?:keep|don't share|do not share).{0,20}(?:secret|private|confidential)",
            r"don't tell\s+(?:anyone|your family|the bank)",
            r"(?:not|don't|do not)\s+(?:to\s+)?discuss\b.{0,40}(?:family|bank|anyone)",
            r"discourag\w*\s+questions",
        ),
        "Take time to verify urgent offers, especially when someone asks you to keep them secret.",
        "medium",
        "flag_urgency_secrecy",
    ),
    (
        "Vague duties with high pay",
        _any(
            r"(?:simple|easy|basic)\s+(?:tasks?|work|duties).{0,40}(?:earn|make|paid).{0,20}\$?\d[\d,]*\s*(?:a|per)?\s*(?:day|daily|week|weekly)",
            r"(?:earn|make)\s+\$?\d[\d,]*\s*(?:a|per)?\s*(?:day|daily|week|weekly).{0,40}(?:simple|easy|basic)\s+(?:tasks?|work|duties)",
            r"(?:earn|make|offer|pay)\w*\s+\$?\d[\d,]*\s*(?:a|per|each)\s+(?:day|week)\b.{0,50}(?:simple|easy|basic)",
            r"(?:large|big|high|huge)\s+(?:daily|weekly)\s+(?:earnings|pay|income).{0,40}(?:simple|easy|basic)",
        ),
        "Ask for specific duties and independently verify unusually high pay for simple work.",
        "medium",
        "flag_vague_duties_high_pay",
    ),
]
