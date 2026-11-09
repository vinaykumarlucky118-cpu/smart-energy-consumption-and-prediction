"""
EnerSense – Smart Energy Intelligence Platform
Energy Calculation Utilities + AI Energy Advisor Engine
Physics-based, rule-based, and ML computation engine.
"""

import re
from datetime import datetime

# ========================= DEFAULT APPLIANCE DATABASE =========================

DEFAULT_APPLIANCES = [
    {'name': 'Ceiling Fan', 'power_watts': 75, 'icon': 'fa-fan'},
    {'name': 'LED Light', 'power_watts': 10, 'icon': 'fa-lightbulb'},
    {'name': 'Tube Light', 'power_watts': 40, 'icon': 'fa-lightbulb'},
    {'name': 'Television (LED 40")', 'power_watts': 120, 'icon': 'fa-tv'},
    {'name': 'Refrigerator (250L)', 'power_watts': 200, 'icon': 'fa-snowflake'},
    {'name': 'Air Conditioner (1.5T)', 'power_watts': 1500, 'icon': 'fa-wind'},
    {'name': 'Air Conditioner (1T)', 'power_watts': 1000, 'icon': 'fa-wind'},
    {'name': 'Air Cooler', 'power_watts': 200, 'icon': 'fa-wind'},
    {'name': 'Washing Machine', 'power_watts': 500, 'icon': 'fa-shirt'},
    {'name': 'Desktop Computer', 'power_watts': 300, 'icon': 'fa-desktop'},
    {'name': 'Laptop', 'power_watts': 65, 'icon': 'fa-laptop'},
    {'name': 'Water Heater (Geyser)', 'power_watts': 2000, 'icon': 'fa-fire'},
    {'name': 'Microwave Oven', 'power_watts': 1200, 'icon': 'fa-utensils'},
    {'name': 'Iron', 'power_watts': 1000, 'icon': 'fa-iron'},
    {'name': 'Hair Dryer', 'power_watts': 1200, 'icon': 'fa-wind'},
    {'name': 'WiFi Router', 'power_watts': 12, 'icon': 'fa-wifi'},
    {'name': 'Phone Charger', 'power_watts': 20, 'icon': 'fa-mobile'},
    {'name': 'Mixer / Grinder', 'power_watts': 750, 'icon': 'fa-blender'},
    {'name': 'Water Pump (0.5HP)', 'power_watts': 375, 'icon': 'fa-tint'},
    {'name': 'Electric Kettle', 'power_watts': 1500, 'icon': 'fa-mug-hot'},
    {'name': 'Induction Cooktop', 'power_watts': 1800, 'icon': 'fa-utensils'},
]

# ========================= PHYSICS CALCULATIONS =========================

def calculate_power_kw(voltage, current):
    """P = V × I (Watts) → converted to kW."""
    return round((voltage * current) / 1000.0, 3)

def calculate_energy_kwh(power_kw, hours):
    """E = P × t (kWh)."""
    return round(power_kw * hours, 2)

def calculate_appliance_energy(power_watts, quantity, hours_per_day):
    """Calculate daily and monthly energy for an appliance.
    Energy (kWh) = Power (W) × Quantity × Hours / 1000
    """
    daily_kwh = round((power_watts * quantity * hours_per_day) / 1000.0, 3)
    monthly_kwh = round(daily_kwh * 30, 2)
    return daily_kwh, monthly_kwh

def calculate_bill(energy_kwh, tariff_rate):
    """Estimated Bill = Energy × Tariff Rate."""
    return round(energy_kwh * tariff_rate, 2)

def calculate_co2_emissions(energy_kwh, emission_factor=0.82):
    """Convert kWh to estimated CO₂ emissions in kg.
    Default factor: 0.82 kg CO₂/kWh (India grid average estimate).
    Note: This is an approximate emission factor and varies by region/source.
    """
    return round(energy_kwh * emission_factor, 2)

# ========================= ENERGY SCORE =========================

def calculate_energy_score(predicted_kwh, usage_hours, num_appliances, temperature, thresholds=None):
    """
    Calculate an Energy Efficiency Score (0-100).
    Higher score = more efficient usage.

    Factors:
    - Consumption vs thresholds (40 pts max)
    - Usage hours efficiency (25 pts max)
    - Appliance density (20 pts max)
    - Temperature awareness (15 pts max)
    """
    if thresholds is None:
        thresholds = {'low': 11.35, 'high': 23.02}

    low_th = thresholds.get('low', 11.35)
    high_th = thresholds.get('high', 23.02)
    max_expected = high_th * 2

    # Consumption factor (0-40 points)
    if predicted_kwh <= low_th:
        consumption_score = 40
    elif predicted_kwh <= high_th:
        consumption_score = 40 - (predicted_kwh - low_th) / (high_th - low_th) * 20
    else:
        consumption_score = max(0, 20 - (predicted_kwh - high_th) / (max_expected - high_th) * 20)

    # Usage hours factor (0-25 points)
    if usage_hours <= 4:
        hours_score = 25
    elif usage_hours <= 8:
        hours_score = 25 - (usage_hours - 4) / 4 * 10
    elif usage_hours <= 16:
        hours_score = 15 - (usage_hours - 8) / 8 * 10
    else:
        hours_score = max(0, 5 - (usage_hours - 16) / 8 * 5)

    # Appliance factor (0-20 points)
    if num_appliances <= 3:
        appliance_score = 20
    elif num_appliances <= 6:
        appliance_score = 20 - (num_appliances - 3) / 3 * 8
    elif num_appliances <= 10:
        appliance_score = 12 - (num_appliances - 6) / 4 * 6
    else:
        appliance_score = max(0, 6 - (num_appliances - 10) / 10 * 6)

    # Temperature awareness (0-15 points)
    if 18 <= temperature <= 26:
        temp_score = 15
    elif 14 <= temperature <= 32:
        temp_score = 10
    else:
        temp_score = 5

    total = int(round(min(100, max(0, consumption_score + hours_score + appliance_score + temp_score))))

    if total >= 80:
        status = 'Excellent'
        color = '#10b981'
    elif total >= 60:
        status = 'Good'
        color = '#6366f1'
    elif total >= 40:
        status = 'Average'
        color = '#f59e0b'
    else:
        status = 'Needs Improvement'
        color = '#ef4444'

    return {
        'score': total,
        'status': status,
        'color': color,
        'breakdown': {
            'consumption': round(consumption_score, 1),
            'usage_hours': round(hours_score, 1),
            'appliances': round(appliance_score, 1),
            'temperature': round(temp_score, 1)
        }
    }

