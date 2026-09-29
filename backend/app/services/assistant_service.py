"""
Context-aware agricultural intelligence assistant service.

Architecture:
  USER QUESTION
  → INTENT DETECTION
  → RETRIEVE UNDERROOT CONTEXT (soil analysis, health score, recommendations, history)
  → RAG KNOWLEDGE RETRIEVAL
  → BUILD GROUNDED RESPONSE
  → RETURN ANSWER + SOURCES

Rules:
- Never fabricate soil measurements.
- Clearly distinguish "your UnderRoot data" from "general knowledge".
- Use actual health_score, deficiencies, excesses from deterministic analyzer.
- Do not invent chemical application rates beyond what the recommendation engine provides.
"""
from __future__ import annotations
from app.integrations.rag.client import get_rag
from app.services.soil_analyzer import analyze_parameters, PARAM_RULES
from app.services.soil_service import calculate_health
from app.services.recommendation_service import crop_recommendations, fertilizer_recommendations

# ── Language strings ─────────────────────────────────────────────────────────
_LANG: dict[str, dict[str, str]] = {
    "en": {
        "no_soil": (
            "I don't have any soil test data linked to your account yet. "
            "Please run a soil test first so I can give you personalised advice based on your actual soil."
        ),
        "data_prefix": "Based on your latest UnderRoot soil test",
        "general_prefix": "In general agricultural practice",
        "health_label": "Soil Health Score",
        "deficiency_label": "Parameters that need attention",
        "excess_label": "Parameters above optimal",
        "all_optimal": "All measured parameters are within the optimal range.",
        "crop_refer": "Check the 'Crop Recommendations' page for the best crops matched to your exact soil values.",
        "fert_refer": "Check the 'Fertilizer Recommendations' page for specific fertilizer guidance.",
        "tip_footer": (
            "\n\n💡 For exact fertilizer doses and crop selection specific to your field, "
            "consult your local Krishi Vigyan Kendra (KVK) or agriculture officer."
        ),
        "knowledge_intro": "\n\nFrom the agricultural knowledge base:\n",
        "sources_intro": "Sources: ",
        "greet": (
            "Namaste! I'm your UnderRoot soil intelligence assistant. "
            "I can explain your soil test results, recommend crops and fertilizers, "
            "and answer general agricultural questions. What would you like to know?"
        ),
        "no_data_for_question": (
            "I don't have enough information in your current UnderRoot data to answer that precisely. "
            "Please run a soil test first."
        ),
        "history_prefix": "Looking at your soil test history",
        "ph_good": "pH ({v}) is within the optimal range for most crops.",
        "ph_low": "pH ({v}) is acidic — may limit nutrient availability. Lime application can help.",
        "ph_high": "pH ({v}) is alkaline — may reduce phosphorus, iron and zinc availability.",
        "n_low": "Nitrogen ({v} kg/ha) is low — crop may show yellowing leaves and slow growth.",
        "p_low": "Phosphorus ({v} kg/ha) is low — root development and early growth may be limited.",
        "k_low": "Potassium ({v} kg/ha) is low — crop resistance to drought and disease may be reduced.",
        "ec_high": "EC ({v} dS/m) is elevated — salinity stress risk for sensitive crops.",
        "oc_low": "Organic carbon ({v}%) is low — soil structure and water retention are reduced.",
        "unit_ph": "", "unit_n": "kg/ha", "unit_p": "kg/ha", "unit_k": "kg/ha",
        "unit_ec": "dS/m", "unit_moisture": "%", "unit_temp": "°C", "unit_oc": "%",
        "ph_label": "pH", "n_label": "Nitrogen", "p_label": "Phosphorus", "k_label": "Potassium",
        "ec_label": "EC", "moisture_label": "Moisture", "temp_label": "Temperature", "oc_label": "Organic Carbon",
    },
    "hi": {
        "no_soil": (
            "अभी आपके खाते में कोई मिट्टी परीक्षण नहीं है। "
            "कृपया पहले मिट्टी परीक्षण करें ताकि मैं आपको सही व्यक्तिगत सलाह दे सकूं।"
        ),
        "data_prefix": "आपके नवीनतम UnderRoot मिट्टी परीक्षण के अनुसार",
        "general_prefix": "सामान्य कृषि ज्ञान के अनुसार",
        "health_label": "मिट्टी स्वास्थ्य स्कोर",
        "deficiency_label": "जिन मापदंडों पर ध्यान देना है",
        "excess_label": "अधिक मात्रा वाले मापदंड",
        "all_optimal": "सभी मापे गए मापदंड सामान्य सीमा में हैं।",
        "crop_refer": "'फसल सुझाव' पृष्ठ देखें — वहाँ आपकी मिट्टी के अनुसार सर्वोत्तम फसलें दिखती हैं।",
        "fert_refer": "'खाद सुझाव' पृष्ठ देखें — वहाँ विशिष्ट खाद मार्गदर्शन उपलब्ध है।",
        "tip_footer": (
            "\n\n💡 सटीक खाद की मात्रा और फसल चुनाव के लिए अपने नज़दीकी "
            "कृषि विज्ञान केंद्र (KVK) या कृषि अधिकारी से मिलें।"
        ),
        "knowledge_intro": "\n\nकृषि ज्ञान आधार से:\n",
        "sources_intro": "स्रोत: ",
        "greet": (
            "नमस्ते! मैं आपका UnderRoot मिट्टी सहायक हूं। "
            "मिट्टी परीक्षण, फसल, खाद या सामान्य खेती के बारे में कुछ भी पूछें।"
        ),
        "no_data_for_question": (
            "आपके वर्तमान UnderRoot डेटा में इस प्रश्न का सटीक उत्तर देने के लिए पर्याप्त जानकारी नहीं है। "
            "पहले मिट्टी परीक्षण करें।"
        ),
        "history_prefix": "आपके मिट्टी परीक्षण इतिहास को देखते हुए",
        "ph_good": "pH ({v}) अधिकांश फसलों के लिए अच्छा है।",
        "ph_low": "pH ({v}) अम्लीय है — पोषक तत्वों की उपलब्धता कम हो सकती है। चूना डालें।",
        "ph_high": "pH ({v}) क्षारीय है — फास्फोरस, लोहा, जस्ता की कमी हो सकती है।",
        "n_low": "नाइट्रोजन ({v} kg/ha) कम है — पत्तियां पीली हो सकती हैं।",
        "p_low": "फॉस्फोरस ({v} kg/ha) कम है — जड़ें कमज़ोर हो सकती हैं।",
        "k_low": "पोटाश ({v} kg/ha) कम है — रोग और सूखे के प्रति प्रतिरोध कम हो सकता है।",
        "ec_high": "EC ({v} dS/m) अधिक है — लवणता का खतरा।",
        "oc_low": "जैविक कार्बन ({v}%) कम है — मिट्टी की संरचना और जल धारण क्षमता कम है।",
        "unit_ph": "", "unit_n": "kg/ha", "unit_p": "kg/ha", "unit_k": "kg/ha",
        "unit_ec": "dS/m", "unit_moisture": "%", "unit_temp": "°C", "unit_oc": "%",
        "ph_label": "pH", "n_label": "नाइट्रोजन", "p_label": "फॉस्फोरस", "k_label": "पोटाश",
        "ec_label": "EC", "moisture_label": "नमी", "temp_label": "तापमान", "oc_label": "जैविक कार्बन",
    },
    "gu": {
        "no_soil": (
            "આપના ખાતામાં હજુ કોઈ માટી પરીક્ષણ નથી. "
            "પ્રથમ માટી પરીક્ષણ કરો, ત્યાર બાદ હું ખાસ સલાહ આપી શકીશ."
        ),
        "data_prefix": "આપના છેલ્લા UnderRoot માટી પરીક્ષણ પ્રમાણે",
        "general_prefix": "સામાન્ય કૃષિ જ્ઞાન પ્રમાણે",
        "health_label": "માટી આરોગ્ય સ્કોર",
        "deficiency_label": "ધ્યાન આપવા જેવા માપદંડ",
        "excess_label": "વધારે માત્રામાં રહેલ માપદંડ",
        "all_optimal": "બધા માપેલ માપદંડ સ્વીકાર્ય સ્તરે છે.",
        "crop_refer": "'પાક ભલામણ' પૃષ્ઠ જુઓ — ત્યાં આપની માટી પ્રમાણે શ્રેષ્ઠ પાક દર્શાવ્યા છે.",
        "fert_refer": "'ખાતર ભલામણ' પૃષ્ઠ જુઓ — ત્યાં વિગતવાર ખાતર માર્ગદર્શન ઉપલબ્ધ છે.",
        "tip_footer": (
            "\n\n💡 ખેતર માટે ચોક્કસ ખાતર માત્રા અને પાક પસંદગી માટે "
            "નજીકના KVK અથવા કૃષિ અધિકારીનો સંપર્ક કરો."
        ),
        "knowledge_intro": "\n\nકૃષિ જ્ઞાન આધારમાંથી:\n",
        "sources_intro": "સ્ત્રોત: ",
        "greet": (
            "નમસ્તે! હું આપનો UnderRoot માટી સ્વાસ્થ્ય સહાયક છું. "
            "માટી, પાક, ખાતર કે ખેતી વિશે ગમે તે પૂછો — સ્વાગત છે."
        ),
        "no_data_for_question": (
            "આ પ્રશ્નનો ચોક્કસ જવાબ આપવા માટે આપના UnderRoot ડેટામાં પૂરતી માહિતી નથી. "
            "પ્રથમ માટી પરીક્ષણ કરો."
        ),
        "history_prefix": "આપના માટી પરીક્ષણ ઇતિહાસ પ્રમાણે",
        "ph_good": "pH ({v}) મોટા ભાગના પાક માટે સારો છે.",
        "ph_low": "pH ({v}) ખાટો (એસિડિક) છે — પોષક તત્ત્વોની ઉપલબ્ધતા ઓછી. ચૂનો ઉમેરો.",
        "ph_high": "pH ({v}) ક્ષારીય છે — ફૉસ્ફૉરસ, લોખંડ, ઝિંકની ઉપલબ્ધ ઓછી.",
        "n_low": "નાઇટ્રોજન ({v} kg/ha) ઓછો છે — પાંદડા પીળા થઈ શકે.",
        "p_low": "ફૉસ્ફૉરસ ({v} kg/ha) ઓછો છે — મૂળ નબળા રહી શકે.",
        "k_low": "પોટૅશ ({v} kg/ha) ઓછો છે — રોગ અને દુષ્કાળ સામે ઓછો પ્રતિકાર.",
        "ec_high": "EC ({v} dS/m) વધારે છે — ક્ષારીય જોખમ.",
        "oc_low": "જૈવ કાર્બન ({v}%) ઓછો છે — માટીની રચના અને ભેજ ધારણ ક્ષમતા ઓછી.",
        "unit_ph": "", "unit_n": "kg/ha", "unit_p": "kg/ha", "unit_k": "kg/ha",
        "unit_ec": "dS/m", "unit_moisture": "%", "unit_temp": "°C", "unit_oc": "%",
        "ph_label": "pH", "n_label": "નાઇટ્રોજન", "p_label": "ફૉસ્ફૉરસ", "k_label": "પોટૅશ",
        "ec_label": "EC", "moisture_label": "ભેજ", "temp_label": "તાપમાન", "oc_label": "જૈવ કાર્બન",
    },
    "mr": {
        "no_soil": (
            "तुमच्या खात्यात अजून माती चाचणी नाही. "
            "कृपया आधी माती चाचणी करा म्हणजे मी तुम्हाला योग्य सल्ला देऊ शकेन."
        ),
        "data_prefix": "तुमच्या ताज्या UnderRoot माती चाचणीनुसार",
        "general_prefix": "सामान्य कृषी ज्ञानानुसार",
        "health_label": "माती आरोग्य गुण",
        "deficiency_label": "लक्ष देण्यायोग्य मापदंड",
        "excess_label": "जास्त प्रमाणातील मापदंड",
        "all_optimal": "सर्व मोजलेले मापदंड योग्य श्रेणीत आहेत.",
        "crop_refer": "'पीक शिफारसी' पेजवर जा — तिथे तुमच्या मातीनुसार सर्वोत्तम पिके दाखवली आहेत.",
        "fert_refer": "'खत शिफारसी' पेजवर जा — तिथे विशिष्ट खत मार्गदर्शन उपलब्ध आहे.",
        "tip_footer": (
            "\n\n💡 अचूक खत मात्रा आणि पीक निवडीसाठी जवळच्या KVK "
            "किंवा कृषी अधिकाऱ्याला भेटा."
        ),
        "knowledge_intro": "\n\nकृषी ज्ञान आधारातून:\n",
        "sources_intro": "स्रोत: ",
        "greet": (
            "नमस्ते! मी तुमचा UnderRoot माती सहाय्यक आहे. "
            "माती, पिके, खते किंवा शेतीबद्दल काहीही विचारा."
        ),
        "no_data_for_question": (
            "या प्रश्नाचे अचूक उत्तर देण्यासाठी तुमच्या UnderRoot डेटात पुरेशी माहिती नाही. "
            "आधी माती चाचणी करा."
        ),
        "history_prefix": "तुमच्या माती चाचणी इतिहासानुसार",
        "ph_good": "pH ({v}) बहुतांश पिकांसाठी चांगला आहे.",
        "ph_low": "pH ({v}) आम्लीय आहे — पोषक तत्त्वांची उपलब्धता कमी. चुना घाला.",
        "ph_high": "pH ({v}) क्षारीय आहे — फॉस्फरस, लोह, झिंक कमी मिळेल.",
        "n_low": "नायट्रोजन ({v} kg/ha) कमी आहे — पाने पिवळी होऊ शकतात.",
        "p_low": "फॉस्फरस ({v} kg/ha) कमी आहे — मुळे कमकुवत राहू शकतात.",
        "k_low": "पोटॅश ({v} kg/ha) कमी आहे — रोग आणि दुष्काळाविरुद्ध प्रतिकार कमी.",
        "ec_high": "EC ({v} dS/m) जास्त आहे — क्षारीय धोका.",
        "oc_low": "सेंद्रिय कार्बन ({v}%) कमी आहे — जमिनीची रचना आणि जलधारण क्षमता कमी.",
        "unit_ph": "", "unit_n": "kg/ha", "unit_p": "kg/ha", "unit_k": "kg/ha",
        "unit_ec": "dS/m", "unit_moisture": "%", "unit_temp": "°C", "unit_oc": "%",
        "ph_label": "pH", "n_label": "नायट्रोजन", "p_label": "फॉस्फरस", "k_label": "पोटॅश",
        "ec_label": "EC", "moisture_label": "ओलावा", "temp_label": "तापमान", "oc_label": "सेंद्रिय कार्बन",
    },
}

