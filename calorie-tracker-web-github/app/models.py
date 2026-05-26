from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    gender = db.Column(db.String(1))
    age = db.Column(db.Integer)
    activity_level = db.Column(db.String(20), default='moderate')
    target_weight_kg = db.Column(db.Float)
    target_date = db.Column(db.Date)
    budget_mode = db.Column(db.String(20), default='none')
    payday_day_of_week = db.Column(db.Integer)
    payday_bonus = db.Column(db.Float, default=500)
    daily_savings = db.Column(db.Float, default=100)
    accumulated_savings = db.Column(db.Float, default=0)
    daily_water_goal_cups = db.Column(db.Integer, default=8)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def bmr(self):
        if not all([self.height_cm, self.weight_kg, self.age]):
            return 0
        if self.gender == 'M':
            return 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age + 5
        else:
            return 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age - 161
    
    @property
    def tdee(self):
        activity_multipliers = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
        multiplier = activity_multipliers.get(self.activity_level, 1.55)
        return self.bmr * multiplier
    
    @property
    def daily_budget(self):
        base_budget = self.tdee
        
        if self.budget_mode == 'payday':
            today = datetime.utcnow().weekday()
            if today == self.payday_day_of_week:
                return base_budget + self.payday_bonus
        
        elif self.budget_mode == 'savings':
            today = datetime.utcnow().weekday()
            if today >= 5:
                return base_budget + self.accumulated_savings
            else:
                return base_budget - self.daily_savings
        
        return base_budget

class Food(db.Model):
    __tablename__ = 'foods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    unit = db.Column(db.String(20), default='份')
    calories = db.Column(db.Float, nullable=False)
    protein_g = db.Column(db.Float, default=0)
    carbs_g = db.Column(db.Float, default=0)
    sugar_g = db.Column(db.Float, default=0)
    fat_g = db.Column(db.Float, default=0)

class DailyLog(db.Model):
    __tablename__ = 'daily_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(20))
    quantity = db.Column(db.Float, default=1)
    unit = db.Column(db.String(20))
    calories = db.Column(db.Float, nullable=False)
    protein_g = db.Column(db.Float, default=0)
    carbs_g = db.Column(db.Float, default=0)
    sugar_g = db.Column(db.Float, default=0)
    fat_g = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WaterIntake(db.Model):
    __tablename__ = 'water_intake'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    cups = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CustomFoodHistory(db.Model):
    __tablename__ = 'custom_food_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    usage_count = db.Column(db.Integer, default=1)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