# ========================= CONSUMPTION CLASSIFICATION =========================

def classify_consumption(predicted_kwh, thresholds=None):
    """Classify consumption into LOW, NORMAL, or HIGH based on model thresholds."""
    if thresholds is None:
        thresholds = {'low': 11.35, 'high': 23.02}
    low_th = thresholds.get('low', 11.35)
    high_th = thresholds.get('high', 23.02)

    if predicted_kwh < low_th:
        return 'LOW', '#10b981', 'Efficient Usage'
    elif predicted_kwh <= high_th:
        return 'NORMAL', '#6366f1', 'Balanced Consumption'
    else:
        return 'HIGH', '#ef4444', 'High Load Demand'

# ========================= RECOMMENDATIONS ENGINE =========================

def generate_recommendations(predicted_kwh, level, voltage, current, usage_hours, appliances, temperature, previous_kwh):
    """Generate dynamic, intelligent energy saving tips based on parameters."""
    tips = []
    p_kw = (voltage * current) / 1000.0

    if level == 'LOW':
        tips.append({
            'text': 'Your energy consumption is low and efficient. Maintain your current conservation habits.',
            'reason': f'Predicted consumption ({predicted_kwh:.1f} kWh) is below the efficiency threshold of {11.35:.1f} kWh.',
            'impact': 'Keep it up!',
            'icon': 'fa-leaf',
            'type': 'positive'
        })
        if appliances > 6:
            tips.append({
                'text': 'Consider turning off standby power for unused appliances to save additional energy.',
                'reason': f'You have {appliances} active appliances. Standby power can account for 5–10% of total usage.',
                'impact': 'Save ~5%',
                'icon': 'fa-plug',
                'type': 'suggestion'
            })
        if usage_hours > 10:
            tips.append({
                'text': 'Consider using smart timers or smart plugs to automatically switch off appliances when not needed.',
                'reason': f'Your appliances run {usage_hours:.1f} hours/day. Automation can reduce idle runtime.',
                'impact': 'Save 5–10%',
                'icon': 'fa-clock',
                'type': 'suggestion'
            })
    elif level == 'NORMAL':
        tips.append({
            'text': 'Your energy consumption is within normal limits. Small improvements can push you to the efficient range.',
            'reason': f'Predicted consumption is {predicted_kwh:.1f} kWh — moderate and manageable.',
            'impact': 'Stable',
            'icon': 'fa-check-circle',
            'type': 'positive'
        })
        if temperature > 30.0:
            saving_est = round(predicted_kwh * 0.15, 1)
            tips.append({
                'text': f'Ambient temperature is warm ({temperature}°C). Setting AC to 24–26°C reduces cooling load significantly.',
                'reason': 'Higher ambient temperatures force cooling appliances to work harder, consuming more electricity.',
                'impact': f'Could save ~{saving_est} kWh',
                'icon': 'fa-temperature-high',
                'type': 'warning'
            })
        if usage_hours > 8.0:
            tips.append({
                'text': f'Appliances run for {usage_hours:.1f} hrs/day. Use programmable timers to reduce idle running time.',
                'reason': 'Longer runtime proportionally increases energy consumption (E = P × t).',
                'impact': 'Reduce runtime by 1–2 hrs to save 10–20%',
                'icon': 'fa-clock',
                'type': 'suggestion'
            })
        if appliances >= 5:
            tips.append({
                'text': 'Unplug chargers and small devices when not in use to eliminate phantom loads.',
                'reason': 'Phantom loads from multiple devices collectively account for 5–10% of household energy.',
                'impact': 'Save 5–10%',
                'icon': 'fa-plug',
                'type': 'suggestion'
            })
    else:  # HIGH
        tips.append({
            'text': 'High energy consumption detected! A systematic review of your usage is strongly recommended.',
            'reason': f'Predicted consumption ({predicted_kwh:.1f} kWh) exceeds the high-consumption threshold.',
            'impact': 'Immediate action recommended',
            'icon': 'fa-exclamation-triangle',
            'type': 'critical'
        })
        if usage_hours > 10.0:
            saving_hours = round(usage_hours * 0.2, 1)
            saving_kwh = round(p_kw * saving_hours, 2)
            tips.append({
                'text': f'Excessive daily runtime ({usage_hours:.1f} hrs). Reducing by {saving_hours:.1f} hrs/day could save ~{saving_kwh:.2f} kWh.',
                'reason': 'Runtime is the primary driver of energy consumption in most households.',
                'impact': f'Save ~{saving_kwh} kWh/day',
                'icon': 'fa-clock',
                'type': 'critical'
            })
        if current > 10.0:
            tips.append({
                'text': f'Heavy load current detected ({current:.1f}A, ~{p_kw:.2f} kW). Stagger high-wattage equipment usage.',
                'reason': 'Running multiple high-power appliances simultaneously increases peak demand charges.',
                'impact': 'Reduce peak load and avoid surge costs',
                'icon': 'fa-bolt',
                'type': 'warning'
            })
        if temperature > 32.0:
            tips.append({
                'text': f'High ambient temperature ({temperature:.1f}°C). Clean HVAC filters and use ceiling fans to supplement AC.',
                'reason': 'Every 1°C increase in AC setpoint above 24°C reduces cooling energy by ~6%.',
                'impact': 'Improve cooling efficiency by 15–25%',
                'icon': 'fa-temperature-high',
                'type': 'warning'
            })
        if appliances > 8:
            tips.append({
                'text': f'High appliance density ({appliances} units). Upgrade to BEE 5-star rated energy-efficient models.',
                'reason': 'More appliances increase baseline consumption even on standby.',
                'impact': 'Long-term savings of 20–40%',
                'icon': 'fa-star',
                'type': 'suggestion'
            })
        if previous_kwh < (predicted_kwh * 0.75):
            increase_pct = round((predicted_kwh - previous_kwh) / max(0.1, previous_kwh) * 100, 1)
            tips.append({
                'text': f'Consumption surged ~{increase_pct}% vs previous ({previous_kwh:.1f} kWh). Check for equipment malfunction or leaks.',
                'reason': 'Sudden large increases often indicate faulty insulation, refrigerant leaks, or equipment problems.',
                'impact': 'Investigate immediately',
                'icon': 'fa-arrow-trend-up',
                'type': 'critical'
            })

    return tips