# ── Intent keyword maps (multilingual) ───────────────────────────────────────
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "health":       ["health", "score", "healthy", "good soil", "स्वास्थ्य", "स्वास्थ", "स्कोर", "स्वास्थ", "health score",
                     "स्वास्थ्य स्कोर", "આરોગ્ય", "स्कोर", "गुण", "आरोग्य"],
    "report":       ["report", "explain", "analysis", "result", "summary", "detail", "रिपोर्ट", "विश्लेषण", "रिपोर्ट",
                     "detail", "explain report", "soil report", "अहवाल", "विश्लेषण", "અહેવાલ", "विस्तार"],
    "ph":           ["ph", "acid", "alkaline", "acidic", "sour", "sweet", "pH", "अम्ल", "खट्टा", "क्षारीय",
                     "खाटु", "ખાટ", "आंबट", "क्षार", "अम्लता"],
    "nitrogen":     ["nitrogen", "urea", "yellow leaves", "yellowing", "नाइट्रोजन", "यूरिया", "पीला", "नाइट्रो",
                     "નાઇ", "नायट्रोजन", "पिवळ", "पीली", "हरित"],
    "phosphorus":   ["phosphorus", "dap", "ssp", "root", "फॉस्फोरस", "फॉस्फ", "जड़", "ফ", "ফৌ",
                     "ফৌsfos", "ফ্ব", "ফ্ব"],
    "potassium":    ["potassium", "potash", "mop", "disease resistance", "पोटाश", "पोट",
                     "पोटॅश", "पोटेशियम", "drought resistance"],
    "fertilizer":   ["fertilizer", "fertiliser", "khad", "खाद", "खत", "urea", "dap", "mop", "npk",
                     "manure", "compost", "खातर", "ખાતર", "fertilize", "खत", "dose", "apply"],
    "crop":         ["crop", "crops", "which crop", "grow", "plant", "sow", "फसल", "पाक", "पीक",
                     "wheat", "rice", "maize", "cotton", "sugarcane", "कौन सी", "कोणते", "ઉગ", "ઉગાડ"],
    "moisture":     ["moisture", "water", "irrigation", "watering", "नमी", "पानी", "सिंचाई",
                     "ભેજ", "ओलावा", "wet", "dry", "waterlog"],
    "organic":      ["organic", "compost", "manure", "gobar", "गोबर", "जैविक", "organic carbon",
                     "oc", "ઓર્ગ", "सेंद्रिय", "खाद"],
    "salinity":     ["salt", "ec", "salinity", "saline", "नमक", "मीठा", "मीठ", "ક્ષ", "खारे"],
    "comparison":   ["compare", "comparison", "history", "last time", "previous", "trend",
                     "इतिहास", "तुलना", "पिछला", "ઇ"],
    "general":      ["what is", "how to", "explain", "why", "does", "general", "क्या है", "कैसे",
                     "बताइए", "शुं"],
}


