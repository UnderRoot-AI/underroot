"""
Farmer-friendly, multilingual assistant service.
Uses the local RAG knowledge base and the user's soil test data.
Responds in the language the user selected (en / hi / gu / mr).
"""
from __future__ import annotations
from app.integrations.rag.client import get_rag

# ── Language strings ────────────────────────────────────────────────────────
_LANG: dict[str, dict[str, str]] = {
    "en": {
        "no_soil": "I don't see any soil test linked yet. Please run a soil test first so I can give you personalised advice.",
        "soil_prefix": "Your latest soil test shows",
        "ph_label": "pH",
        "n_label": "Nitrogen",
        "p_label": "Phosphorus",
        "k_label": "Potassium",
        "ec_label": "Salt (EC)",
        "moisture_label": "Moisture",
        "temp_label": "Temperature",
        "oc_label": "Organic Carbon",
        "unit_ph": "",
        "unit_n": "kg/ha",
        "unit_p": "kg/ha",
        "unit_k": "kg/ha",
        "unit_ec": "dS/m",
        "unit_moisture": "%",
        "unit_temp": "°C",
        "unit_oc": "%",
        "ph_good": "✅ Your pH ({v}) is good for most crops.",
        "ph_low": "⚠️ Your pH ({v}) is a bit sour (acidic). Adding lime can help. Ask your KVK officer about lime dose.",
        "ph_high": "⚠️ Your pH ({v}) is a bit sweet (alkaline). Growing tolerant crops like barley or mustard can help. Organic compost also slowly improves this.",
        "n_low": "⚠️ Nitrogen is low ({v} kg/ha). Your crop may show yellow leaves. Use Urea or DAP as recommended.",
        "p_low": "⚠️ Phosphorus is low ({v} kg/ha). Roots may be weak. Apply DAP or SSP at sowing time.",
        "k_low": "⚠️ Potassium is low ({v} kg/ha). Crop may be less strong against disease. Use MOP fertilizer.",
        "ec_high": "⚠️ Salt level (EC) is high ({v} dS/m). Too much salt harms roots. Ask about salt management.",
        "oc_low": "💡 Organic carbon is low ({v}%). Add compost (gobar khad) or green manure to improve soil health.",
        "tip_footer": "\n\n💡 Tip: For exact fertilizer dose and crop choice for your field, talk to your local Krishi Vigyan Kendra (KVK) or agriculture officer.",
        "knowledge_intro": "\n\nFrom the agriculture knowledge base:\n",
        "greet": "Namaste! I am your soil health assistant. Ask me anything about your soil, crops, or farming. I will explain in simple words.",
    },
    "hi": {
        "no_soil": "अभी कोई मिट्टी परीक्षण नहीं मिला। कृपया पहले मिट्टी परीक्षण करें ताकि मैं आपको सही सलाह दे सकूं।",
        "soil_prefix": "आपके नवीनतम मिट्टी परीक्षण में",
        "ph_label": "pH (अम्लता)",
        "n_label": "नाइट्रोजन",
        "p_label": "फॉस्फोरस",
        "k_label": "पोटाश",
        "ec_label": "नमक (EC)",
        "moisture_label": "नमी",
        "temp_label": "तापमान",
        "oc_label": "जैविक कार्बन",
        "unit_ph": "",
        "unit_n": "kg/ha",
        "unit_p": "kg/ha",
        "unit_k": "kg/ha",
        "unit_ec": "dS/m",
        "unit_moisture": "%",
        "unit_temp": "°C",
        "unit_oc": "%",
        "ph_good": "✅ आपका pH ({v}) अधिकांश फसलों के लिए अच्छा है।",
        "ph_low": "⚠️ आपकी मिट्टी थोड़ी खट्टी (अम्लीय) है (pH {v})। चूना (lime) डालने से सुधार होता है। KVK अधिकारी से मात्रा जानें।",
        "ph_high": "⚠️ आपकी मिट्टी थोड़ी क्षारीय है (pH {v})। जौ, सरसों जैसी सहनशील फसलें उगाएं। जैविक खाद भी धीरे-धीरे सुधार करती है।",
        "n_low": "⚠️ नाइट्रोजन कम है ({v} kg/ha)। पत्तियां पीली हो सकती हैं। यूरिया या DAP का उपयोग करें।",
        "p_low": "⚠️ फॉस्फोरस कम है ({v} kg/ha)। जड़ें कमज़ोर हो सकती हैं। बुआई के समय DAP या SSP डालें।",
        "k_low": "⚠️ पोटाश कम है ({v} kg/ha)। फसल बीमारी से कम मजबूत होगी। MOP (पोटाश) खाद डालें।",
        "ec_high": "⚠️ नमक (EC) अधिक है ({v} dS/m)। अधिक नमक जड़ों को नुकसान पहुंचाता है। नमक प्रबंधन के बारे में सलाह लें।",
        "oc_low": "💡 जैविक कार्बन कम है ({v}%)। गोबर खाद या हरी खाद डालकर मिट्टी की सेहत सुधारें।",
        "tip_footer": "\n\n💡 सुझाव: सटीक खाद की मात्रा और फसल चुनाव के लिए अपने नज़दीकी कृषि विज्ञान केंद्र (KVK) या कृषि अधिकारी से मिलें।",
        "knowledge_intro": "\n\nकृषि ज्ञान आधार से:\n",
        "greet": "नमस्ते! मैं आपका मिट्टी स्वास्थ्य सहायक हूं। अपनी मिट्टी, फसल या खेती के बारे में कुछ भी पूछें। मैं आसान भाषा में समझाऊंगा।",
    },
    "gu": {
        "no_soil": "હજુ કોઈ માટી પરીક્ષણ મળ્યું નથી. પહેલા માટી પરીક્ષણ કરો, ત્યાર બાદ હું ખાસ સલાહ આપી શકીશ.",
        "soil_prefix": "આપના છેલ્લા માટી પરીક્ષણ મુજબ",
        "ph_label": "pH",
        "n_label": "નાઇટ્રોજન",
        "p_label": "ફૉસ્ફૉરસ",
        "k_label": "પોટૅશ",
        "ec_label": "મીઠું (EC)",
        "moisture_label": "ભેજ",
        "temp_label": "તાપમાન",
        "oc_label": "જૈવ કાર્બન",
        "unit_ph": "",
        "unit_n": "kg/ha",
        "unit_p": "kg/ha",
        "unit_k": "kg/ha",
        "unit_ec": "dS/m",
        "unit_moisture": "%",
        "unit_temp": "°C",
        "unit_oc": "%",
        "ph_good": "✅ આપનો pH ({v}) અધિકાંશ પાક માટે સારો છે.",
        "ph_low": "⚠️ માટી થોડી ખાટી (એસિડિક) છે (pH {v}). ચૂનો (lime) ઉમેરવાથી સુધારો થાય. KVK ઓફિસર પાસેથી માત્રા જાણો.",
        "ph_high": "⚠️ માટી થોડી ક્ષારીય છે (pH {v}). જવ, સરસવ જેવા સહનશીલ પાક ઉગાડો. ઓર્ગેનિક ખાદ ધીમે ધીમે સુધારો કરે.",
        "n_low": "⚠️ નાઇટ્રોજન ઓછો છે ({v} kg/ha). પાંદડા પીળા થઈ શકે. યૂરિયા અથવા DAP વાપરો.",
        "p_low": "⚠️ ફૉસ્ફૉરસ ઓછો છે ({v} kg/ha). મૂળ નબળા થઈ શકે. વાવણી સમયે DAP કે SSP ઉમેરો.",
        "k_low": "⚠️ પોટૅશ ઓછો છે ({v} kg/ha). પાક રોગ સામે ઓછો મજબૂત. MOP ઉમેરો.",
        "ec_high": "⚠️ મીઠાનું પ્રમાણ (EC) વધારે છે ({v} dS/m). વધારે મીઠું મૂળને નુકસાન કરે. નિષ્ણાતની સલાહ લો.",
        "oc_low": "💡 જૈવ કાર્બન ઓછો છે ({v}%). ગોબર ખાદ અથવા લીલા ખાતર ઉમેરો.",
        "tip_footer": "\n\n💡 સૂચન: ચોક્કસ ખાતર અને પાક પસંદગી માટે નજીકના KVK અથવા કૃષિ અધિકારીને મળો.",
        "knowledge_intro": "\n\nકૃષિ જ્ઞાન આધારમાંથી:\n",
        "greet": "નમસ્તે! હું આપનો માટી સ્વાસ્થ્ય સહાયક છું. માટી, પાક કે ખેતી વિશે ગમે તે પૂછો — સરળ ભાષામાં સમજાવીશ.",
    },
    "mr": {
        "no_soil": "अजून कोणतीही माती चाचणी सापडली नाही. कृपया आधी माती चाचणी करा म्हणजे मी तुम्हाला योग्य सल्ला देऊ शकेन.",
        "soil_prefix": "तुमच्या ताज्या माती चाचणीनुसार",
        "ph_label": "pH",
        "n_label": "नायट्रोजन",
        "p_label": "फॉस्फरस",
        "k_label": "पोटॅश",
        "ec_label": "मीठ (EC)",
        "moisture_label": "ओलावा",
        "temp_label": "तापमान",
        "oc_label": "सेंद्रिय कार्बन",
        "unit_ph": "",
        "unit_n": "kg/ha",
        "unit_p": "kg/ha",
        "unit_k": "kg/ha",
        "unit_ec": "dS/m",
        "unit_moisture": "%",
        "unit_temp": "°C",
        "unit_oc": "%",
        "ph_good": "✅ तुमचा pH ({v}) बहुतांश पिकांसाठी चांगला आहे.",
        "ph_low": "⚠️ माती थोडी आंबट (आम्लीय) आहे (pH {v}). चुना (lime) घालण्याने सुधारणा होते. KVK अधिकाऱ्याकडून मात्रा जाणून घ्या.",
        "ph_high": "⚠️ माती थोडी क्षारीय आहे (pH {v}). जव, मोहरी सारखी सहनशील पिके घ्या. सेंद्रिय खत हळूहळू सुधारणा करते.",
        "n_low": "⚠️ नायट्रोजन कमी आहे ({v} kg/ha). पाने पिवळी होऊ शकतात. युरिया किंवा DAP वापरा.",
        "p_low": "⚠️ फॉस्फरस कमी आहे ({v} kg/ha). मुळे कमकुवत होऊ शकतात. पेरणीच्या वेळी DAP किंवा SSP घाला.",
        "k_low": "⚠️ पोटॅश कमी आहे ({v} kg/ha). पीक रोगास कमी प्रतिरोधक. MOP खत घाला.",
        "ec_high": "⚠️ मीठाचे प्रमाण (EC) जास्त आहे ({v} dS/m). जास्त मीठ मुळांना इजा करते. तज्ज्ञांचा सल्ला घ्या.",
        "oc_low": "💡 सेंद्रिय कार्बन कमी आहे ({v}%). शेणखत किंवा हिरवळ खत घालून जमिनीची सुधारणा करा.",
        "tip_footer": "\n\n💡 सूचना: अचूक खत मात्रा आणि पीक निवडीसाठी जवळच्या KVK किंवा कृषी अधिकाऱ्याला भेटा.",
        "knowledge_intro": "\n\nकृषी ज्ञान आधारातून:\n",
        "greet": "नमस्ते! मी तुमचा माती आरोग्य सहाय्यक आहे. माती, पिके किंवा शेतीबद्दल काहीही विचारा — साध्या भाषेत सांगेन.",
    },
}