def generate_recommendation_string(tips):
    """Convert structured tips to a pipe-delimited string for database storage."""
    return " | ".join([t['text'] for t in tips])

# ========================= AI INSIGHTS ENGINE =========================

def generate_insights(predictions, profile=None, appliances_data=None):
    """
    Generate rule-based AI insights from user energy data.
    These are computed from actual data, not from a generative model.
    """
    insights = []

    if not predictions:
        return [{
            'text': 'No prediction data available yet. Run your first energy prediction to get personalized insights.',
            'icon': 'fa-info-circle',
            'type': 'info'
        }]

    # Trend analysis
    if len(predictions) >= 3:
        recent_3 = [p['predicted_consumption'] for p in predictions[-3:]]
        if all(recent_3[i] < recent_3[i+1] for i in range(len(recent_3)-1)):
            avg_increase = round((recent_3[-1] - recent_3[0]) / max(0.1, recent_3[0]) * 100, 1)
            insights.append({
                'text': f'Your energy consumption has been increasing over your last 3 predictions (up ~{avg_increase}%). Consider reviewing which appliances you are running.',
                'icon': 'fa-arrow-trend-up',
                'type': 'warning'
            })
        elif all(recent_3[i] > recent_3[i+1] for i in range(len(recent_3)-1)):
            avg_decrease = round((recent_3[0] - recent_3[-1]) / max(0.1, recent_3[0]) * 100, 1)
            insights.append({
                'text': f'Great progress! Your energy consumption has been decreasing over your last 3 predictions (down ~{avg_decrease}%). Your conservation efforts are working.',
                'icon': 'fa-arrow-trend-down',
                'type': 'positive'
            })

    # Usage hours insight
    avg_hours = sum(p.get('usage_hours', 0) for p in predictions) / max(1, len(predictions))
    if avg_hours > 10:
        insights.append({
            'text': f'Your average daily appliance runtime is {avg_hours:.1f} hours — a primary driver of your energy consumption. Reducing by just 1–2 hours could yield measurable savings.',
            'icon': 'fa-clock',
            'type': 'suggestion'
        })

    # Temperature pattern
    temps = [p.get('temperature', 25) for p in predictions]
    avg_temp = sum(temps) / max(1, len(temps))
    if avg_temp > 32:
        insights.append({
            'text': f'Your average ambient temperature is {avg_temp:.1f}°C, which significantly increases cooling energy demand. Ensure proper insulation and use natural ventilation when possible.',
            'icon': 'fa-temperature-high',
            'type': 'warning'
        })

    # Consumption distribution
    levels = [p.get('consumption_level', 'NORMAL') for p in predictions]
    high_pct = levels.count('HIGH') / max(1, len(levels)) * 100
    if high_pct > 50:
        insights.append({
            'text': f'{high_pct:.0f}% of your predictions fall in the HIGH consumption category. A systematic review of your appliance usage and operating hours could help bring this down significantly.',
            'icon': 'fa-exclamation-circle',
            'type': 'critical'
        })
    elif high_pct == 0 and len(predictions) >= 3:
        insights.append({
            'text': 'All your recent predictions are in the LOW or NORMAL range. You are managing your energy efficiently — keep it up!',
            'icon': 'fa-thumbs-up',
            'type': 'positive'
        })

    # Budget insight
    if profile:
        budget = profile.get('monthly_budget', 2000)
        tariff = profile.get('tariff_rate', 6.0)
        if predictions:
            latest_kwh = predictions[-1].get('predicted_consumption', 0)
            est_monthly = latest_kwh * 30
            est_cost = est_monthly * tariff
            currency = profile.get('currency', '₹')
            if est_cost > budget:
                overshoot = round(est_cost - budget, 0)
                insights.append({
                    'text': f'Based on your latest prediction, your estimated monthly bill ({currency}{est_cost:.0f}) may exceed your budget ({currency}{budget:.0f}) by {currency}{overshoot:.0f}. Consider reducing high-consumption periods.',
                    'icon': 'fa-wallet',
                    'type': 'warning'
                })

    # Appliance count insight
    avg_appliances = sum(p.get('number_of_appliances', 0) for p in predictions) / max(1, len(predictions))
    if avg_appliances > 8:
        insights.append({
            'text': f'You typically run {avg_appliances:.0f} appliances simultaneously. Consider switching to BEE 5-star rated appliances for long-term energy savings of 20–40%.',
            'icon': 'fa-star',
            'type': 'suggestion'
        })

    if not insights:
        insights.append({
            'text': 'Your energy usage appears balanced and efficient. Continue monitoring regularly to maintain efficiency.',
            'icon': 'fa-check-circle',
            'type': 'positive'
        })

    return insights

# ========================= SMART ALERTS =========================

def generate_alerts(predicted_kwh, profile, thresholds=None):
    """Generate contextual alerts based on consumption and budget."""
    alerts = []
    if thresholds is None:
        thresholds = {'low': 11.35, 'high': 23.02}

    level, _, _ = classify_consumption(predicted_kwh, thresholds)

    if level == 'HIGH':
        alerts.append({
            'type': 'danger',
            'icon': '⚠',
            'title': 'High Consumption Alert',
            'message': f'Your estimated usage ({predicted_kwh:.1f} kWh) is higher than the normal pattern. Review your appliance usage and operating hours.'
        })

    if profile:
        budget = profile.get('monthly_budget', 2000)
        tariff = profile.get('tariff_rate', 6.0)
        currency = profile.get('currency', '₹')
        est_monthly_cost = predicted_kwh * 30 * tariff

        if est_monthly_cost > budget:
            alerts.append({
                'type': 'warning',
                'icon': '💰',
                'title': 'Budget Alert',
                'message': f'Your estimated monthly bill ({currency}{est_monthly_cost:.0f}) may exceed your budget of {currency}{budget:.0f}. Consider reducing usage during peak hours.'
            })
        elif est_monthly_cost > budget * 0.8:
            alerts.append({
                'type': 'info',
                'icon': '📊',
                'title': 'Budget Watch',
                'message': f'You are using {est_monthly_cost/budget*100:.0f}% of your monthly energy budget ({currency}{est_monthly_cost:.0f} of {currency}{budget:.0f}).'
            })

    if level == 'LOW':
        alerts.append({
            'type': 'success',
            'icon': '🌱',
            'title': 'Energy Efficient',
            'message': 'Your consumption is within the efficient range. Keep up the excellent work!'
        })

    return alerts