FOOD_DATA = {
    'fruit': [
        {'name': '蘋果', 'unit': '個', 'calories': 95, 'protein_g': 0.5, 'carbs_g': 25, 'sugar_g': 19, 'fat_g': 0.3},
        {'name': '香蕉', 'unit': '根', 'calories': 105, 'protein_g': 1.3, 'carbs_g': 27, 'sugar_g': 14, 'fat_g': 0.3},
        {'name': '橙', 'unit': '個', 'calories': 47, 'protein_g': 0.9, 'carbs_g': 12, 'sugar_g': 9, 'fat_g': 0.3},
        {'name': '葡萄', 'unit': '把', 'calories': 67, 'protein_g': 0.7, 'carbs_g': 17, 'sugar_g': 16, 'fat_g': 0.4},
        {'name': '草莓', 'unit': '份', 'calories': 32, 'protein_g': 0.8, 'carbs_g': 8, 'sugar_g': 4.9, 'fat_g': 0.3},
    ],
    'vegetable': [
        {'name': '番茄', 'unit': '個', 'calories': 18, 'protein_g': 0.9, 'carbs_g': 3.9, 'sugar_g': 2.6, 'fat_g': 0.2},
        {'name': '生菜', 'unit': '份', 'calories': 15, 'protein_g': 1.2, 'carbs_g': 2.9, 'sugar_g': 0.6, 'fat_g': 0.2},
        {'name': '胡蘿蔔', 'unit': '根', 'calories': 41, 'protein_g': 0.9, 'carbs_g': 10, 'sugar_g': 4.7, 'fat_g': 0.2},
        {'name': '花椰菜', 'unit': '份', 'calories': 34, 'protein_g': 2.8, 'carbs_g': 7, 'sugar_g': 1.4, 'fat_g': 0.4},
        {'name': '黃瓜', 'unit': '根', 'calories': 16, 'protein_g': 0.7, 'carbs_g': 3.6, 'sugar_g': 1.7, 'fat_g': 0.1},
    ],
    'dairy': [
        {'name': '牛奶', 'unit': '杯', 'calories': 149, 'protein_g': 7.7, 'carbs_g': 11.7, 'sugar_g': 12.3, 'fat_g': 7.9},
        {'name': '優格', 'unit': '杯', 'calories': 100, 'protein_g': 3.5, 'carbs_g': 6, 'sugar_g': 4, 'fat_g': 0.4},
        {'name': '起司', 'unit': '片', 'calories': 113, 'protein_g': 7, 'carbs_g': 0.7, 'sugar_g': 0.1, 'fat_g': 9.3},
        {'name': '奶油', 'unit': '湯匙', 'calories': 102, 'protein_g': 0.1, 'carbs_g': 0.1, 'sugar_g': 0, 'fat_g': 11.5},
    ],
    'fat_nut': [
        {'name': '花生醬', 'unit': '湯匙', 'calories': 96, 'protein_g': 3.6, 'carbs_g': 3.5, 'sugar_g': 1.5, 'fat_g': 8.1},
        {'name': '杏仁', 'unit': '盎司', 'calories': 164, 'protein_g': 6, 'carbs_g': 6, 'sugar_g': 1.2, 'fat_g': 14},
        {'name': '橄欖油', 'unit': '湯匙', 'calories': 119, 'protein_g': 0, 'carbs_g': 0, 'sugar_g': 0, 'fat_g': 13.5},
        {'name': '核桃', 'unit': '份', 'calories': 185, 'protein_g': 4.3, 'carbs_g': 3.9, 'sugar_g': 0.8, 'fat_g': 18.5},
    ],
    'protein': [
        {'name': '雞胸肉', 'unit': '100g', 'calories': 165, 'protein_g': 31, 'carbs_g': 0, 'sugar_g': 0, 'fat_g': 3.6},
        {'name': '蛋', 'unit': '個', 'calories': 155, 'protein_g': 13, 'carbs_g': 1.1, 'sugar_g': 1.1, 'fat_g': 11},
        {'name': '豆腐', 'unit': '100g', 'calories': 76, 'protein_g': 8, 'carbs_g': 1.9, 'sugar_g': 0.1, 'fat_g': 4.8},
        {'name': '魚', 'unit': '100g', 'calories': 206, 'protein_g': 22, 'carbs_g': 0, 'sugar_g': 0, 'fat_g': 12.6},
        {'name': '牛肉', 'unit': '100g', 'calories': 250, 'protein_g': 26, 'carbs_g': 0, 'sugar_g': 0, 'fat_g': 15},
    ],
    'grain': [
        {'name': '白米飯', 'unit': '碗', 'calories': 206, 'protein_g': 4.3, 'carbs_g': 45, 'sugar_g': 0.1, 'fat_g': 0.3},
        {'name': '全麥麵包', 'unit': '片', 'calories': 80, 'protein_g': 4, 'carbs_g': 14, 'sugar_g': 1.5, 'fat_g': 1},
        {'name': '燕麥', 'unit': '杯', 'calories': 150, 'protein_g': 5, 'carbs_g': 27, 'sugar_g': 1, 'fat_g': 3},
        {'name': '麵條', 'unit': '份', 'calories': 221, 'protein_g': 8, 'carbs_g': 43, 'sugar_g': 0.2, 'fat_g': 1.1},
        {'name': '玉米', 'unit': '根', 'calories': 77, 'protein_g': 2.7, 'carbs_g': 17, 'sugar_g': 3.2, 'fat_g': 1.1},
    ],
}

def init_sample_foods():
    if Food.query.first() is not None:
        return
    
    for category, foods in FOOD_DATA.items():
        for food in foods:
            db.session.add(Food(
                name=food['name'],
                category=category,
                unit=food['unit'],
                calories=food['calories'],
                protein_g=food['protein_g'],
                carbs_g=food['carbs_g'],
                sugar_g=food['sugar_g'],
                fat_g=food['fat_g'],
            ))
    
    db.session.commit()
