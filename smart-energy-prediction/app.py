"""
EnerSense – Smart Energy Intelligence Platform
Flask Web Backend Application
"""

import os
import io
import csv
import json
import functools
import numpy as np
import pandas as pd
import joblib
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, session, Response
)

from database.db_setup import (
    init_db, insert_prediction, get_prediction_by_id,
    get_all_predictions, get_dashboard_stats,
    create_user, get_user_by_email, get_user_by_id,
    verify_user_credentials, DB_PATH,
    get_user_profile, update_user_profile, update_user_name,
    get_user_appliances, add_appliance, delete_appliance, clear_user_appliances,
    populate_default_appliances, save_simulator_session, get_comparison_data,
    save_advisor_conversation, get_advisor_history, get_weekly_consumption,
    update_user_password
)

from utils.energy_utils import (
    classify_consumption, generate_recommendations, generate_recommendation_string,
    calculate_energy_score, calculate_power_kw, calculate_energy_kwh,
    calculate_appliance_energy, calculate_bill, calculate_co2_emissions,
    calculate_slab_bill, TARIFF_SLABS, DEFAULT_APPLIANCES,
    generate_insights, generate_alerts,
    get_advisor_response, ADVISOR_SUGGESTED_QUESTIONS
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "energy_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "model", "scaler.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "model", "metrics.json")

FEATURE_NAMES = ['voltage', 'current', 'usage_hours', 'number_of_appliances', 'temperature', 'previous_consumption']

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "enersense-smart-energy-platform-secret-key-auth-2026")
app.jinja_env.globals.update(float=float, int=int, min=min, max=max, round=round, abs=abs, str=str, len=len)

# Ensure database and default tables exist
init_db()

# Load trained ML Model and Scaler
model = None
scaler = None
metrics_data = {}

def load_ml_assets():
    global model, scaler, metrics_data
    try:
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            model = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            print("[EnerSense] Loaded trained ML Model and Scaler successfully.")
        else:
            print("[EnerSense] Warning: Model artifacts not found. Please train models first.")

        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, 'r') as f:
                metrics_data = json.load(f)
        else:
            metrics_data = {
                'best_model': 'Random Forest Regressor',
                'thresholds': {'low': 11.35, 'high': 23.02}
            }
    except Exception as e:
        print(f"[EnerSense] Error loading ML assets: {e}")

load_ml_assets()

# ========================= AUTH DECORATOR & CONTEXT =========================

def login_required(view):
    """Decorator to require login credentials before accessing protected views."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this feature.", "warning")
            return redirect(url_for('login', next=request.url))
        return view(**kwargs)
    return wrapped_view

@app.context_processor
def inject_global_data():
    """Make metrics and current user universally available to all templates."""
    current_user = None
    profile = {}
    if 'user_id' in session:
        current_user = {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email'),
            'role': session.get('user_role')
        }
        try:
            profile = get_user_profile(session['user_id'])
        except Exception:
            profile = {}
    return dict(metrics=metrics_data, current_user=current_user, user_profile=profile)

# ========================= AUTH ROUTES =========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Login route."""
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))

    next_page = request.args.get('next') or request.form.get('next') or url_for('dashboard_page')

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template('login.html', email=email)

        user = verify_user_credentials(email, password)
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(next_page)
        else:
            flash("Invalid email or password.", "danger")
            return render_template('login.html', email=email)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration route."""
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not all([name, email, password, confirm_password]):
            flash("Please complete all registration fields.", "danger")
            return render_template('register.html', name=name, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return render_template('register.html', name=name, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "warning")
            return render_template('register.html', name=name, email=email)

        user_id, err = create_user(name, email, password, role="User")
        if err:
            flash(f"Registration failed: {err}", "danger")
            return render_template('register.html', name=name, email=email)

        session.clear()
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email.lower()
        session['user_role'] = 'User'

        flash(f"Account created! Welcome, {name}.", "success")
        return redirect(url_for('dashboard_page'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    """Sign out user."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/api/auth/firebase-login', methods=['POST'])