# ========================= TARIFF SLABS =========================

TARIFF_SLABS = {
    'flat': {
        'name': 'Flat Rate',
        'description': 'Single uniform rate applied to all units consumed',
        'calculate': lambda kwh, rate: round(kwh * rate, 2)
    },
    'slab_residential': {
        'name': 'Residential Slab (Example)',
        'description': 'Tiered pricing: lower rates for low usage, higher rates as consumption increases',
        'slabs': [
            {'limit': 100, 'label': '0 – 100 units', 'rate': 3.5},
            {'limit': 200, 'label': '101 – 200 units', 'rate': 5.5},
            {'limit': float('inf'), 'label': 'Above 200 units', 'rate': 7.5}
        ]
    },
    'slab_commercial': {
        'name': 'Commercial Slab (Example)',
        'description': 'Higher tiered pricing for commercial / business premises',
        'slabs': [
            {'limit': 200, 'label': '0 – 200 units', 'rate': 6.0},
            {'limit': 500, 'label': '201 – 500 units', 'rate': 8.0},
            {'limit': float('inf'), 'label': 'Above 500 units', 'rate': 10.0}
        ]
    }
}

def calculate_slab_bill(energy_kwh, slab_type='flat', flat_rate=6.0):
    """Calculate bill using slab or flat tariff."""
    if slab_type == 'flat':
        return round(energy_kwh * flat_rate, 2), [{'units': energy_kwh, 'rate': flat_rate, 'cost': round(energy_kwh * flat_rate, 2)}]

    slab = TARIFF_SLABS.get(slab_type, TARIFF_SLABS['flat'])
    if 'slabs' not in slab:
        return round(energy_kwh * flat_rate, 2), [{'units': energy_kwh, 'rate': flat_rate, 'cost': round(energy_kwh * flat_rate, 2)}]

    remaining = energy_kwh
    total_bill = 0
    breakdown = []
    prev_limit = 0

    for s in slab['slabs']:
        slab_limit = s['limit'] - prev_limit
        units_in_slab = min(remaining, slab_limit)
        cost = round(units_in_slab * s['rate'], 2)
        if units_in_slab > 0:
            breakdown.append({
                'range': f'{prev_limit}–{min(s["limit"], prev_limit + units_in_slab):.0f}' if s['limit'] != float('inf') else f'{prev_limit}+',
                'units': round(units_in_slab, 2),
                'rate': s['rate'],
                'cost': cost
            })
        total_bill += cost
        remaining -= units_in_slab
        prev_limit = s['limit']
        if remaining <= 0:
            break

    return round(total_bill, 2), breakdown


# ========================= AI ENERGY ADVISOR ENGINE =========================

