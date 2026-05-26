// 全域變數
let currentDate = new Date();
let currentMonth = new Date();

// 頁面切換
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        
        e.target.classList.add('active');
        const pageId = e.target.dataset.page;
        document.getElementById(pageId).classList.add('active');
        
        if (pageId === 'daily-log') loadDailyLog();
        if (pageId === 'calendar') loadMonthlyReport();
    });
});

// 基本資料頁
document.getElementById('profileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    const res = await fetch('/api/profile', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if (res.ok) {
        alert('保存成功');
        loadProfile();
    }
});

async function loadProfile() {
    const res = await fetch('/api/profile');
    const profile = await res.json();
    
    if (profile.height_cm) {
        document.querySelector('[name="height_cm"]').value = profile.height_cm;
        document.querySelector('[name="weight_kg"]').value = profile.weight_kg;
        document.querySelector('[name="gender"]').value = profile.gender;
        document.querySelector('[name="age"]').value = profile.age;
        document.querySelector('[name="activity_level"]').value = profile.activity_level;
        document.querySelector('[name="target_weight_kg"]').value = profile.target_weight_kg;
        document.querySelector('[name="target_date"]').value = profile.target_date;
        document.querySelector('[name="daily_water_goal_cups"]').value = profile.daily_water_goal_cups;
        
        // 加載預算設定
        const budgetMode = profile.budget_mode || 'none';
        document.getElementById('budgetMode').value = budgetMode;
        document.querySelector('[name="payday_day_of_week"]').value = profile.payday_day_of_week || 6;
        document.querySelector('[name="payday_bonus"]').value = profile.payday_bonus || 500;
        document.querySelector('[name="daily_savings"]').value = profile.daily_savings || 100;
        updateBudgetModeUI();
        
        document.getElementById('bmrValue').textContent = Math.round(profile.bmr);
        document.getElementById('tdeeValue').textContent = Math.round(profile.tdee);
        document.getElementById('budgetValue').textContent = Math.round(profile.daily_budget);
    }
}

// 預算模式切換
function updateBudgetModeUI() {
    const mode = document.getElementById('budgetMode').value;
    document.getElementById('paydayDayGroup').style.display = mode === 'payday' ? 'block' : 'none';
    document.getElementById('paydayBonusGroup').style.display = mode === 'payday' ? 'block' : 'none';
    document.getElementById('dailySavingsGroup').style.display = mode === 'savings' ? 'block' : 'none';
}

document.getElementById('budgetMode').addEventListener('change', updateBudgetModeUI);

// 每日飲食記帳頁
document.getElementById('logDate').valueAsDate = new Date();

document.getElementById('prevDay').addEventListener('click', () => {
    currentDate.setDate(currentDate.getDate() - 1);
    document.getElementById('logDate').valueAsDate = new Date(currentDate);
    loadDailyLog();
});

document.getElementById('nextDay').addEventListener('click', () => {
    currentDate.setDate(currentDate.getDate() + 1);
    document.getElementById('logDate').valueAsDate = new Date(currentDate);
    loadDailyLog();
});

document.getElementById('logDate').addEventListener('change', (e) => {
    currentDate = new Date(e.target.value);
    loadDailyLog();
});

document.getElementById('foodCategory').addEventListener('change', async (e) => {
    const category = e.target.value;
    const selectGroup = document.getElementById('foodSelectGroup');
    const customGroup = document.getElementById('customFoodGroup');
    
    if (category === 'custom') {
        selectGroup.style.display = 'none';
        customGroup.style.display = 'block';
    } else {
        selectGroup.style.display = 'block';
        customGroup.style.display = 'none';
        
        const res = await fetch(`/api/foods?category=${category}`);
        const foods = await res.json();
        
        const select = document.getElementById('foodSelect');
        select.innerHTML = '';
        foods.forEach(food => {
            const option = document.createElement('option');
            option.value = JSON.stringify(food);
            option.textContent = `${food.name} (${food.calories} kcal/${food.unit})`;
            select.appendChild(option);
        });
        
        if (foods.length > 0) {
            select.dispatchEvent(new Event('change'));
        }
    }
});