# ── Keyword maps for multilingual query detection ───────────────────────────
_KEYWORDS = {
    "ph":          ["ph", "पीएच", "अम्ल", "खट्टा", "क्षारीय", "acid", "alkaline", "ખાટ", "pH", "आंबट", "क्षार"],
    "nitrogen":    ["nitrogen", "नाइट्रोजन", "urea", "यूरिया", "yellow", "पीला", "नाइट्रो", "નાઇ", "नायट्रोजन"],
    "phosphorus":  ["phosphorus", "फॉस्फोरस", "dap", "ssP", "root", "जड़", "फास्फ", "ફૉ", "फॉस्फ"],
    "potassium":   ["potassium", "पोटाश", "potash", "mop", "strong", "disease", "बीमारी", "पोट", "पोटॅश"],
    "fertilizer":  ["fertilizer", "खाद", "खाद्य", "कीटनाशक", "urea", "dap", "mop", "npk", "खातर", "खत"],
    "crop":        ["crop", "फसल", "crops", "which crop", "कौन सी", "पाक", "पीक", "wheat", "rice", "maize", "गेहूं", "चावल"],
    "moisture":    ["moisture", "water", "नमी", "पानी", "irrigation", "सिंचाई", "ભેજ", "ओलावा"],
    "organic":     ["organic", "compost", "gobar", "गोबर", "जैविक", "oc", "organic carbon", "ઓર્ग", "सेंद्रिय"],
    "salinity":    ["salt", "ec", "salinity", "नमक", "ec value", "मीठा", "મીઠ", "मीठ"],
    "health":      ["health", "score", "स्वास्थ्य", "healthy", "good soil", "अच्छी मिट्टी", "स्वास्थ"],
}