class EnergyAdvisorEngine:
    """
    Rule-based AI Energy Advisor for EnerSense.
    Provides personalized energy advice based on user data and questions.
    Falls back gracefully when user data is not available.
    Optional: Use Gemini API if GEMINI_API_KEY is set in environment.
    """

    def __init__(self, user_profile=None, recent_predictions=None):
        self.profile = user_profile or {}
        self.predictions = recent_predictions or []
        self.tariff = self.profile.get('tariff_rate', 6.0)
        self.budget = self.profile.get('monthly_budget', 2000)
        self.currency = self.profile.get('currency', '₹')
        self.emission_factor = self.profile.get('emission_factor', 0.82)
        self.home_type = self.profile.get('home_type', 'Apartment')
        self.num_people = self.profile.get('num_people', 2)

    def _get_latest_kwh(self):
        """Get the latest predicted consumption."""
        if self.predictions:
            return self.predictions[0].get('predicted_consumption', 0)
        return None

    def _get_avg_kwh(self):
        """Get average consumption across all predictions."""
        if self.predictions:
            vals = [p.get('predicted_consumption', 0) for p in self.predictions]
            return round(sum(vals) / len(vals), 2)
        return None

    def answer(self, question: str) -> dict:
        """
        Answer an energy-related question.
        Returns: {'answer': str, 'topic': str}
        """
        q = question.lower().strip()

        # --- GREETINGS ---
        if any(w in q for w in ['hello', 'hi', 'hey', 'namaste', 'good morning', 'good evening']):
            name = self.profile.get('name', 'there') if self.profile else 'there'
            return {
                'answer': f"Hello! 👋 I'm your EnerSense Energy Advisor. I can help you understand your electricity consumption, estimate bills, suggest ways to save energy, and answer questions about your appliances. What would you like to know?",
                'topic': 'greeting'
            }

        # --- BILL QUESTIONS ---
        if any(w in q for w in ['bill', 'cost', 'charge', 'expensive', 'rupee', 'money', 'pay', 'invoice']):
            return self._answer_bill_question(q)

        # --- kWh / UNITS EXPLANATION ---
        if any(w in q for w in ['kwh', 'kilowatt', 'unit', 'what is energy', 'how is energy measured']):
            return self._answer_kwh_question(q)

        # --- AC / COOLING ---
        if any(w in q for w in ['ac', 'air conditioner', 'air conditioning', 'cooling', 'hvac', 'inverter ac', 'split ac']):
            return self._answer_ac_question(q)

        # --- APPLIANCE QUESTIONS ---
        if any(w in q for w in ['appliance', 'refrigerator', 'fridge', 'washing machine', 'geyser', 'heater', 'fan', 'tv', 'television', 'microwave', 'computer', 'laptop', 'light', 'led', 'tube']):
            return self._answer_appliance_question(q)

        # --- SAVING TIPS ---
        if any(w in q for w in ['save', 'saving', 'reduce', 'cut', 'lower', 'decrease', 'tips', 'advice', 'improve', 'efficient', 'efficiency']):
            return self._answer_savings_question(q)

        # --- SOLAR ---
        if any(w in q for w in ['solar', 'panel', 'renewable', 'rooftop', 'pv', 'photovoltaic']):
            return self._answer_solar_question(q)

        # --- CARBON / CO2 ---
        if any(w in q for w in ['carbon', 'co2', 'emission', 'footprint', 'environment', 'green', 'climate', 'pollution']):
            return self._answer_carbon_question(q)

        # --- SCORE ---
        if any(w in q for w in ['score', 'rating', 'grade', 'efficiency score', 'energy score']):
            return self._answer_score_question(q)

        # --- PEAK HOURS ---
        if any(w in q for w in ['peak', 'off-peak', 'time of day', 'when to use', 'night', 'morning', 'evening', 'schedule']):
            return self._answer_peak_hours_question(q)

        # --- TARIFF / SLAB ---
        if any(w in q for w in ['tariff', 'slab', 'rate', 'per unit', 'electricity rate', 'how much per kwh']):
            return self._answer_tariff_question(q)

        # --- PREDICTION ---
        if any(w in q for w in ['predict', 'forecast', 'estimate', 'ml', 'machine learning', 'model', 'random forest']):
            return self._answer_prediction_question(q)

        # --- MY CONSUMPTION ---
        if any(w in q for w in ['my usage', 'my consumption', 'how much do i use', 'my data', 'my prediction', 'how am i doing']):
            return self._answer_my_consumption(q)

        # --- GENERAL / FALLBACK ---
        return self._answer_general(q)

    def _answer_bill_question(self, q):
        latest = self._get_latest_kwh()
        if latest:
            monthly_kwh = round(latest * 30, 1)
            est_bill = round(monthly_kwh * self.tariff, 0)
            answer = (
                f"📝 **Your Bill Estimate:**\n\n"
                f"Based on your latest prediction of **{latest:.2f} kWh/day**, your estimated monthly consumption is **{monthly_kwh} kWh**.\n\n"
                f"At your configured tariff rate of **{self.currency}{self.tariff}/kWh**, your estimated monthly bill is **{self.currency}{est_bill:.0f}**.\n\n"
                f"**To reduce your bill:**\n"
                f"• Run high-wattage appliances (AC, geyser) during cooler hours\n"
                f"• Replace old appliances with BEE 5-star rated models\n"
                f"• Set AC thermostat to 24°C (saves ~6% per degree)\n"
                f"• Unplug devices on standby — they silently consume power\n\n"
                f"💡 Use the **Bill Estimator** tool for detailed slab-based calculations!"
            )
        else:
            answer = (
                f"📝 **How Your Electricity Bill Works:**\n\n"
                f"Your electricity bill = Units consumed (kWh) × Tariff rate (₹/kWh)\n\n"
                f"Most states in India use **slab-based tariffs** where the rate increases as you consume more:\n"
                f"• 0–100 units: ₹3.5/unit (low rate)\n"
                f"• 101–200 units: ₹5.5/unit (medium rate)\n"
                f"• 200+ units: ₹7.5/unit (high rate)\n\n"
                f"**Tips to lower your bill:**\n"
                f"• Stay in the first slab (< 100 units/month) for the lowest rate\n"
                f"• Use the Bill Estimator to calculate exactly what you owe\n"
                f"• Make a prediction first to see your personalized estimates!"
            )
        return {'answer': answer, 'topic': 'billing'}

    def _answer_kwh_question(self, q):
        answer = (
            "⚡ **What is a kWh (Kilowatt-hour)?**\n\n"
            "A **kilowatt-hour (kWh)** is the standard unit of electricity measurement — what you see on your electricity bill as 'units'.\n\n"
            "**Formula:** 1 kWh = 1,000 Watts running for 1 hour\n\n"
            "**Real Examples:**\n"
            "• A 100W bulb running for 10 hours = **1 kWh**\n"
            "• A 1.5-ton AC (1500W) running for 1 hour = **1.5 kWh**\n"
            "• A refrigerator (200W) running 24 hours = **4.8 kWh/day**\n\n"
            "**Physics behind it:**\n"
            "P = V × I (Power = Voltage × Current)\n"
            "E = P × t (Energy = Power × Time)\n\n"
            "This is why EnerSense asks for Voltage (V), Current (A), and Usage Hours — together they calculate your energy usage!"
        )
        return {'answer': answer, 'topic': 'education'}

    def _answer_ac_question(self, q):
        answer = (
            "❄️ **Air Conditioner Energy Guide:**\n\n"
            "ACs are typically the **largest energy consumer** in Indian homes, often accounting for 40–60% of the summer electricity bill.\n\n"
            "**AC Energy by Capacity:**\n"
            "• 1-ton AC (non-inverter): ~1,000W = 1 kWh/hour\n"
            "• 1.5-ton AC (non-inverter): ~1,500W = 1.5 kWh/hour\n"
            "• 1.5-ton AC (5-star inverter): ~900W = 0.9 kWh/hour\n\n"
            "**Running 8 hours/day (30 days):**\n"
            "• Non-inverter 1.5T: 1500 × 8 × 30 / 1000 = **360 kWh/month** (~₹2,160)\n"
            "• 5-star inverter 1.5T: ~216 kWh/month (~₹1,296) — saves ₹864!\n\n"
            "**Key Saving Tips:**\n"
            "✅ Set temperature to **24°C** (not 18°C!) — each 1°C increase saves ~6% energy\n"
            "✅ Use **sleep mode** at night — temperature auto-adjusts\n"
            "✅ Clean filters monthly — dirty filters increase energy use by 10–15%\n"
            "✅ Use ceiling fans with AC to distribute cool air\n"
            "✅ Keep curtains/blinds closed during daytime heat\n"
            "✅ Consider upgrading to **5-star inverter AC** for 30–40% savings"
        )
        return {'answer': answer, 'topic': 'appliances'}

    def _answer_appliance_question(self, q):
        lines = []
        if 'fridge' in q or 'refrigerator' in q:
            lines = [
                "🧊 **Refrigerator Energy Guide:**",
                "• Average fridge (250L): **150–200W** = ~4–5 kWh/day (always on)",
                "• Monthly: ~120–150 kWh (~₹720–900 at ₹6/unit)",
                "**Tips:** Set temperature to 4°C (fridge) & -18°C (freezer). Keep coils clean. Don't put hot food directly inside."
            ]
        elif 'washing' in q or 'washer' in q:
            lines = [
                "🫧 **Washing Machine Energy Guide:**",
                "• Semi-auto: ~350W | Front-load: ~500W | Top-load: ~450W",
                "• Per wash (45 min): ~0.3–0.5 kWh",
                "**Tips:** Use cold water wash (saves 90% of energy). Run full loads. Choose 5-star rated machines."
            ]
        elif 'geyser' in q or 'heater' in q or 'water heat' in q:
            lines = [
                "🚿 **Water Heater (Geyser) Energy Guide:**",
                "• Storage geyser: **2,000W** — one of the biggest energy users",
                "• 30-min use daily: 1 kWh/day = **30 kWh/month** (~₹180)",
                "**Tips:** Set temperature to 50°C (not 75°C). Install timer. Consider solar water heater for 80% savings!"
            ]
        elif 'fan' in q:
            lines = [
                "💨 **Ceiling Fan Energy Guide:**",
                "• Ceiling fan: 50–75W (very efficient!)",
                "• 10 hours/day: 0.5–0.75 kWh/day = ~15–22 kWh/month",
                "**Tips:** BLDC fans use only 28–35W (50% less than regular). Clean fan blades for optimal airflow."
            ]
        elif 'tv' in q or 'television' in q:
            lines = [
                "📺 **TV Energy Guide:**",
                "• LED 40\": ~80–120W | OLED 55\": ~130–150W",
                "• 4 hrs/day: ~0.4–0.5 kWh/day = ~12–15 kWh/month",
                "**Tips:** Enable auto-brightness. Use energy saving mode. Turn off completely instead of leaving on standby."
            ]
        elif 'light' in q or 'led' in q or 'tube' in q or 'bulb' in q:
            lines = [
                "💡 **Lighting Energy Guide:**",
                "• Old tube light: 40W | LED replacement: 10–18W (60% savings!)",
                "• Old bulb: 60W | LED equivalent: 7–9W (85% savings!)",
                "**Tip:** Replace all lights with LED. 6 bulbs × 6 hrs × ₹6 = only ₹3.60/day with LED!"
            ]
        elif 'computer' in q or 'laptop' in q or 'desktop' in q:
            lines = [
                "💻 **Computer Energy Guide:**",
                "• Laptop: 45–65W | Desktop + monitor: 250–350W",
                "• 8 hrs/day, desktop: ~2.5 kWh/day = 75 kWh/month (~₹450)",
                "**Tips:** Use laptop instead of desktop when possible. Enable power-saving mode. Use sleep mode after 15 min idle."
            ]
        else:
            answer = (
                "🏠 **Common Appliance Power Guide:**\n\n"
                "| Appliance | Power | Monthly (8hrs/day) |\n"
                "|-----------|-------|--------------------|\n"
                "| AC 1.5T | 1,500W | 360 kWh (~₹2,160) |\n"
                "| Geyser | 2,000W | 30 kWh (~₹180) |\n"
                "| Refrigerator | 200W | 144 kWh (~₹864) |\n"
                "| Washing Machine | 500W | 12 kWh (~₹72) |\n"
                "| Ceiling Fan | 75W | 18 kWh (~₹108) |\n"
                "| LED TV | 100W | 24 kWh (~₹144) |\n"
                "| Laptop | 65W | 15.6 kWh (~₹94) |\n"
                "| LED Bulb | 10W | 2.4 kWh (~₹14) |\n\n"
                "Use the **Appliance Calculator** for your exact appliance mix!"
            )
            return {'answer': answer, 'topic': 'appliances'}

        return {'answer': '\n'.join(lines), 'topic': 'appliances'}

    def _answer_savings_question(self, q):
        latest = self._get_latest_kwh()
        tip_intro = ""
        if latest:
            potential = round(latest * 30 * self.tariff * 0.20, 0)
            tip_intro = f"Based on your current usage, you could potentially save **{self.currency}{potential:.0f}/month** with these tips:\n\n"

        answer = (
            f"💡 **Energy Saving Tips:**\n\n"
            f"{tip_intro}"
            f"**🏠 At Home:**\n"
            f"1. Switch to **LED lights** (saves 80% vs incandescent)\n"
            f"2. Set AC to **24°C** instead of 18°C (saves 36% cooling energy)\n"
            f"3. Use **cold water** for laundry (saves 90% of washing machine energy)\n"
            f"4. Unplug chargers and devices on **standby** — they still consume power\n\n"
            f"**⏰ Timing Strategies:**\n"
            f"5. Run dishwasher/washing machine at **off-peak hours** (10pm–6am)\n"
            f"6. Use **timers** on geysers — heat only when needed\n"
            f"7. Pre-cool rooms before sleeping and set AC **sleep mode**\n\n"
            f"**🔧 Equipment:**\n"
            f"8. Service AC and refrigerator coils **annually**\n"
            f"9. Upgrade to **BEE 5-star appliances** when replacing\n"
            f"10. Install **power strips** with on/off switches for entertainment systems\n\n"
            f"**🌿 Bigger Picture:**\n"
            f"11. Install **solar panels** (payback: 5–7 years, free energy after)\n"
            f"12. Add **ceiling insulation** to reduce AC load by 20–30%\n\n"
            f"Use the **Energy Simulator** to calculate exactly how much each change saves you!"
        )
        return {'answer': answer, 'topic': 'savings'}

    def _answer_solar_question(self, q):
        answer = (
            "☀️ **Solar Energy for Your Home:**\n\n"
            "Solar panels convert sunlight to electricity, reducing your grid consumption and electricity bill.\n\n"
            "**System Sizing (India average):**\n"
            "• 1 kW solar = ~4–5 units/day (1,460–1,825 units/year)\n"
            "• 3 kW system: Handles most of a 2BHK apartment's needs\n"
            "• Cost: ~₹2.5–3.5 lakh for 3kW (after PM-KUSUM subsidies)\n\n"
            "**Financial Benefits:**\n"
            "• Save ₹1,500–2,500/month on electricity (3kW system)\n"
            "• Payback period: **5–7 years**\n"
            "• Net metering: Sell surplus power back to the grid\n"
            "• PM Surya Ghar Muft Bijli Yojana: Get 300 free units/month!\n\n"
            "**Is solar right for you?**\n"
            f"Based on your profile, if you consume {self._get_avg_kwh() or 10:.1f} kWh/day, a 2–3 kW system could cover 60–80% of your needs.\n\n"
            "**Next Steps:** Contact a MNRE-approved installer and check state subsidies at your local DISCOM."
        )
        return {'answer': answer, 'topic': 'solar'}

    def _answer_carbon_question(self, q):
        latest = self._get_latest_kwh()
        personal = ""
        if latest:
            daily_co2 = round(latest * self.emission_factor, 2)
            monthly_co2 = round(daily_co2 * 30, 1)
            trees = round(monthly_co2 / 21.7, 1)  # avg tree absorbs ~21.7 kg CO2/year = 1.8/month
            personal = (
                f"\n\n**Your Carbon Footprint:**\n"
                f"• Daily: {daily_co2:.2f} kg CO₂\n"
                f"• Monthly: {monthly_co2:.1f} kg CO₂\n"
                f"• Equivalent to {trees:.1f} trees needed to offset (annual absorption)\n"
                f"• Emission factor used: {self.emission_factor} kg CO₂/kWh (India grid average)"
            )

        answer = (
            "🌿 **Carbon Footprint from Electricity:**\n\n"
            "Every unit of electricity you consume generates CO₂ at your power plant (mostly coal in India).\n\n"
            "**India's Grid Emission Factor:**\n"
            "• Average: **0.82 kg CO₂ per kWh** (Central Electricity Authority, India)\n"
            "• This varies by state: renewable-heavy states like Karnataka are lower\n\n"
            "**Context:**\n"
            "• 100 kWh/month → 82 kg CO₂/month → 984 kg CO₂/year\n"
            "• A single 2,000 km flight: ~200–300 kg CO₂ per person\n\n"
            "**Reduce Your Carbon Footprint:**\n"
            "✅ Switch to solar (zero emissions electricity)\n"
            "✅ Buy BEE 5-star appliances (less energy = less CO₂)\n"
            "✅ Use LEDs and turn off lights when leaving\n"
            "✅ Line-dry clothes instead of using a dryer"
            f"{personal}"
        )
        return {'answer': answer, 'topic': 'carbon'}

    def _answer_score_question(self, q):
        answer = (
            "📊 **Your Energy Score Explained:**\n\n"
            "EnerSense calculates your Energy Efficiency Score (0–100) based on 4 factors:\n\n"
            "| Factor | Max Points | What it measures |\n"
            "|--------|-----------|------------------|\n"
            "| Consumption level | 40 pts | How close to efficient threshold |\n"
            "| Usage hours | 25 pts | Fewer hours = higher score |\n"
            "| Appliance count | 20 pts | Fewer active appliances = better |\n"
            "| Temperature | 15 pts | Comfortable range (18–26°C) = full points |\n\n"
            "**Score Interpretation:**\n"
            "• 80–100: 🟢 Excellent — You're an energy champion!\n"
            "• 60–79: 🔵 Good — Minor improvements possible\n"
            "• 40–59: 🟡 Average — Several opportunities to improve\n"
            "• 0–39: 🔴 Needs Improvement — Take action now\n\n"
            "**To improve your score:**\n"
            "1. Reduce daily usage hours (biggest impact)\n"
            "2. Lower overall consumption\n"
            "3. Reduce the number of simultaneous active appliances\n"
            "4. Maintain comfortable (not extreme) temperature settings"
        )
        return {'answer': answer, 'topic': 'score'}

    def _answer_peak_hours_question(self, q):
        answer = (
            "⏰ **Peak vs Off-Peak Hours in India:**\n\n"
            "Most electricity DISCOMs in India have time-of-day pricing or peak load management.\n\n"
            "**Typical Peak Hours (High Demand):**\n"
            "• Morning: 6:00 AM – 10:00 AM\n"
            "• Evening: 6:00 PM – 11:00 PM\n"
            "*(When demand is highest — prices/load may be higher)*\n\n"
            "**Off-Peak Hours (Cheapest/Lowest Load):**\n"
            "• Late night: 11:00 PM – 5:00 AM\n"
            "• Afternoon: 12:00 PM – 4:00 PM\n\n"
            "**Smart Timing Strategies:**\n"
            "✅ Run washing machine at **10 PM–11 PM** (off-peak)\n"
            "✅ Heat water with geyser at **6 AM** (before peak, use hot water all day)\n"
            "✅ Pre-cool rooms to **22°C** before 6 PM, then raise to 26°C during peak\n"
            "✅ Charge EVs at **night** (cheapest and lowest grid stress)\n"
            "✅ Run dishwasher after **10 PM**\n\n"
            "**Check your DISCOM website** for Time-of-Day (ToD) tariffs that may offer real discounts for off-peak usage."
        )
        return {'answer': answer, 'topic': 'peak_hours'}

    def _answer_tariff_question(self, q):
        currency = self.currency
        tariff = self.tariff
        answer = (
            f"💳 **Electricity Tariff Explained:**\n\n"
            f"Your current configured tariff: **{currency}{tariff:.2f}/kWh**\n\n"
            f"**Types of Tariff Structures:**\n\n"
            f"1. **Flat Rate:** Same rate for all units\n"
            f"   • Simple to calculate: kWh × rate = bill\n\n"
            f"2. **Slab / Block Rate (most common in India):**\n"
            f"   • 0–100 units: ₹3.0–4.0/unit\n"
            f"   • 101–200 units: ₹5.0–6.0/unit\n"
            f"   • 201–300 units: ₹6.5–8.0/unit\n"
            f"   • 300+ units: ₹8.0–10.0/unit\n\n"
            f"3. **Time-of-Day (ToD):** Different rates at different hours\n\n"
            f"**Fixed Charges:** Your bill also includes:\n"
            f"• Fixed/demand charge (₹50–200/month)\n"
            f"• Electricity duty (5–20%)\n"
            f"• Fuel cost adjustment\n\n"
            f"**Update your tariff** in Settings to get accurate bill estimates in EnerSense!"
        )
        return {'answer': answer, 'topic': 'tariff'}

    def _answer_prediction_question(self, q):
        answer = (
            "🤖 **How EnerSense Predictions Work:**\n\n"
            "EnerSense uses a **Random Forest Regressor** (an ensemble ML model) to predict your energy consumption.\n\n"
            "**Training Data:** 2,000 synthetic but physically grounded records generated using:\n"
            "P = V × I (Power formula) + real-world factors\n\n"
            "**6 Input Features:**\n"
            "1. Voltage (V) — household supply voltage\n"
            "2. Current (A) — total electrical current drawn\n"
            "3. Usage Hours — daily appliance runtime\n"
            "4. No. of Appliances — active device count\n"
            "5. Temperature (°C) — ambient temperature (affects cooling)\n"
            "6. Previous Consumption — historical baseline (kWh)\n\n"
            "**Model Performance:**\n"
            "• R² Score: **0.984** (98.4% accuracy on test data)\n"
            "• MAE: **1.16 kWh** (average prediction error)\n"
            "• RMSE: **1.59 kWh**\n\n"
            "**Prediction Process:**\n"
            "1. Your inputs are normalized using StandardScaler\n"
            "2. 100 decision trees each make a prediction\n"
            "3. Average of all 100 predictions = final result\n"
            "4. Result classified as LOW / NORMAL / HIGH\n\n"
            "View the full evaluation on the **Model Performance** page!"
        )
        return {'answer': answer, 'topic': 'ml_model'}

    def _answer_my_consumption(self, q):
        latest = self._get_latest_kwh()
        avg = self._get_avg_kwh()
        count = len(self.predictions)

        if not latest:
            return {
                'answer': "📊 I don't have any prediction data for you yet. Please run your first **Energy Prediction** to see personalized insights about your consumption!\n\nGo to: **AI Prediction** → Enter your parameters → Get your result!",
                'topic': 'user_data'
            }

        monthly_kwh = round(latest * 30, 1)
        est_bill = round(monthly_kwh * self.tariff, 0)
        co2_monthly = round(monthly_kwh * self.emission_factor, 1)

        # Level classification
        if latest < 11.35:
            level_emoji = "🟢"
            level_text = "LOW (Efficient)"
        elif latest <= 23.02:
            level_emoji = "🔵"
            level_text = "NORMAL (Balanced)"
        else:
            level_emoji = "🔴"
            level_text = "HIGH (Action needed)"

        answer = (
            f"📊 **Your Energy Summary:**\n\n"
            f"Based on your **{count} prediction(s)**:\n\n"
            f"• Latest: **{latest:.2f} kWh/day** {level_emoji} {level_text}\n"
            f"• Average: **{avg:.2f} kWh/day**\n"
            f"• Monthly Estimate: **{monthly_kwh} kWh**\n"
            f"• Estimated Bill: **{self.currency}{est_bill:.0f}/month**\n"
            f"• CO₂ Footprint: **{co2_monthly} kg/month**\n"
            f"• Budget: **{self.currency}{self.budget:.0f}/month** ({'✅ Within budget' if est_bill <= self.budget else '⚠️ Over budget'})\n\n"
            f"Visit your **Dashboard** for charts, trends, and detailed analysis!"
        )
        return {'answer': answer, 'topic': 'user_data'}

    def _answer_general(self, q):
        answer = (
            "🔋 **EnerSense Energy Guide:**\n\n"
            "I can help you with:\n\n"
            "**💡 Ask me about:**\n"
            "• 'How can I reduce my electricity bill?'\n"
            "• 'How much energy does my AC use?'\n"
            "• 'What is a kWh?'\n"
            "• 'My consumption and what it means'\n"
            "• 'Solar panel costs and benefits'\n"
            "• 'What are peak electricity hours?'\n"
            "• 'How is my energy score calculated?'\n"
            "• 'Carbon footprint from my electricity'\n\n"
            "**🛠 EnerSense Tools:**\n"
            "• **AI Prediction** — Get your daily kWh estimate\n"
            "• **Appliance Calculator** — Per-device energy breakdown\n"
            "• **Energy Simulator** — See savings from usage changes\n"
            "• **Bill Estimator** — Calculate exact electricity bill\n\n"
            "What would you like to know? Type your question or click a suggested topic above!"
        )
        return {'answer': answer, 'topic': 'general'}