document.getElementById('foodSelect').addEventListener('change', (e) => {
    if (e.target.value) {
        const food = JSON.parse(e.target.value);
        document.getElementById('foodCalories').value = food.calories;
    }
});

document.getElementById('foodQuantity').addEventListener('change', (e) => {
    const quantity = parseFloat(e.target.value) || 1;
    const baseCalories = parseFloat(document.getElementById('foodCalories').value) || 0;
    document.getElementById('foodCalories').value = (baseCalories * quantity).toFixed(0);
});

document.getElementById('addFoodBtn').addEventListener('click', async () => {
    const category = document.getElementById('foodCategory').value;
    const date = document.getElementById('logDate').value;
    let foodName, calories;
    
    if (category === 'custom') {
        foodName = document.getElementById('customFoodName').value;
        calories = parseFloat(document.getElementById('foodCalories').value) || 0;
        
        if (!foodName || calories <= 0) {
            alert('請輸入食物名稱和熱量');
            return;
        }
    } else {
        const foodStr = document.getElementById('foodSelect').value;
        if (!foodStr) {
            alert('請選擇食物');
            return;
        }
        const food = JSON.parse(foodStr);
        foodName = food.name;
        calories = parseFloat(document.getElementById('foodCalories').value);
    }
    
    const res = await fetch('/api/logs', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            date,
            food_name: foodName,
            category,
            calories,
            quantity: parseFloat(document.getElementById('foodQuantity').value) || 1,
        })
    });
    
    if (res.ok) {
        document.getElementById('customFoodName').value = '';
        document.getElementById('foodQuantity').value = 1;
        loadDailyLog();
    }
});

document.getElementById('saveWaterBtn').addEventListener('click', async () => {
    const date = document.getElementById('logDate').value;
    const cups = parseFloat(document.getElementById('waterCups').value) || 0;
    
    const res = await fetch('/api/water', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({date, cups})
    });
    
    if (res.ok) {
        alert('飲水量已保存');
        loadDailyLog();
    }
});

async function loadDailyLog() {
    const date = document.getElementById('logDate').value;
    
    // 載入飲食記錄
    const logsRes = await fetch(`/api/logs?date=${date}`);
    const logs = await logsRes.json();
    
    const logsList = document.getElementById('dailyLogsList');
    logsList.innerHTML = '';
    
    let totalCalories = 0, totalProtein = 0, totalCarbs = 0, totalSugar = 0;
    
    logs.forEach(log => {
        totalCalories += log.calories;
        totalProtein += log.protein_g;
        totalCarbs += log.carbs_g;
        totalSugar += log.sugar_g;
        
        const item = document.createElement('div');
        item.className = 'log-item';
        item.innerHTML = `
            <div class="log-item-info">
                <div class="log-item-name">${log.food_name}</div>
                <div class="log-item-details">${log.quantity} ${log.unit} • ${log.category}</div>
            </div>
            <div class="log-item-calories">${log.calories} kcal</div>
            <button class="log-item-delete" onclick="deleteLog(${log.id})">刪除</button>
        `;
        logsList.appendChild(item);
    });
    
    // 載入飲水量
    const waterRes = await fetch(`/api/water?date=${date}`);
    const water = await waterRes.json();
    document.getElementById('waterCups').value = water.cups;
    
    // 載入個人資料以取得目標
    const profileRes = await fetch('/api/profile');
    const profile = await profileRes.json();
    
    const budget = profile.daily_budget || 2000;
    const balance = budget - totalCalories;
    const waterGoal = profile.daily_water_goal_cups || 8;
    const waterPercent = Math.min((water.cups / waterGoal) * 100, 100);
    
    // 更新飲水進度
    document.getElementById('waterFill').style.width = waterPercent + '%';
    document.getElementById('waterText').textContent = `${water.cups} / ${waterGoal} 杯 (${(water.cups * 250).toFixed(0)}ml / ${(waterGoal * 250).toFixed(0)}ml)`;
    
    // 更新每日摘要
    const summary = document.getElementById('dailySummary');
    summary.innerHTML = `
        <div class="summary-item">
            <div class="summary-label">總熱量</div>
            <div class="summary-value">${totalCalories}</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">每日預算</div>
            <div class="summary-value">${Math.round(budget)}</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">熱量餘額</div>
            <div class="summary-value" style="color: ${balance >= 0 ? '#7cb342' : '#ef5350'}">${Math.round(balance)}</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">蛋白質</div>
            <div class="summary-value">${totalProtein.toFixed(1)}g</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">碳水</div>
            <div class="summary-value">${totalCarbs.toFixed(1)}g</div>
        </div>
        <div class="summary-item">
            <div class="summary-label">糖分</div>
            <div class="summary-value">${totalSugar.toFixed(1)}g</div>
        </div>
    `;
}