def _detect_topics(message: str) -> list[str]:
    low = message.lower()
    return [topic for topic, words in _KEYWORDS.items() if any(w in low for w in words)]


def _soil_summary_lines(soil: dict, lang: dict) -> list[str]:
    """Return plain-language bullet lines about what's in the soil."""
    lines = []
    ph = soil.get("ph")
    if ph is not None:
        if 6.0 <= float(ph) <= 7.5:
            lines.append(lang["ph_good"].format(v=ph))
        elif float(ph) < 6.0:
            lines.append(lang["ph_low"].format(v=ph))
        else:
            lines.append(lang["ph_high"].format(v=ph))

    n = soil.get("nitrogen")
    if n is not None and float(n) < 40:
        lines.append(lang["n_low"].format(v=n))

    p = soil.get("phosphorus")
    if p is not None and float(p) < 25:
        lines.append(lang["p_low"].format(v=p))

    k = soil.get("potassium")
    if k is not None and float(k) < 40:
        lines.append(lang["k_low"].format(v=k))

    ec = soil.get("ec")
    if ec is not None and float(ec) > 4.0:
        lines.append(lang["ec_high"].format(v=ec))

    oc = soil.get("organic_carbon")
    if oc is not None and float(oc) < 0.5:
        lines.append(lang["oc_low"].format(v=oc))

    return lines