# ========================= SUGGESTED ADVISOR QUESTIONS =========================

ADVISOR_SUGGESTED_QUESTIONS = [
    "How can I reduce my electricity bill?",
    "How much energy does an AC use?",
    "What is a kWh and how is it calculated?",
    "What are the best times to use heavy appliances?",
    "How is my energy score calculated?",
    "Tell me about solar panels for my home",
    "What is my carbon footprint from electricity?",
    "How does EnerSense predict my energy usage?",
    "How much does a geyser / water heater cost to run?",
    "What appliances use the most electricity?",
]


def get_advisor_response(question: str, user_profile=None, recent_predictions=None) -> dict:
    """
    Main function to get an advisor response.
    Optionally uses Gemini API if GEMINI_API_KEY is set.
    Falls back to rule-based engine.
    """
    import os

    # Try Gemini API if key is configured
    gemini_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if gemini_key and len(gemini_key) > 10:
        try:
            return _get_gemini_response(question, gemini_key, user_profile, recent_predictions)
        except Exception as e:
            print(f"[Advisor] Gemini API failed ({e}), using rule-based engine.")

    # Rule-based fallback (always works)
    engine = EnergyAdvisorEngine(user_profile=user_profile, recent_predictions=recent_predictions)
    result = engine.answer(question)
    return result