def api_firebase_login():
    """Endpoint for Firebase authenticated users."""
    try:
        data = request.get_json(force=True)
        email = data.get('email', '').strip()
        name = data.get('name', 'Firebase User').strip()

        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400

        user = get_user_by_email(email)
        if not user:
            user_id, _ = create_user(name, email, password="firebase-oauth-token-auth", role="User")
            user = get_user_by_id(user_id)

        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']

        return jsonify({
            'status': 'success',
            'redirect': url_for('dashboard_page'),
            'user': {'name': user['name'], 'email': user['email']}
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# ========================= MAIN PAGES =========================

@app.route('/')
def index():
    """Landing Home Page."""
    stats = get_dashboard_stats()
    return render_template('index.html', stats=stats, metrics=metrics_data)

@app.route('/about')
def about():
    """About page — Physics + AI connection."""
    return render_template('about.html', metrics=metrics_data)

# ========================= 1. DASHBOARD =========================

@app.route('/dashboard')
@login_required
def dashboard_page():
    """Main Analytics Dashboard."""
    user_id = session.get('user_id')
    stats = get_dashboard_stats(user_id=user_id)
    profile = get_user_profile(user_id)
    comparison = get_comparison_data(user_id=user_id)
    weekly = get_weekly_consumption(user_id=user_id)
    thresholds = metrics_data.get('thresholds', {'low': 11.35, 'high': 23.02})

    latest_kwh = 0
    energy_score_data = {'score': 0, 'status': 'No Data', 'color': '#94a3b8'}
    alerts = []
    co2 = 0
    est_bill = 0
    budget_status = {}

    if stats['recent']:
        latest = stats['recent'][-1]
        latest_kwh = latest['predicted_consumption']
        energy_score_data = calculate_energy_score(
            latest_kwh,
            latest.get('usage_hours', 6),
            latest.get('number_of_appliances', 4),
            latest.get('temperature', 25),
            thresholds
        )
        co2 = calculate_co2_emissions(latest_kwh * 30, profile.get('emission_factor', 0.82))
        tariff = profile.get('tariff_rate', 6.0)
        est_bill = calculate_bill(latest_kwh * 30, tariff)
        alerts = generate_alerts(latest_kwh, profile, thresholds)

        budget = profile.get('monthly_budget', 2000)
        budget_status = {
            'budget': budget,
            'estimated': est_bill,
            'within': est_bill <= budget,
            'percentage': min(100, round(est_bill / max(1, budget) * 100, 1))
        }

    potential_saving = round(max(0, est_bill * 0.15), 0) if est_bill > 0 else 0

    return render_template('dashboard.html',
        stats=stats, profile=profile, comparison=comparison, weekly=weekly,
        energy_score=energy_score_data, latest_kwh=latest_kwh,
        co2=co2, est_bill=est_bill, alerts=alerts,
        budget_status=budget_status, potential_saving=potential_saving,
        thresholds=thresholds, metrics=metrics_data
    )

# ========================= 2. PREDICTION =========================

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    """Energy Prediction with ML Model."""
    if request.method == 'POST':
        try:
            v_str = request.form.get('voltage', '').strip()
            i_str = request.form.get('current', '').strip()
            t_str = request.form.get('usage_hours', '').strip()
            app_str = request.form.get('number_of_appliances', '').strip()
            temp_str = request.form.get('temperature', '').strip()
            prev_str = request.form.get('previous_consumption', '').strip()

            if not all([v_str, i_str, t_str, app_str, temp_str, prev_str]):
                flash("Please fill in all required energy parameters.", "danger")
                return render_template('predict.html')

            voltage = float(v_str)
            current = float(i_str)
            usage_hours = float(t_str)
            number_of_appliances = int(app_str)
            temperature = float(temp_str)
            previous_consumption = float(prev_str)

            # Validation
            errors = []
            if not (150.0 <= voltage <= 300.0):
                errors.append("Voltage must be between 150V and 300V.")
            if not (0.1 <= current <= 50.0):
                errors.append("Current must be between 0.1A and 50A.")
            if not (0.1 <= usage_hours <= 24.0):
                errors.append("Usage hours must be between 0.1 and 24.")
            if not (1 <= number_of_appliances <= 50):
                errors.append("Appliances must be between 1 and 50.")
            if not (-10.0 <= temperature <= 60.0):
                errors.append("Temperature must be between -10°C and 60°C.")
            if not (0.0 <= previous_consumption <= 200.0):
                errors.append("Previous consumption must be 0–200 kWh.")

            if errors:
                for e in errors:
                    flash(e, "warning")
                return render_template('predict.html')

            # ML Inference
            if model is None or scaler is None:
                load_ml_assets()
                if model is None:
                    flash("ML model is not loaded. Please train models first.", "danger")
                    return render_template('predict.html')

            input_df = pd.DataFrame([[
                voltage, current, usage_hours, number_of_appliances, temperature, previous_consumption
            ]], columns=FEATURE_NAMES)

            scaled_features = scaler.transform(input_df)
            raw_prediction = model.predict(scaled_features)[0]
            predicted_consumption = max(0.1, round(float(raw_prediction), 2))

            thresholds = metrics_data.get('thresholds', {'low': 11.35, 'high': 23.02})
            level, color, label = classify_consumption(predicted_consumption, thresholds)
            tips = generate_recommendations(
                predicted_consumption, level, voltage, current,
                usage_hours, number_of_appliances, temperature, previous_consumption
            )
            recommendation = generate_recommendation_string(tips)

            record_data = {
                'voltage': voltage,
                'current': current,
                'usage_hours': usage_hours,
                'number_of_appliances': number_of_appliances,
                'temperature': temperature,
                'previous_consumption': previous_consumption,
                'predicted_consumption': predicted_consumption,
                'consumption_level': level,
                'recommendation': recommendation,
                'user_id': session.get('user_id')
            }
            record_id = insert_prediction(record_data)

            flash("Energy consumption predicted and recorded!", "success")
            return redirect(url_for('result', record_id=record_id))

        except ValueError:
            flash("Invalid input. Please enter valid numeric values.", "danger")
            return render_template('predict.html')
        except Exception as e:
            flash(f"Prediction error: {str(e)}", "danger")
            return render_template('predict.html')

    return render_template('predict.html')

@app.route('/result/<int:record_id>')
@login_required
def result(record_id):
    """Detailed Prediction Result Page."""
    record = get_prediction_by_id(record_id)
    if not record:
        flash("Prediction record not found.", "warning")
        return redirect(url_for('predict'))

    thresholds = metrics_data.get('thresholds', {'low': 11.35, 'high': 23.02})
    level, color, label = classify_consumption(record['predicted_consumption'], thresholds)

    physics_power_kw = calculate_power_kw(record['voltage'], record['current'])
    ideal_physics_kwh = calculate_energy_kwh(physics_power_kw, record['usage_hours'])

    profile = get_user_profile(session.get('user_id'))
    tariff = profile.get('tariff_rate', 6.0)
    emission_factor = profile.get('emission_factor', 0.82)

    predicted = record['predicted_consumption']
    monthly_kwh = round(predicted * 30, 2)
    monthly_bill = calculate_bill(monthly_kwh, tariff)
    co2_daily = calculate_co2_emissions(predicted, emission_factor)
    co2_monthly = calculate_co2_emissions(monthly_kwh, emission_factor)

    energy_score = calculate_energy_score(
        predicted,
        record['usage_hours'],
        record['number_of_appliances'],
        record['temperature'],
        thresholds
    )

    tips = generate_recommendations(
        predicted, level, record['voltage'], record['current'],
        record['usage_hours'], record['number_of_appliances'],
        record['temperature'], record['previous_consumption']
    )

    potential_saving = round(monthly_bill * 0.15, 0) if level != 'LOW' else round(monthly_bill * 0.05, 0)

    return render_template(
        'result.html',
        record=record, level=level, color=color, level_label=label,
        physics_power_kw=physics_power_kw, ideal_physics_kwh=ideal_physics_kwh,
        monthly_kwh=monthly_kwh, monthly_bill=monthly_bill,
        co2_daily=co2_daily, co2_monthly=co2_monthly,
        energy_score=energy_score, tips=tips,
        potential_saving=potential_saving,
        tariff=tariff, emission_factor=emission_factor,
        thresholds=thresholds, metrics=metrics_data
    )

# ========================= 3. BILL ESTIMATOR =========================

@app.route('/bill-estimator', methods=['GET', 'POST'])
@login_required
def bill_estimator():
    """Electricity Bill Estimator."""
    profile = get_user_profile(session.get('user_id'))
    result_data = None

    if request.method == 'POST':
        try:
            energy_kwh = float(request.form.get('energy_kwh', 0))
            slab_type = request.form.get('slab_type', 'flat')
            flat_rate = float(request.form.get('flat_rate', profile.get('tariff_rate', 6.0)))

            if energy_kwh <= 0:
                flash("Energy consumption must be positive.", "warning")
            elif energy_kwh > 10000:
                flash("Energy consumption seems unrealistically high.", "warning")
            else:
                total_bill, breakdown = calculate_slab_bill(energy_kwh, slab_type, flat_rate)
                co2 = calculate_co2_emissions(energy_kwh, profile.get('emission_factor', 0.82))
                result_data = {
                    'energy_kwh': energy_kwh,
                    'slab_type': slab_type,
                    'flat_rate': flat_rate,
                    'total_bill': total_bill,
                    'breakdown': breakdown,
                    'co2': co2,
                    'currency': profile.get('currency', '₹')
                }
        except ValueError:
            flash("Please enter valid numbers.", "danger")

    return render_template('bill_estimator.html', profile=profile,
                         result=result_data, tariff_slabs=TARIFF_SLABS)

# ========================= 4. APPLIANCE CALCULATOR =========================

@app.route('/appliance-calculator', methods=['GET', 'POST'])
@login_required
def appliance_calculator():
    """Appliance Energy Calculator."""
    user_id = session.get('user_id')
    profile = get_user_profile(user_id)

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'add':
            name = request.form.get('appliance_name', '').strip()
            power = request.form.get('power_watts', '').strip()
            qty = request.form.get('quantity', '1').strip()
            hours = request.form.get('hours_per_day', '1').strip()

            try:
                if not name:
                    flash("Please enter an appliance name.", "warning")
                else:
                    power_val = float(power)
                    qty_val = int(qty)
                    hours_val = float(hours)
                    if power_val <= 0 or qty_val <= 0 or hours_val <= 0:
                        flash("All values must be positive.", "warning")
                    elif hours_val > 24:
                        flash("Hours per day cannot exceed 24.", "warning")
                    else:
                        add_appliance(user_id, name, power_val, qty_val, hours_val)
                        flash(f"Added {name} to your appliance list.", "success")
            except ValueError:
                flash("Please enter valid numbers.", "danger")

        elif action == 'delete':
            aid = request.form.get('appliance_id', '')
            if aid:
                delete_appliance(int(aid), user_id)
                flash("Appliance removed.", "info")

        elif action == 'clear':
            clear_user_appliances(user_id)
            flash("All appliances cleared.", "info")

        return redirect(url_for('appliance_calculator'))

    appliances = get_user_appliances(user_id)
    tariff = profile.get('tariff_rate', 6.0)

    calc_appliances = []
    total_daily = 0
    total_monthly = 0
    total_monthly_cost = 0

    for a in appliances:
        daily, monthly = calculate_appliance_energy(a['power_watts'], a['quantity'], a['hours_per_day'])
        cost = calculate_bill(monthly, tariff)
        calc_appliances.append({
            **a,
            'daily_kwh': daily,
            'monthly_kwh': monthly,
            'monthly_cost': cost
        })
        total_daily += daily
        total_monthly += monthly
        total_monthly_cost += cost

    totals = {
        'daily_kwh': round(total_daily, 2),
        'monthly_kwh': round(total_monthly, 2),
        'monthly_cost': round(total_monthly_cost, 2),
        'co2_monthly': calculate_co2_emissions(total_monthly, profile.get('emission_factor', 0.82))
    }

    return render_template('appliance_calculator.html',
        appliances=calc_appliances, totals=totals, profile=profile,
        default_appliances=DEFAULT_APPLIANCES
    )

# ========================= 5. ENERGY SIMULATOR =========================

@app.route('/simulator', methods=['GET', 'POST'])
@login_required
def simulator():
    """What-If Energy Saving Simulator."""
    user_id = session.get('user_id')
    profile = get_user_profile(user_id)
    tariff = profile.get('tariff_rate', 6.0)
    result_data = None

    if request.method == 'POST':
        action = request.form.get('action', 'simulate')

        if action == 'load_defaults':
            clear_user_appliances(user_id)
            populate_default_appliances(user_id)
            flash("Loaded standard household appliances for simulation.", "success")
            return redirect(url_for('simulator'))

        try:
            sim_data = []
            total_current = 0
            total_new = 0

            i = 0
            while True:
                name = request.form.get(f'sim_name_{i}')
                if name is None:
                    break
                power = float(request.form.get(f'sim_power_{i}', 0))
                qty = int(request.form.get(f'sim_qty_{i}', 1))
                current_hrs = float(request.form.get(f'sim_current_hrs_{i}', 0))
                new_hrs = float(request.form.get(f'sim_new_hrs_{i}', 0))

                current_daily, current_monthly = calculate_appliance_energy(power, qty, current_hrs)
                new_daily, new_monthly = calculate_appliance_energy(power, qty, new_hrs)

                sim_data.append({
                    'name': name,
                    'power': power,
                    'qty': qty,
                    'current_hrs': current_hrs,
                    'new_hrs': new_hrs,
                    'current_monthly': current_monthly,
                    'new_monthly': new_monthly,
                    'saved_monthly': round(current_monthly - new_monthly, 2)
                })
                total_current += current_monthly
                total_new += new_monthly
                i += 1

            if not sim_data:
                flash("No appliance data available to simulate. Please adjust usage hours.", "warning")
            else:
                energy_saved = round(total_current - total_new, 2)
                money_saved = calculate_bill(energy_saved, tariff)

                result_data = {
                    'sim_items': sim_data,
                    'items': sim_data,
                    'total_current': round(total_current, 2),
                    'total_new': round(total_new, 2),
                    'energy_saved': energy_saved,
                    'money_saved': money_saved,
                    'co2_saved': calculate_co2_emissions(energy_saved, profile.get('emission_factor', 0.82))
                }

                save_simulator_session(user_id, sim_data, {
                    'current_kwh': total_current,
                    'new_kwh': total_new,
                    'saved_kwh': energy_saved,
                    'money_saved': money_saved
                })

        except (ValueError, TypeError) as e:
            flash(f"Invalid input: {e}", "danger")

    appliances = get_user_appliances(user_id)
    if not appliances:
        populate_default_appliances(user_id)
        appliances = get_user_appliances(user_id)

    return render_template('simulator.html',
        appliances=appliances, profile=profile,
        result=result_data, default_appliances=DEFAULT_APPLIANCES
    )

# ========================= 6. HISTORY =========================

@app.route('/history')
@login_required
def history():
    """Historical Prediction Records."""
    user_id = session.get('user_id')
    filter_level = request.args.get('level', '').strip()
    search = request.args.get('q', '').strip()
    date_filter = request.args.get('period', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = 20
    offset = (page - 1) * per_page

    records, total_count = get_all_predictions(
        limit=per_page, offset=offset, filter_level=filter_level,
        search=search, user_id=user_id, date_filter=date_filter
    )

    profile = get_user_profile(user_id)
    tariff = profile.get('tariff_rate', 6.0)

    for r in records:
        r['est_cost'] = calculate_bill(r['predicted_consumption'] * 30, tariff)

    total_pages = max(1, (total_count + per_page - 1) // per_page)

    return render_template(
        'history.html',
        records=records, total_count=total_count,
        filter_level=filter_level, search=search, date_filter=date_filter,
        page=page, total_pages=total_pages,
        profile=profile, metrics=metrics_data
    )

# ========================= 7. INSIGHTS =========================

@app.route('/insights')
@login_required
def insights_page():
    """AI Insights & Recommendations."""
    user_id = session.get('user_id')
    profile = get_user_profile(user_id)
    records, _ = get_all_predictions(limit=50, user_id=user_id)
    records.reverse()

    ai_insights = generate_insights(records, profile)
    comparison = get_comparison_data(user_id=user_id)
    thresholds = metrics_data.get('thresholds', {'low': 11.35, 'high': 23.02})

    energy_score = {'score': 0, 'status': 'No Data', 'color': '#94a3b8'}
    if records:
        latest = records[-1]
        energy_score = calculate_energy_score(
            latest['predicted_consumption'],
            latest.get('usage_hours', 6),
            latest.get('number_of_appliances', 4),
            latest.get('temperature', 25),
            thresholds
        )

    return render_template('insights.html',
        insights=ai_insights, comparison=comparison,
        energy_score=energy_score, profile=profile,
        records=records[-20:], metrics=metrics_data
    )

# ========================= 8. AI ENERGY ADVISOR =========================

@app.route('/advisor', methods=['GET', 'POST'])
@login_required
def advisor_page():
    """AI Energy Advisor interactive Q&A assistant."""
    user_id = session.get('user_id')
    profile = get_user_profile(user_id)
    recent_records, _ = get_all_predictions(limit=10, user_id=user_id)

    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            response_dict = get_advisor_response(
                question, user_profile=profile, recent_predictions=recent_records
            )
            save_advisor_conversation(
                user_id, question, response_dict['answer'],
                topic=response_dict.get('topic', 'general')
            )
            return redirect(url_for('advisor_page'))

    conversations = get_advisor_history(user_id, limit=30)
    return render_template(
        'advisor.html',
        conversations=conversations,
        suggested_questions=ADVISOR_SUGGESTED_QUESTIONS,
        profile=profile
    )

@app.route('/api/advisor', methods=['POST'])
def api_advisor():
    """AJAX endpoint for instant Energy Advisor responses."""
    try:
        data = request.get_json(force=True)
        question = data.get('question', '').strip()
        if not question:
            return jsonify({'status': 'error', 'message': 'Question is required'}), 400

        user_id = session.get('user_id')
        profile = get_user_profile(user_id) if user_id else {}
        recent_records = []
        if user_id:
            recent_records, _ = get_all_predictions(limit=10, user_id=user_id)

        response_dict = get_advisor_response(
            question, user_profile=profile, recent_predictions=recent_records
        )

        if user_id:
            save_advisor_conversation(
                user_id, question, response_dict['answer'],
                topic=response_dict.get('topic', 'general')
            )

        return jsonify({
            'status': 'success',
            'answer': response_dict['answer'],
            'topic': response_dict.get('topic', 'general')
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# ========================= 9. SETTINGS & PASSWORD CHANGE =========================

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """User Profile & Preferences Settings."""
    user_id = session.get('user_id')
    profile = get_user_profile(user_id)

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            if name:
                update_user_name(user_id, name)
                session['user_name'] = name

            update_user_profile(user_id, {
                'home_type': request.form.get('home_type', 'Apartment'),
                'num_people': request.form.get('num_people', 2),
                'monthly_budget': request.form.get('monthly_budget', 2000),
                'tariff_rate': request.form.get('tariff_rate', 6.0),
                'region': request.form.get('region', 'India'),
                'currency': request.form.get('currency', '₹'),
                'emission_factor': request.form.get('emission_factor', 0.82)
            })
            flash("Settings saved successfully.", "success")
            return redirect(url_for('settings'))
        except Exception as e:
            flash(f"Error saving settings: {e}", "danger")

    return render_template('settings.html', profile=profile)

@app.route('/settings/change-password', methods=['POST'])
@login_required
def change_password():
    """Update user password securely."""
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    current_pwd = request.form.get('current_password', '').strip()
    new_pwd = request.form.get('new_password', '').strip()
    confirm_pwd = request.form.get('confirm_new_password', '').strip()

    if not all([current_pwd, new_pwd, confirm_pwd]):
        flash("Please complete all password fields.", "danger")
        return redirect(url_for('settings'))

    if new_pwd != confirm_pwd:
        flash("New passwords do not match.", "warning")
        return redirect(url_for('settings'))

    if len(new_pwd) < 6:
        flash("New password must be at least 6 characters.", "warning")
        return redirect(url_for('settings'))

    user = verify_user_credentials(user_email, current_pwd)
    if not user:
        flash("Incorrect current password.", "danger")
        return redirect(url_for('settings'))

    update_user_password(user_id, new_pwd)
    flash("Password updated successfully!", "success")
    return redirect(url_for('settings'))

# ========================= 10. MODEL PERFORMANCE =========================

@app.route('/model-performance')
@login_required
def model_performance():
    """Model Evaluation Page."""
    return render_template('model_performance.html', metrics=metrics_data)

# ========================= API ENDPOINTS & EXPORT =========================

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """API endpoint for dashboard chart data."""
    user_id = session.get('user_id')
    stats = get_dashboard_stats(user_id=user_id)
    return jsonify(stats)

@app.route('/api/weekly-data')
@login_required
def api_weekly_data():
    """API endpoint for weekly consumption chart."""
    user_id = session.get('user_id')
    data = get_weekly_consumption(user_id=user_id)
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/export-csv')
@login_required
def export_csv():
    """Download user prediction history as CSV."""
    user_id = session.get('user_id')
    records, _ = get_all_predictions(limit=1000, user_id=user_id)
    profile = get_user_profile(user_id)
    tariff = profile.get('tariff_rate', 6.0)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'ID', 'Timestamp', 'Voltage (V)', 'Current (A)', 'Usage Hours',
        'Appliances', 'Temperature (C)', 'Previous Consumption (kWh)',
        'Predicted Consumption (kWh)', 'Level', 'Monthly Est (kWh)',
        'Estimated Cost', 'Recommendation'
    ])

    for r in records:
        pred = r['predicted_consumption']
        cost = calculate_bill(pred * 30, tariff)
        writer.writerow([
            r['id'], r['timestamp'], r['voltage'], r['current'],
            r['usage_hours'], r['number_of_appliances'], r['temperature'],
            r['previous_consumption'], pred, r['consumption_level'],
            round(pred * 30, 2), cost, r['recommendation']
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=enersense_history.csv"}
    )

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """REST API for programmatic prediction."""
    try:
        data = request.get_json(force=True)
        voltage = float(data.get('voltage', 230.0))
        current_val = float(data.get('current', 5.0))
        usage_hours = float(data.get('usage_hours', 6.0))
        number_of_appliances = int(data.get('number_of_appliances', 4))
        temperature = float(data.get('temperature', 28.0))
        previous_consumption = float(data.get('previous_consumption', 6.0))

        if model is None or scaler is None:
            return jsonify({'status': 'error', 'message': 'Model not loaded'}), 503

        input_df = pd.DataFrame([[
            voltage, current_val, usage_hours, number_of_appliances, temperature, previous_consumption
        ]], columns=FEATURE_NAMES)
        scaled_features = scaler.transform(input_df)
        pred_val = max(0.1, round(float(model.predict(scaled_features)[0]), 2))

        thresholds = metrics_data.get('thresholds', {'low': 11.35, 'high': 23.02})
        level, _, _ = classify_consumption(pred_val, thresholds)
        tips = generate_recommendations(
            pred_val, level, voltage, current_val, usage_hours,
            number_of_appliances, temperature, previous_consumption
        )

        rec_id = insert_prediction({
            'voltage': voltage, 'current': current_val, 'usage_hours': usage_hours,
            'number_of_appliances': number_of_appliances, 'temperature': temperature,
            'previous_consumption': previous_consumption, 'predicted_consumption': pred_val,
            'consumption_level': level, 'recommendation': generate_recommendation_string(tips),
            'user_id': session.get('user_id')
        })

        return jsonify({
            'status': 'success',
            'id': rec_id,
            'predicted_consumption_kwh': pred_val,
            'consumption_level': level,
            'recommendations': [t['text'] for t in tips]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

# ========================= ERROR HANDLERS =========================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("=" * 60)
    print("EnerSense – Smart Energy Intelligence Platform")
    print("Server starting at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
