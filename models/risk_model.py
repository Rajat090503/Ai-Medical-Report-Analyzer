def predict_health_risk(report):

    score = 0

    if "INR" in report:

        inr = float(report["INR"]["value"])

        if inr < 2:
            score += 1

        elif inr <= 3:
            score += 0

        else:
            score += 3

    if "Glucose Fasting" in report:

        sugar = float(report["Glucose Fasting"]["value"])

        if sugar <= 99:
            score += 0

        elif sugar <= 125:
            score += 2

        else:
            score += 4

    if "Random Blood Sugar" in report:

        sugar = float(report["Random Blood Sugar"]["value"])

        if sugar <= 140:
            score += 0

        elif sugar <= 200:
            score += 2

        else:
            score += 4

    if "Creatinine" in report:

        creat = float(report["Creatinine"]["value"])

        if creat > 1.3:
            score += 2

    if "Hemoglobin" in report:

        hb = float(report["Hemoglobin"]["value"])

        if hb < 10:
            score += 2

    # Risk Calculation

    if score <= 1:

        risk = "Low Risk"
        confidence = 95 - (score * 3)
        health_score = 95 - (score * 5)

    elif score <= 4:

        risk = "Medium Risk"
        confidence = 85 - ((score - 2) * 4)
        health_score = 80 - ((score - 2) * 5)

    else:

        risk = "High Risk"
        confidence = min(95, 80 + score)
        health_score = max(20, 60 - (score * 4))

    confidence = round(confidence, 1)
    health_score = round(health_score)

    return risk, confidence, health_score