"""
主应用文件 - 贵州天气健康管理系统 (PWA版本)
支持手机端安装的渐进式Web应用
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
import os

# ===== 添加当前目录到Python路径 =====
sys.path.append(os.path.dirname(__file__))

# ===== PWA相关函数 =====
def add_pwa_assets():
    """添加PWA资源到页面head"""
    pwa_html = """
    <!-- PWA配置 -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#764ba2">
    
    <!-- iOS支持 -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="天气健康">
    <link rel="apple-touch-icon" href="/icon-192.png">
    
    <!-- Android支持 -->
    <meta name="mobile-web-app-capable" content="yes">
    """
    return pwa_html

def register_service_worker():
    """注册Service Worker的JavaScript代码"""
    sw_js = """
    <script>
        // 注册Service Worker
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/service-worker.js')
                    .then(function(registration) {
                        console.log('✅ ServiceWorker 注册成功:', registration.scope);
                        
                        // 检查更新
                        registration.addEventListener('updatefound', () => {
                            console.log('🔄 发现新版本，正在更新...');
                        });
                    })
                    .catch(function(error) {
                        console.log('❌ ServiceWorker 注册失败:', error);
                    });
            });
        }
        
        // 处理PWA安装提示
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // 可以在这里显示安装按钮
            setTimeout(() => {
                if (deferredPrompt && window.innerWidth < 768) {
                    showInstallPrompt();
                }
            }, 3000);
        });
        
        // 显示安装提示
        function showInstallPrompt() {
            const installBtn = document.createElement('div');
            installBtn.innerHTML = `
                <div style="
                    position: fixed;
                    bottom: 80px;
                    right: 20px;
                    background: #764ba2;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 25px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    cursor: pointer;
                    z-index: 9999;
                    font-size: 14px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">
                    📱 安装应用
                </div>
            `;
            
            installBtn.onclick = () => {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('✅ 用户同意安装');
                    }
                    deferredPrompt = null;
                    installBtn.remove();
                });
            };
            
            document.body.appendChild(installBtn);
            
            // 10秒后自动隐藏
            setTimeout(() => {
                if (document.body.contains(installBtn)) {
                    installBtn.remove();
                }
            }, 10000);
        }
        
        // 离线检测
        window.addEventListener('offline', () => {
            console.log('📴 网络已断开');
            showOfflineMessage();
        });
        
        window.addEventListener('online', () => {
            console.log('📶 网络已恢复');
            hideOfflineMessage();
        });
        
        function showOfflineMessage() {
            let msg = document.getElementById('offline-message');
            if (!msg) {
                msg = document.createElement('div');
                msg.id = 'offline-message';
                msg.innerHTML = `
                    <div style="
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background: #ff9800;
                        color: white;
                        padding: 10px 15px;
                        border-radius: 5px;
                        z-index: 10000;
                        font-size: 12px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    ">
                        📶 网络已断开，使用离线数据
                    </div>
                `;
                document.body.appendChild(msg);
            }
        }
        
        function hideOfflineMessage() {
            const msg = document.getElementById('offline-message');
            if (msg) {
                msg.remove();
                
                // 显示重新连接提示
                const reconnectMsg = document.createElement('div');
                reconnectMsg.innerHTML = `
                    <div style="
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background: #4caf50;
                        color: white;
                        padding: 10px 15px;
                        border-radius: 5px;
                        z-index: 10000;
                        font-size: 12px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                        animation: fadeOut 2s forwards 2s;
                    ">
                        ✅ 网络已恢复
                    </div>
                `;
                document.body.appendChild(reconnectMsg);
                setTimeout(() => reconnectMsg.remove(), 4000);
            }
        }
        
        // 检测是否已安装
        window.addEventListener('appinstalled', () => {
            console.log('🎉 PWA已安装到设备');
            // 可以发送分析事件等
        });
    </script>
    <style>
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    </style>
    """
    return sw_js

# ===== 简洁的CSS样式 =====
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
    }
    .health-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .health-high { border-left-color: #ff4444; background: #ffebee; }
    .health-medium { border-left-color: #ff9800; background: #fff3e0; }
    .health-low { border-left-color: #4caf50; background: #e8f5e8; }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.3rem;
        text-align: center;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .section-title {
        background: #f8f9fa;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        font-weight: bold;
        color: skyblue;
    }
    .risk-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        color: white;
        font-weight: bold;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
    .risk-high { background: #ff4444; }
    .risk-medium { background: #ff9800; }
    .risk-low { background: #4caf50; }
    
    /* PWA安装按钮样式 */
    .pwa-install-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 25px;
        cursor: pointer;
        font-weight: bold;
        margin: 10px 0;
        width: 100%;
        transition: transform 0.2s;
    }
    .pwa-install-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

class SimpleVisualWeatherApp:
    """
    简洁可视化天气应用 - PWA版本
    """
    
    def __init__(self):
        """初始化应用"""
        self.weather_loader = None
        self.current_city = None
        self.data_loaded = False
        
    def run(self):
        """运行简洁可视化天气应用的主方法"""
        # 添加PWA资源
        st.markdown(add_pwa_assets(), unsafe_allow_html=True)
        st.markdown(register_service_worker(), unsafe_allow_html=True)
        
        # 应用标题
        st.markdown('<div class="main-header">🏞️ 贵州天气健康分析 📱</div>', unsafe_allow_html=True)
        
        # PWA安装提示
        self.show_pwa_installation_guide()
        
        # 城市选择
        selected_city = self.create_city_selector()
        
        # 初始化数据加载器
        self.initialize_data_loader(selected_city)
        
        # 显示主要内容
        self.show_main_dashboard(selected_city)
        
        # 页脚
        self.create_footer()
    
    def show_pwa_installation_guide(self):
        """显示PWA安装指南"""
        with st.sidebar:
            st.markdown("### 📱 安装到手机")
            st.markdown("""
            **支持以下浏览器：**
            - **Chrome/Edge**（Android）
            - **Safari**（iOS）
            - **三星浏览器**
            
            **安装方法：**
            1. 点击浏览器菜单（右上角•••）
            2. 选择"安装应用"或"添加到主屏幕"
            3. 确认安装即可
            
            **PWA功能：**
            ✅ 离线使用  
            ✅ 推送通知  
            ✅ 后台更新  
            ✅ 全屏体验
            """)
            
            if st.button("🔄 检查PWA支持", key="check_pwa"):
                st.info("""
                **PWA状态检查：**
                - Service Worker: ✅ 已注册
                - Manifest: ✅ 已加载
                - 离线支持: ✅ 已启用
                - 安装状态: 等待用户操作
                """)
    
    def create_city_selector(self):
        """创建城市选择器"""
        st.sidebar.title("📍 选择城市")
        guizhou_cities = ["贵阳市", "毕节市", "遵义市", "六盘水市", "安顺市"]
        selected_city = st.sidebar.selectbox("", guizhou_cities, key="city_selector")
        
        st.sidebar.markdown("---")
        st.sidebar.info("""
        **监控的疾病类型：**
        - 🦵 关节痛
        - 👃 过敏性鼻炎  
        - 🌬️ 哮喘
        - 🧴 皮肤敏感
        - ❤️ 心脑血管疾病
        """)
        
        return selected_city
    
    def initialize_data_loader(self, city):
        """
        初始化真实数据加载器
        """
        if not self.data_loaded or self.current_city != city:
            try:
                with st.spinner(f'正在加载{city}数据...'):
                    from data_sources import RealWeatherDataLoader
                    self.weather_loader = RealWeatherDataLoader(city)
                    self.current_city = city
                    self.data_loaded = True
                    st.success(f"✅ {city} 数据加载完成")
            except Exception as e:
                st.error(f"❌ 数据加载失败: {e}")
                self.data_loaded = False
    
    def show_main_dashboard(self, city):
        """
        显示主仪表盘 - 简洁直观
        """
        if not self.data_loaded or not self.weather_loader:
            st.error("🔧 数据加载中...")
            return
        
        # 获取实时数据
        with st.spinner('正在获取最新天气数据...'):
            try:
                realtime_data = self.weather_loader.get_realtime_data()
                
                # 显示数据更新时间
                if 'update_time' in realtime_data.columns:
                    update_time = realtime_data['update_time'].iloc[0]
                    if isinstance(update_time, pd.Timestamp):
                        st.caption(f"📅 数据更新时间: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 顶部关键指标
                self.display_key_metrics(realtime_data, city)
                
                # 健康风险概览
                self.display_health_overview(realtime_data)
                
                # 天气详情
                self.display_weather_details(realtime_data)
                
                # 疾病风险详情
                self.display_disease_details(realtime_data)
                
                # 预测信息
                self.display_forecast_info(city)
                
            except Exception as e:
                st.error(f"❌ 数据获取失败: {e}")
    
    def display_key_metrics(self, data, city):
        """显示关键指标"""
        st.markdown(f'<div class="section-title">📊 {city} - 今日关键指标</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = data['temperature'].iloc[0]
            temp_status = "寒冷" if temp < 10 else "凉爽" if temp < 18 else "舒适" if temp < 26 else "炎热"
            temp_color = "#2196F3" if temp < 10 else "#4CAF50" if temp < 26 else "#FF9800"
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 1.2rem; color: {temp_color}; font-weight: bold;">{temp:.1f}°C</div>
                <div style="font-size: 0.8rem; color: #666;">🌡️ 温度</div>
                <div style="font-size: 0.7rem; color: #888;">{temp_status}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            humidity = data['humidity'].iloc[0]
            humidity_status = "干燥" if humidity < 40 else "舒适" if humidity < 70 else "潮湿"
            humidity_color = "#FF9800" if humidity < 40 else "#4CAF50" if humidity < 70 else "#2196F3"
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 1.2rem; color: {humidity_color}; font-weight: bold;">{humidity:.0f}%</div>
                <div style="font-size: 0.8rem; color: #666;">💧 湿度</div>
                <div style="font-size: 0.7rem; color: #888;">{humidity_status}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            uv_index = data['uv_index'].iloc[0] if 'uv_index' in data.columns else 0
            uv_status = "弱" if uv_index < 3 else "中等" if uv_index < 6 else "强"
            uv_color = "#4CAF50" if uv_index < 3 else "#FF9800" if uv_index < 6 else "#F44336"
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 1.2rem; color: {uv_color}; font-weight: bold;">{uv_index}</div>
                <div style="font-size: 0.8rem; color: #666;">☀️ 紫外线</div>
                <div style="font-size: 0.7rem; color: #888;">{uv_status}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # 计算总体健康风险
            diseases_risk = self.calculate_disease_risks(data)
            max_risk = max([risk['score'] for risk in diseases_risk.values()])
            overall_risk = "高" if max_risk >= 2.5 else "中" if max_risk >= 1.5 else "低"
            risk_color = "#F44336" if overall_risk == "高" else "#FF9800" if overall_risk == "中" else "#4CAF50"
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 1.2rem; color: {risk_color}; font-weight: bold;">{overall_risk}</div>
                <div style="font-size: 0.8rem; color: #666;">❤️ 健康风险</div>
                <div style="font-size: 0.7rem; color: #888;">总体评估</div>
            </div>
            """, unsafe_allow_html=True)
    
    def display_health_overview(self, data):
        """显示健康风险概览"""
        st.markdown('<div class="section-title">🎯 今日健康风险概览</div>', unsafe_allow_html=True)
        
        diseases_risk = self.calculate_disease_risks(data)
        
        # 创建风险分布图
        risk_counts = {'高风险': 0, '中风险': 0, '低风险': 0}
        for risk_data in diseases_risk.values():
            if risk_data['level'] == 'high':
                risk_counts['高风险'] += 1
            elif risk_data['level'] == 'medium':
                risk_counts['中风险'] += 1
            else:
                risk_counts['低风险'] += 1
        
        fig = px.pie(
            values=list(risk_counts.values()),
            names=list(risk_counts.keys()),
            color=list(risk_counts.keys()),
            color_discrete_map={'高风险': '#ff4444', '中风险': '#ff9800', '低风险': '#4caf50'}
        )
        
        fig.update_layout(
            showlegend=True,
            height=250,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 简要提示
        if risk_counts['高风险'] > 0:
            st.error(f"🚨 今日有 {risk_counts['高风险']} 种疾病处于高风险，请特别注意防护")
        elif risk_counts['中风险'] > 0:
            st.warning(f"⚠️ 今日有 {risk_counts['中风险']} 种疾病处于中风险，建议注意")
        else:
            st.success("✅ 今日所有疾病风险均较低，适合户外活动")
    
    def display_weather_details(self, data):
        """显示天气详情"""
        st.markdown('<div class="section-title">🌤️ 天气详情</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 温度体感分析
            temp = data['temperature'].iloc[0]
            feels_like = data['apparent_temperature'].iloc[0]
            
            fig = go.Figure()
            
            fig.add_trace(go.Indicator(
                mode = "number+delta",
                value = temp,
                number = {'suffix': "°C", "font": {"size": 30}},
                delta = {'reference': feels_like, 'relative': False, 'position': "top"},
                title = {"text": "实际温度<br><span style='font-size:0.8em;color:gray'>体感" + f"{feels_like:.1f}°C</span>"},
                domain = {'x': [0, 1], 'y': [0, 1]}
            ))
            
            fig.update_layout(height=150)
            st.plotly_chart(fig, use_container_width=True)
            
            # 温度建议
            if abs(temp - feels_like) > 3:
                st.info(f"🌡️ 体感温度与实际温度相差 {abs(temp-feels_like):.1f}°C，请注意防护")
        
        with col2:
            # 风力信息
            wind_speed = data['wind_speed'].iloc[0] if 'wind_speed' in data.columns else 0
            wind_gusts = data['wind_gusts'].iloc[0] if 'wind_gusts' in data.columns else 0
            
            fig = go.Figure()
            
            fig.add_trace(go.Indicator(
                mode = "number+gauge",
                value = wind_speed,
                number = {'suffix': "m/s", "font": {"size": 30}},
                gauge = {
                    'shape': "bullet",
                    'axis': {'range': [0, 15]},
                    'bar': {'color': "darkblue"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 5], 'color': "lightgreen"},
                        {'range': [5, 10], 'color': "yellow"},
                        {'range': [10, 15], 'color': "red"}]
                },
                title = {"text": "风速<br><span style='font-size:0.8em;color:gray'>阵风" + f"{wind_gusts:.1f}m/s</span>"},
                domain = {'x': [0, 1], 'y': [0, 1]}
            ))
            
            fig.update_layout(height=150)
            st.plotly_chart(fig, use_container_width=True)
            
            # 风力建议
            if wind_speed > 8:
                st.warning("💨 风力较大，建议减少户外活动")
    
    def display_disease_details(self, data):
        """显示疾病风险详情"""
        st.markdown('<div class="section-title">🩺 疾病风险详情</div>', unsafe_allow_html=True)
        
        diseases_risk = self.calculate_disease_risks(data)
        
        # 按风险等级排序
        sorted_diseases = sorted(diseases_risk.items(), 
                               key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x[1]['level']], 
                               reverse=True)
        
        for disease, risk_data in sorted_diseases:
            disease_name = {
                'joint_pain': '🦵 关节痛',
                'rhinitis': '👃 过敏性鼻炎',
                'asthma': '🌬️ 哮喘',
                'skin_disease': '🧴 皮肤敏感',
                'cardiovascular': '❤️ 心脑血管疾病'
            }[disease]
            
            risk_class = f"health-{risk_data['level']}"
            risk_badge_class = f"risk-{risk_data['level']}"
            
            # 获取具体建议
            advice = self.get_disease_advice(disease, risk_data, data)
            
            st.markdown(f"""
            <div class="health-card {risk_class}">
                <div style="display: flex; justify-content: between; align-items: center;">
                    <div style="font-weight: bold; font-size: 1.1rem;">{disease_name}</div>
                    <span class="risk-badge {risk_badge_class}">{risk_data['level'].upper()}风险</span>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #555;">
                    {advice}
                </div>
                <div style="margin-top: 0.5rem;">
                    <div style="background: #e0e0e0; border-radius: 5px; height: 6px;">
                        <div style="width: {risk_data['score']/3*100}%; 
                                  background: {'#f44336' if risk_data['level'] == 'high' else '#ff9800' if risk_data['level'] == 'medium' else '#4caf50'}; 
                                  height: 6px; border-radius: 5px;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def get_disease_advice(self, disease, risk_data, weather_data):
        """获取疾病建议"""
        temp = weather_data['temperature'].iloc[0]
        humidity = weather_data['humidity'].iloc[0]
        
        advice_map = {
            'joint_pain': {
                'high': f"高湿度({humidity}%)和温度变化可能加重关节疼痛，建议减少户外活动，注意保暖",
                'medium': "注意关节保暖，避免长时间在潮湿环境中停留",
                'low': "天气条件对关节友好，适合适度活动"
            },
            'rhinitis': {
                'high': "当前天气条件可能增加过敏原传播，建议佩戴口罩，减少户外时间",
                'medium': "注意防护，避免接触花粉等过敏原",
                'low': "天气条件适宜，正常出行即可"
            },
            'asthma': {
                'high': f"高湿度({humidity}%)可能影响呼吸，避免剧烈运动，随身携带药物",
                'medium': "注意呼吸状况，避免刺激性环境",
                'low': "呼吸条件良好，保持正常活动"
            },
            'skin_disease': {
                'high': "注意防晒和皮肤保护，避免长时间暴晒",
                'medium': "做好基础防护，保持皮肤清洁",
                'low': "天气条件对皮肤友好，正常护理即可"
            },
            'cardiovascular': {
                'high': f"低温({temp:.1f}°C)增加心血管负担，注意保暖，避免剧烈温度变化",
                'medium': "注意身体状况，避免突然的剧烈运动",
                'low': "心血管负荷较轻，保持健康生活方式"
            }
        }
        
        return advice_map[disease][risk_data['level']]
    
    def display_forecast_info(self, city):
        """显示预测信息"""
        st.markdown('<div class="section-title">📅 未来3天趋势</div>', unsafe_allow_html=True)
        
        try:
            from data_sources import RealWeatherDataLoader
            loader = RealWeatherDataLoader(city)
            prediction_data = loader.get_forecast_data(3)
            
            if prediction_data is not None and not prediction_data.empty:
                # 创建简单的趋势图
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=prediction_data['date'].dt.strftime('%m/%d'),
                    y=prediction_data['temperature_2m_max'],
                    name='最高温度',
                    line=dict(color='red', width=2),
                    mode='lines+markers'
                ))
                
                fig.add_trace(go.Scatter(
                    x=prediction_data['date'].dt.strftime('%m/%d'),
                    y=prediction_data['temperature_2m_min'],
                    name='最低温度',
                    line=dict(color='blue', width=2),
                    mode='lines+markers'
                ))
                
                fig.update_layout(
                    height=200,
                    margin=dict(l=20, r=20, t=30, b=20),
                    showlegend=True,
                    xaxis_title="日期",
                    yaxis_title="温度 (°C)"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 简要趋势分析
                if len(prediction_data) > 1:
                    temp_change = prediction_data['temperature_2m_max'].iloc[-1] - prediction_data['temperature_2m_max'].iloc[0]
                    if abs(temp_change) > 5:
                        trend = "明显上升" if temp_change > 0 else "明显下降"
                        st.info(f"📈 未来几天温度{trend}，请关注天气变化")
                    else:
                        st.success("📊 未来几天温度变化平稳")
                    
            else:
                st.info("🔮 预测数据加载中...")
                
        except Exception as e:
            st.info("🔮 预测信息暂不可用")
    
    def calculate_disease_risks(self, data):
        """
        计算各种疾病风险
        """
        temp = data['temperature'].iloc[0]
        humidity = data['humidity'].iloc[0]
        pressure = data['pressure'].iloc[0] if 'pressure' in data.columns else 1013
        wind_speed = data['wind_speed'].iloc[0] if 'wind_speed' in data.columns else 0
        uv_index = data['uv_index'].iloc[0] if 'uv_index' in data.columns else 0
        
        diseases_risk = {}
        
        # 关节痛风险
        joint_risk_score = 0
        if humidity > 80:
            joint_risk_score += 2
        if abs(temp - 20) > 10:
            joint_risk_score += 1
        if pressure < 1000:
            joint_risk_score += 1
            
        if joint_risk_score >= 3:
            joint_level = "high"
        elif joint_risk_score >= 2:
            joint_level = "medium"
        else:
            joint_level = "low"
        
        diseases_risk['joint_pain'] = {
            'level': joint_level,
            'score': joint_risk_score
        }
        
        # 过敏性鼻炎风险
        rhinitis_risk_score = 0
        if wind_speed > 5:
            rhinitis_risk_score += 2
        if humidity < 30 or humidity > 70:
            rhinitis_risk_score += 1
            
        if rhinitis_risk_score >= 2:
            rhinitis_level = "high"
        elif rhinitis_risk_score >= 1:
            rhinitis_level = "medium"
        else:
            rhinitis_level = "low"
        
        diseases_risk['rhinitis'] = {
            'level': rhinitis_level,
            'score': rhinitis_risk_score
        }
        
        # 哮喘风险
        asthma_risk_score = 0
        if humidity > 80:
            asthma_risk_score += 2
        if temp < 10 or temp > 30:
            asthma_risk_score += 1
        if wind_speed > 8:
            asthma_risk_score += 1
            
        if asthma_risk_score >= 3:
            asthma_level = "high"
        elif asthma_risk_score >= 2:
            asthma_level = "medium"
        else:
            asthma_level = "low"
        
        diseases_risk['asthma'] = {
            'level': asthma_level,
            'score': asthma_risk_score
        }
        
        # 皮肤敏感风险
        skin_risk_score = 0
        if uv_index >= 6:
            skin_risk_score += 2
        if humidity > 80:
            skin_risk_score += 1
        if temp > 28:
            skin_risk_score += 1
            
        if skin_risk_score >= 3:
            skin_level = "high"
        elif skin_risk_score >= 2:
            skin_level = "medium"
        else:
            skin_level = "low"
        
        diseases_risk['skin_disease'] = {
            'level': skin_level,
            'score': skin_risk_score
        }
        
        # 心脑血管疾病风险
        cardio_risk_score = 0
        if temp < 10:
            cardio_risk_score += 2
        elif temp < 15:
            cardio_risk_score += 1
        if pressure < 1000:
            cardio_risk_score += 1
        if abs(temp - data['apparent_temperature'].iloc[0]) > 3:
            cardio_risk_score += 1
            
        if cardio_risk_score >= 3:
            cardio_level = "high"
        elif cardio_risk_score >= 2:
            cardio_level = "medium"
        else:
            cardio_level = "low"
        
        diseases_risk['cardiovascular'] = {
            'level': cardio_level,
            'score': cardio_risk_score
        }
        
        return diseases_risk
    
    def create_footer(self):
        """
        创建页脚
        """
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p>🏞️ 贵州天气健康分析系统 | 📱 PWA版本 | 实时更新</p>
            <p style="font-size: 0.7rem; color: #888;">
                支持离线使用 | 可安装到手机 | 后台数据更新
            </p>
        </div>
        """, unsafe_allow_html=True)

# ===== 应用启动 =====
if __name__ == "__main__":
    app = SimpleVisualWeatherApp()
    app.run()