def _get_gemini_response(question: str, api_key: str, user_profile=None, recent_predictions=None) -> dict:
    """
    Use Gemini API for advisor responses when API key is available.
    Builds a context-rich prompt with user data.
    """
    import urllib.request
    import json

    profile = user_profile or {}
    preds = recent_predictions or []

    # Build context
    context_parts = [
        "You are EnerSense Energy Advisor — a helpful AI assistant specialized in home energy management for Indian households.",
        "Answer concisely in 150-200 words. Use bullet points and emojis for readability.",
        "Focus on practical, actionable advice. Use Indian context (₹, kWh units, Indian appliances).",
    ]

    if profile:
        context_parts.append(f"User profile: Home type={profile.get('home_type','Apartment')}, "
                             f"People={profile.get('num_people',2)}, "
                             f"Tariff=₹{profile.get('tariff_rate',6)}/kWh, "
                             f"Budget=₹{profile.get('monthly_budget',2000)}/month")

    if preds:
        latest = preds[0].get('predicted_consumption', 0)
        avg = sum(p.get('predicted_consumption', 0) for p in preds) / len(preds)
        context_parts.append(f"Latest prediction: {latest:.2f} kWh/day, Average: {avg:.2f} kWh/day")

    system_prompt = ' '.join(context_parts)
    prompt = f"{system_prompt}\n\nUser question: {question}"

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 512, "temperature": 0.7}
    }).encode('utf-8')

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})

    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())

    answer = data['candidates'][0]['content']['parts'][0]['text']
    return {'answer': answer.strip(), 'topic': 'gemini', 'source': 'gemini_api'}