def _detect_intents(message: str) -> list[str]:
    """Detect relevant intents from the user message."""
    low = message.lower()
    return [intent for intent, words in _INTENT_KEYWORDS.items() if any(w in low for w in words)]


def _format_health(health_score: float | None, health_status: str | None, lang: dict) -> str:
    """Format a user-friendly health score line."""
    if health_score is None:
        return ""
    status = health_status or "Unknown"
    score = round(health_score, 1)
    return f"{lang['health_label']}: {score}/100 — {status}"


def _format_deficiencies(deficiencies: list[str], excesses: list[str], lang: dict) -> list[str]:
    """Format deficiency/excess lines."""
    lines = []
    if deficiencies:
        lines.append(f"{lang['deficiency_label']}: {', '.join(deficiencies)}")
    if excesses:
        lines.append(f"{lang['excess_label']}: {', '.join(excesses)}")
    if not deficiencies and not excesses:
        lines.append(lang["all_optimal"])
    return lines


def _soil_status_lines(soil: dict, lang: dict) -> list[str]:
    """Generate plain-language status lines for each parameter."""
    lines = []
    ph = soil.get("ph")
    if ph is not None:
        ph_f = float(ph)
        if 6.0 <= ph_f <= 7.5:
            lines.append(f"✅ {lang['ph_good'].format(v=ph)}")
        elif ph_f < 6.0:
            lines.append(f"⚠️ {lang['ph_low'].format(v=ph)}")
        else:
            lines.append(f"⚠️ {lang['ph_high'].format(v=ph)}")

    n = soil.get("nitrogen")
    if n is not None and float(n) < 150:
        lines.append(f"⚠️ {lang['n_low'].format(v=n)}")

    p = soil.get("phosphorus")
    if p is not None and float(p) < 15:
        lines.append(f"⚠️ {lang['p_low'].format(v=p)}")

    k = soil.get("potassium")
    if k is not None and float(k) < 200:
        lines.append(f"⚠️ {lang['k_low'].format(v=k)}")

    ec = soil.get("ec")
    if ec is not None and float(ec) > 4.0:
        lines.append(f"⚠️ {lang['ec_high'].format(v=ec)}")

    oc = soil.get("organic_carbon")
    if oc is not None and float(oc) < 0.5:
        lines.append(f"💡 {lang['oc_low'].format(v=oc)}")

    return lines