def _format_soil_block(soil: dict, lang: dict) -> str:
    pairs = [
        (lang["ph_label"],       soil.get("ph"),              lang["unit_ph"]),
        (lang["n_label"],        soil.get("nitrogen"),        lang["unit_n"]),
        (lang["p_label"],        soil.get("phosphorus"),      lang["unit_p"]),
        (lang["k_label"],        soil.get("potassium"),       lang["unit_k"]),
        (lang["ec_label"],       soil.get("ec"),              lang["unit_ec"]),
        (lang["moisture_label"], soil.get("moisture"),        lang["unit_moisture"]),
        (lang["temp_label"],     soil.get("temperature"),     lang["unit_temp"]),
        (lang["oc_label"],       soil.get("organic_carbon"),  lang["unit_oc"]),
    ]
    return ", ".join(
        f"{label}: {val}{' ' + unit if unit else ''}"
        for label, val, unit in pairs if val is not None
    )


def answer(message: str, soil: dict | None = None, language: str = "en"):
    """
    Generate a farmer-friendly, language-aware response using RAG + soil data.
    """
    lang = _LANG.get(language, _LANG["en"])
    q = message.strip()

    # RAG retrieval
    retrieved = get_rag().retrieve(q, top_k=3)

    # Handle greet / empty
    low = q.lower()
    if low in ("hi", "hello", "namaste", "नमस्ते", "hola", "hey", "kem cho", "kemu cho") or len(q) < 4:
        return lang["greet"], []

    # No soil data
    if not soil:
        reply = lang["no_soil"]
        if retrieved:
            kb_bits = "\n".join(f"• {c.text[:200]}" for c in retrieved[:2])
            reply += lang["knowledge_intro"] + kb_bits
        reply += lang["tip_footer"]
        return reply, [c.source for c in retrieved]

    topics = _detect_topics(q)
    soil_block = _format_soil_block(soil, lang)
    advice_lines = _soil_summary_lines(soil, lang)

    # ── Build targeted reply ─────────────────────────────────────────────────
    lines: list[str] = []

    if "ph" in topics:
        ph = soil.get("ph")
        if ph is not None:
            if 6.0 <= float(ph) <= 7.5:
                lines.append(lang["ph_good"].format(v=ph))
            elif float(ph) < 6.0:
                lines.append(lang["ph_low"].format(v=ph))
            else:
                lines.append(lang["ph_high"].format(v=ph))

    if "fertilizer" in topics:
        n = soil.get("nitrogen"); p = soil.get("phosphorus"); k = soil.get("potassium")
        lows = []
        if n is not None and float(n) < 40: lows.append(lang["n_label"])
        if p is not None and float(p) < 25: lows.append(lang["p_label"])
        if k is not None and float(k) < 40: lows.append(lang["k_label"])
        if lows:
            if language == "hi":
                lines.append(f"आपकी मिट्टी में {', '.join(lows)} कम है।")
            elif language == "gu":
                lines.append(f"આપની માટીમાં {', '.join(lows)} ઓછો છે.")
            elif language == "mr":
                lines.append(f"तुमच्या मातीत {', '.join(lows)} कमी आहे.")
            else:
                lines.append(f"Your soil shows low levels of: {', '.join(lows)}.")

    if "crop" in topics:
        if language == "hi":
            lines.append("फसल चुनाव के लिए 'फसल सुझाव' पृष्ठ देखें। वहाँ आपकी मिट्टी के अनुसार सर्वोत्तम फसलें दिखती हैं।")
        elif language == "gu":
            lines.append("'પાક ભલામણ' પૃષ્ઠ જુઓ — ત્યાં આપની માટી પ્રમાણે શ્રેષ્ઠ પાક બતાવવામાં આવ્યા છે.")
        elif language == "mr":
            lines.append("'पीक शिफारसी' पेजवर जा — तिथे तुमच्या मातीनुसार सर्वोत्तम पिके दाखवली आहेत.")
        else:
            lines.append("Check the 'Crop Recommendations' page — it shows the best crops for your exact soil values.")

    if "moisture" in topics or "salinity" in topics:
        for l in advice_lines:
            if "Moisture" in l or "moisture" in l or "EC" in l or "salt" in l.lower() or "नमी" in l or "नमक" in l or "મીઠ" in l or "मीठ" in l:
                lines.append(l)

    if "organic" in topics:
        oc = soil.get("organic_carbon")
        if oc is not None and float(oc) < 0.5:
            lines.append(lang["oc_low"].format(v=oc))

    # If nothing specific matched, show all soil advice
    if not lines:
        lines = advice_lines if advice_lines else [f"{lang['soil_prefix']}: {soil_block}"]

    reply = "\n".join(lines)

    # Add RAG knowledge context (trimmed, plain)
    if retrieved:
        kb_snippet = "\n".join(f"• {c.text[:220]}" for c in retrieved[:2])
        reply += lang["knowledge_intro"] + kb_snippet

    reply += lang["tip_footer"]
    return reply, [c.source for c in retrieved]
