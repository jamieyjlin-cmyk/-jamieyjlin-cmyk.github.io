from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app import db
from app.models import User, UserProfile, Food, DailyLog, WaterIntake, CustomFoodHistory
from app.calculations import calculate_bmr, calculate_tdee, calculate_weight_change
from datetime import datetime, date, timedelta

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

@main_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    return render_template('index.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        if user and user.check_password(data['password']):
            session['user_id'] = user.id
            return jsonify({'success': True})
        return jsonify({'success': False}), 401
    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'error': '帳號已存在'}), 400
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return jsonify({'success': True})
    return render_template('register.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@api_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登入'}), 401
    
    if request.method == 'GET':
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({})
        return jsonify({
            'height_cm': profile.height_cm,
            'weight_kg': profile.weight_kg,
            'gender': profile.gender,
            'age': profile.age,
            'activity_level': profile.activity_level,
            'target_weight_kg': profile.target_weight_kg,
            'target_date': profile.target_date.isoformat() if profile.target_date else None,
            'daily_water_goal_cups': profile.daily_water_goal_cups,
            'budget_mode': profile.budget_mode or 'none',
            'payday_day_of_week': profile.payday_day_of_week,
            'payday_bonus': profile.payday_bonus,
            'daily_savings': profile.daily_savings,
            'bmr': profile.bmr,
            'tdee': profile.tdee,
            'daily_budget': profile.daily_budget,
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
        
        profile.height_cm = data.get('height_cm')
        profile.weight_kg = data.get('weight_kg')
        profile.gender = data.get('gender')
        profile.age = data.get('age')
        profile.activity_level = data.get('activity_level')
        profile.target_weight_kg = data.get('target_weight_kg')
        profile.target_date = datetime.fromisoformat(data.get('target_date')).date() if data.get('target_date') else None
        profile.daily_water_goal_cups = data.get('daily_water_goal_cups', 8)
        profile.budget_mode = data.get('budget_mode', 'none')
        profile.payday_day_of_week = int(data.get('payday_day_of_week', 6)) if data.get('payday_day_of_week') else 6
        profile.payday_bonus = float(data.get('payday_bonus', 500)) if data.get('payday_bonus') else 500
        profile.daily_savings = float(data.get('daily_savings', 100)) if data.get('daily_savings') else 100
        db.session.commit()
        return jsonify({'success': True})

@api_bp.route('/foods', methods=['GET'])
def get_foods():
    category = request.args.get('category', 'fruit')
    foods = Food.query.filter_by(category=category).all()
    return jsonify([{
        'id': f.id,
        'name': f.name,
        'unit': f.unit,
        'calories': f.calories,
        'protein_g': f.protein_g,
        'carbs_g': f.carbs_g,
        'sugar_g': f.sugar_g,
    } for f in foods])

@api_bp.route('/logs', methods=['GET', 'POST', 'DELETE'])
def logs():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登入'}), 401
    
    if request.method == 'GET':
        log_date = request.args.get('date', date.today().isoformat())
        logs = DailyLog.query.filter_by(user_id=user_id, date=log_date).all()
        return jsonify([{
            'id': l.id,
            'food_name': l.food_name,
            'category': l.category,
            'quantity': l.quantity,
            'unit': l.unit,
            'calories': l.calories,
            'protein_g': l.protein_g,
            'carbs_g': l.carbs_g,
            'sugar_g': l.sugar_g,
        } for l in logs])
    
    elif request.method == 'POST':
        data = request.get_json()
        log = DailyLog(
            user_id=user_id,
            date=datetime.fromisoformat(data['date']).date(),
            food_name=data['food_name'],
            category=data.get('category'),
            quantity=data.get('quantity', 1),
            unit=data.get('unit'),
            calories=data['calories'],
            protein_g=data.get('protein_g', 0),
            carbs_g=data.get('carbs_g', 0),
            sugar_g=data.get('sugar_g', 0),
        )
        db.session.add(log)
        db.session.commit()
        
        if data.get('category') == 'custom':
            history = CustomFoodHistory.query.filter_by(user_id=user_id, food_name=data['food_name']).first()
            if history:
                history.usage_count += 1
                history.last_used = datetime.utcnow()
                history.calories = data['calories']  # 更新熱量
            else:
                history = CustomFoodHistory(user_id=user_id, food_name=data['food_name'], calories=data['calories'])
                db.session.add(history)
            db.session.commit()
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        log_id = request.args.get('id')
        log = DailyLog.query.filter_by(id=log_id, user_id=user_id).first()
        if log:
            db.session.delete(log)
            db.session.commit()
        return jsonify({'success': True})

@api_bp.route('/water', methods=['GET', 'POST'])
def water():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登入'}), 401
    
    if request.method == 'GET':
        water_date = request.args.get('date', date.today().isoformat())
        water = WaterIntake.query.filter_by(user_id=user_id, date=water_date).first()
        return jsonify({'cups': water.cups if water else 0})
    
    elif request.method == 'POST':
        data = request.get_json()
        water_date = datetime.fromisoformat(data['date']).date()
        water = WaterIntake.query.filter_by(user_id=user_id, date=water_date).first()
        
        if water:
            water.cups = data['cups']
        else:
            water = WaterIntake(user_id=user_id, date=water_date, cups=data['cups'])
            db.session.add(water)
        
        db.session.commit()
        return jsonify({'success': True})

@api_bp.route('/summary/monthly', methods=['GET'])
def monthly_summary():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登入'}), 401
    
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int, default=date.today().month)
    
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    logs = DailyLog.query.filter_by(user_id=user_id).filter(DailyLog.date.between(first_day, last_day)).all()
    
    daily_totals = {}
    for log in logs:
        if log.date not in daily_totals:
            daily_totals[log.date] = {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'sugar_g': 0}
        daily_totals[log.date]['calories'] += log.calories
        daily_totals[log.date]['protein_g'] += log.protein_g
        daily_totals[log.date]['carbs_g'] += log.carbs_g
        daily_totals[log.date]['sugar_g'] += log.sugar_g
    
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    budget = profile.daily_budget if profile else 0
    
    summaries = []
    total_balance = 0
    
    for day in range(1, (last_day - first_day).days + 2):
        current_date = first_day + timedelta(days=day - 1)
        if current_date > last_day:
            break
        total_calories = daily_totals.get(current_date, {}).get('calories', 0)
        balance = budget - total_calories
        total_balance += balance
        summaries.append({
            'date': current_date.isoformat(),
            'total_calories': total_calories,
            'daily_budget': budget,
            'calorie_balance': balance,
        })
    
    weight_change = calculate_weight_change(total_balance)
    
    return jsonify({
        'summaries': summaries,
        'stats': {
            'total_calories': sum(d.get('calories', 0) for d in daily_totals.values()),
            'total_balance': total_balance,
            'weight_change_estimate': weight_change,
        }
    })

@api_bp.route('/water/monthly', methods=['GET'])
def water_monthly():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登入'}), 401
    
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int, default=date.today().month)
    
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    waters = WaterIntake.query.filter_by(user_id=user_id).filter(WaterIntake.date.between(first_day, last_day)).all()
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    goal_cups = profile.daily_water_goal_cups if profile else 8
    
    total_cups = sum(w.cups for w in waters)
    days_in_month = (last_day - first_day).days + 1
    target_cups = goal_cups * days_in_month
    achievement_rate = (total_cups / target_cups * 100) if target_cups > 0 else 0
    
    return jsonify({
        'stats': {
            'total_cups': total_cups,
            'target_cups': target_cups,
            'achievement_rate': achievement_rate,
        }
    })

@api_bp.route('/custom-foods', methods=['GET'])
def custom_foods():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': '未登入'}), 401
    
    limit = request.args.get('limit', 10, type=int)
    foods = CustomFoodHistory.query.filter_by(user_id=user_id).order_by(CustomFoodHistory.last_used.desc()).limit(limit).all()
    return jsonify([{'food_name': f.food_name, 'calories': f.calories, 'usage_count': f.usage_count} for f in foods])