async function deleteLog(logId) {
    if (confirm('確定要刪除嗎？')) {
        const res = await fetch(`/api/logs?id=${logId}`, {method: 'DELETE'});
        if (res.ok) {
            loadDailyLog();
        }
    }
}

// 月曆報表頁
document.getElementById('prevMonth').addEventListener('click', () => {
    currentMonth.setMonth(currentMonth.getMonth() - 1);
    loadMonthlyReport();
});

document.getElementById('nextMonth').addEventListener('click', () => {
    currentMonth.setMonth(currentMonth.getMonth() + 1);
    loadMonthlyReport();
});

async function loadMonthlyReport() {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth() + 1;
    
    document.getElementById('monthDisplay').textContent = `${year}年${month}月`;
    
    // 載入月度統計
    const summaryRes = await fetch(`/api/summary/monthly?year=${year}&month=${month}`);
    const summary = await summaryRes.json();
    
    // 繪製熱量長條圖
    const dates = summary.summaries.map(s => new Date(s.date).getDate());
    const balances = summary.summaries.map(s => s.calorie_balance);
    
    const trace = {
        x: dates,
        y: balances,
        type: 'bar',
        marker: {
            color: balances.map(b => b >= 0 ? '#7cb342' : '#ef5350')
        }
    };
    
    const layout = {
        title: '每日熱量盈虧',
        xaxis: {title: '日期'},
        yaxis: {title: '熱量 (kcal)'},
        margin: {b: 40, l: 60, t: 40, r: 40}
    };
    
    Plotly.newPlot('calorieChart', [trace], layout, {responsive: true});
    
    // 月度統計卡片
    const stats = document.getElementById('monthlyStats');
    stats.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">總熱量攝取</div>
            <div class="stat-value">${summary.stats.total_calories.toFixed(0)}</div>
            <div class="stat-unit">kcal</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">月度盈虧</div>
            <div class="stat-value" style="color: ${summary.stats.total_balance >= 0 ? '#7cb342' : '#ef5350'}">${summary.stats.total_balance.toFixed(0)}</div>
            <div class="stat-unit">kcal</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">體重變化估計</div>
            <div class="stat-value">${summary.stats.weight_change_estimate.toFixed(2)}</div>
            <div class="stat-unit">kg</div>
        </div>
    `;
    
    // 飲水達成率
    const waterRes = await fetch(`/api/water/monthly?year=${year}&month=${month}`);
    const waterData = await waterRes.json();
    
    const waterStats = document.getElementById('waterStats');
    waterStats.innerHTML = `
        <div style="margin-bottom: 12px;">
            <strong>月度飲水達成率: ${waterData.stats.achievement_rate.toFixed(1)}%</strong>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${Math.min(waterData.stats.achievement_rate, 100)}%"></div>
        </div>
        <p>${waterData.stats.total_cups.toFixed(0)} / ${waterData.stats.target_cups.toFixed(0)} 杯 (${(waterData.stats.total_cups * 250).toFixed(0)}ml / ${(waterData.stats.target_cups * 250).toFixed(0)}ml)</p>
    `;
}

// 初始化
loadProfile();
loadDailyLog();