def _build_full_context_block(
    soil: dict,
    health_score: float | None,
    health_status: str | None,
    analysis: dict | None,
    lang: dict,
) -> str:
    """Build a comprehensive soil context block."""
    parts = [lang["data_prefix"] + ":"]

    # Health score
    health_line = _format_health(health_score, health_status, lang)
    if health_line:
        parts.append(f"  {health_line}")

    # Deficiencies and excesses from deterministic analysis
    if analysis:
        def_lines = _format_deficiencies(
            analysis.get("deficiencies", []),
            analysis.get("excesses", []),
            lang,
        )
        parts.extend(f"  {l}" for l in def_lines)

    # Individual parameter statuses
    status_lines = _soil_status_lines(soil, lang)
    parts.extend(status_lines)

    return "\n".join(parts)


def answer(
    message: str,
    soil: dict | None = None,
    language: str = "en",
    health_score: float | None = None,
    health_status: str | None = None,
    history: list[dict] | None = None,
    user_name: str | None = None,
) -> tuple[str, list[str]]:
    """
    Generate a grounded, context-aware agricultural assistant response.

    Parameters
    ----------
    message      : User's question
    soil         : Raw soil parameter dict (ph, nitrogen, etc.) — optional
    language     : User language code: en/hi/gu/mr
    health_score : Soil health score from soil_service.calculate_health
    health_status: Health status string (Excellent/Good/Needs Attention/Poor)
    history      : Recent conversation history [{role, content}] for context
    user_name    : User's first name for personalisation
    """
    lang = _LANG.get(language, _LANG["en"])
    q = message.strip()
    sources: list[str] = []

    # ── Greet / trivial input ─────────────────────────────────────────────────
    low = q.lower()
    if low in ("hi", "hello", "namaste", "नमस्ते", "hola", "hey", "kem cho", "kemu cho") or len(q) < 4:
        return lang["greet"], []

    # ── RAG retrieval ─────────────────────────────────────────────────────────
    try:
        retrieved = get_rag().retrieve(q, top_k=3)
        sources = [c.source for c in retrieved if c.source]
    except Exception:
        retrieved = []
        sources = []

    # ── Detect intents ────────────────────────────────────────────────────────
    intents = set(_detect_intents(q))

    # ── Run deterministic analysis on current soil if available ───────────────
    analysis: dict | None = None
    crop_recs: list[dict] = []
    fert_recs: list[dict] = []
    if soil:
        try:
            analysis = analyze_parameters(soil)
        except Exception:
            analysis = None
        try:
            crop_recs = crop_recommendations(soil)
        except Exception:
            crop_recs = []
        try:
            fert_recs = fertilizer_recommendations(soil)
        except Exception:
            fert_recs = []

    # ── No soil data case ─────────────────────────────────────────────────────
    if not soil:
        reply_parts = [lang["no_soil"]]
        if retrieved:
            kb_bits = "\n".join(f"• {c.text[:200]}" for c in retrieved[:2])
            reply_parts.append(lang["knowledge_intro"] + kb_bits)
        reply_parts.append(lang["tip_footer"])
        return "\n".join(reply_parts), sources

    # ── Build targeted response based on intents ──────────────────────────────
    lines: list[str] = []

    # Health / report / overview questions
    if intents & {"health", "report"} or (not intents):
        lines.append(_build_full_context_block(soil, health_score, health_status, analysis, lang))

    # Specific parameter questions
    if "ph" in intents:
        ph = soil.get("ph")
        if ph is not None:
            ph_f = float(ph)
            prefix = f"{lang['data_prefix']}: "
            if 6.0 <= ph_f <= 7.5:
                lines.append(prefix + lang["ph_good"].format(v=ph))
            elif ph_f < 6.0:
                lines.append(prefix + lang["ph_low"].format(v=ph))
            else:
                lines.append(prefix + lang["ph_high"].format(v=ph))
        # Supplement with RAG knowledge on pH
        if retrieved:
            for c in retrieved[:1]:
                if "ph" in c.text.lower() or "acid" in c.text.lower() or "alkalin" in c.text.lower():
                    lines.append(f"\n{lang['general_prefix']}: {c.text[:300]}")

    if "nitrogen" in intents:
        n = soil.get("nitrogen")
        prefix = f"{lang['data_prefix']}: "
        if n is not None:
            if float(n) < 150:
                lines.append(prefix + lang["n_low"].format(v=n))
            else:
                lines.append(prefix + f"{lang['n_label']}: {n} {lang['unit_n']} — within optimal range.")
        else:
            lines.append(f"I don't have a nitrogen measurement for your soil.")

    if "phosphorus" in intents:
        p = soil.get("phosphorus")
        prefix = f"{lang['data_prefix']}: "
        if p is not None:
            if float(p) < 15:
                lines.append(prefix + lang["p_low"].format(v=p))
            else:
                lines.append(prefix + f"{lang['p_label']}: {p} {lang['unit_p']} — within optimal range.")
        else:
            lines.append(f"I don't have a phosphorus measurement for your soil.")

    if "potassium" in intents:
        k = soil.get("potassium")
        prefix = f"{lang['data_prefix']}: "
        if k is not None:
            if float(k) < 200:
                lines.append(prefix + lang["k_low"].format(v=k))
            else:
                lines.append(prefix + f"{lang['k_label']}: {k} {lang['unit_k']} — within optimal range.")
        else:
            lines.append(f"I don't have a potassium measurement for your soil.")

    if "organic" in intents:
        oc = soil.get("organic_carbon")
        prefix = f"{lang['data_prefix']}: "
        if oc is not None:
            if float(oc) < 0.5:
                lines.append(prefix + lang["oc_low"].format(v=oc))
            else:
                lines.append(prefix + f"{lang['oc_label']}: {oc} {lang['unit_oc']} — within optimal range.")

    if "salinity" in intents or "moisture" in intents:
        ec = soil.get("ec")
        moisture = soil.get("moisture")
        prefix = f"{lang['data_prefix']}: "
        if ec is not None and float(ec) > 4.0:
            lines.append(prefix + lang["ec_high"].format(v=ec))
        if moisture is not None:
            lines.append(prefix + f"{lang['moisture_label']}: {moisture} {lang['unit_moisture']}")

    # Fertilizer question — use deterministic recommendation engine output
    if "fertilizer" in intents:
        prefix = f"{lang['data_prefix']}: "
        if fert_recs:
            fert_summary = fert_recs[0]
            reason = fert_recs[0].get("reason", "")
            lines.append(f"{prefix}\n{reason}")
        lines.append(f"\n{lang['fert_refer']}")

    # Crop question — use deterministic recommendation engine output
    if "crop" in intents:
        prefix = f"{lang['data_prefix']}: "
        if crop_recs:
            top_crop = crop_recs[0]
            lines.append(
                f"{prefix}\n{top_crop.get('reason', '')} "
                f"(Suitability: {top_crop.get('suitability', '')}%)"
            )
            if len(crop_recs) > 1:
                others = ", ".join(c["crop"] for c in crop_recs[1:])
                lines.append(f"Also suitable: {others}.")
        lines.append(f"\n{lang['crop_refer']}")

    # Comparison / history question
    if "comparison" in intents:
        if history:
            lines.append(lang["history_prefix"] + ":")
            lines.append(f"  {lang['data_prefix']}: " + _format_health(health_score, health_status, lang))
        else:
            lines.append(lang["data_prefix"] + ": " + _format_health(health_score, health_status, lang))

    # If no specific intent matched but soil is available, show full summary
    if not lines:
        lines.append(_build_full_context_block(soil, health_score, health_status, analysis, lang))

    reply = "\n".join(l for l in lines if l)

    # ── Append RAG knowledge context ──────────────────────────────────────────
    # For general questions, prefer RAG. For specific parameter questions, limit to 1 snippet.
    is_general = "general" in intents or not (intents & {
        "health", "report", "ph", "nitrogen", "phosphorus", "potassium",
        "organic", "salinity", "moisture", "fertilizer", "crop", "comparison"
    })
    if retrieved and is_general:
        kb_snippet = "\n".join(f"• {c.text[:250]}" for c in retrieved[:2])
        reply += lang["knowledge_intro"] + kb_snippet
    elif retrieved and intents and len(lines) > 0:
        # Add one relevant RAG snippet if truly helpful
        best = retrieved[0]
        if any(kw in best.text.lower() for kw in q.lower().split()[:3]):
            reply += f"\n\n{lang['general_prefix']}:\n• {best.text[:220]}"

    reply += lang["tip_footer"]
    return reply, list(dict.fromkeys(sources))  # deduplicated sources
