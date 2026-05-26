"""計算邏輯模組"""

def calculate_bmr(height_cm, weight_kg, age, gender):
    """Mifflin-St Jeor 公式"""
    if gender == 'M':
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def calculate_tdee(bmr, activity_level):
    """計算 TDEE"""
    multipliers = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
    return bmr * multipliers.get(activity_level, 1.55)

def calculate_weight_change(calorie_balance):
    """體重變化估計"""
    return calorie_balance / 7700
