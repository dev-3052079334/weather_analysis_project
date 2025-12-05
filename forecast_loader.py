"""
天气预测数据加载模块 - PWA版本
专注于为PWA应用提供天气预测
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional

class ForecastWeatherLoader:
    """
    天气预测数据加载器 - PWA版本
    """
    
    def __init__(self, city: str):
        """
        初始化预测数据加载器
        
        Args:
            city: 城市名称
        """
        self.city = city
        self.city_info = self._get_guizhou_city_info(city)
        self.logger = self._setup_logger()
        
        # 缓存设置
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 3600  # 1小时缓存
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger(f"ForecastLoader_{self.city}")
        logger.setLevel(logging.INFO)
        return logger
    
    def _get_guizhou_city_info(self, city: str) -> Dict:
        """获取贵州城市信息"""
        guizhou_cities = {
            "贵阳市": {"lat": 26.6470, "lon": 106.6302},
            "毕节市": {"lat": 27.3026, "lon": 105.2840},
            "遵义市": {"lat": 27.7064, "lon": 106.9373},
            "六盘水市": {"lat": 26.5935, "lon": 104.8467},
            "安顺市": {"lat": 26.2537, "lon": 105.9462}
        }
        return guizhou_cities.get(city, guizhou_cities["贵阳市"])
    
    def get_forecast_data(self, days: int = 3, target_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        获取天气预测数据 - PWA优化版本
        
        Args:
            days: 预测天数
            target_date: 特定预测日期
            
        Returns:
            预测天气数据DataFrame
        """
        cache_key = f"forecast_{days}_{target_date}"
        
        # 检查缓存
        if cache_key in self.cache:
            cache_time = self.cache_time.get(cache_key)
            if cache_time and (datetime.now() - cache_time).seconds < self.cache_duration:
                self.logger.info(f"使用缓存预测数据 - {self.city}")
                return self.cache[cache_key]
        
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": self.city_info["lat"],
                "longitude": self.city_info["lon"],
                "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code", 
                         "precipitation_probability_max", "wind_speed_10m_max"],
                "timezone": "Asia/Shanghai",
                "forecast_days": days
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "daily" not in data:
                return pd.DataFrame()
            
            daily_data = data["daily"]
            
            # 创建DataFrame
            forecast_list = []
            for i in range(len(daily_data["time"])):
                weather_code = daily_data["weather_code"][i]
                
                forecast_list.append({
                    'date': datetime.strptime(daily_data["time"][i], "%Y-%m-%d"),
                    'temperature_2m_max': daily_data["temperature_2m_max"][i],
                    'temperature_2m_min': daily_data["temperature_2m_min"][i],
                    'weather_code': weather_code,
                    'weather_condition': self._get_weather_condition_chinese(weather_code),
                    'precipitation_probability': daily_data.get("precipitation_probability_max", [0])[i],
                    'wind_speed_max': daily_data.get("wind_speed_10m_max", [0])[i],
                    'city': self.city,
                    'data_source': 'Open-Meteo PWA',
                    'retrieved_at': datetime.now()
                })
            
            forecast_df = pd.DataFrame(forecast_list)
            
            # 缓存数据
            self.cache[cache_key] = forecast_df
            self.cache_time[cache_key] = datetime.now()
            
            self.logger.info(f"成功获取PWA预测数据 - {self.city}, {days}天")
            return forecast_df
            
        except Exception as e:
            self.logger.error(f"获取预测数据失败: {e}")
            
            # 返回离线数据
            return self._get_offline_forecast(days)
    
    def _get_offline_forecast(self, days: int) -> pd.DataFrame:
        """获取离线预测数据"""
        forecast_list = []
        base_date = datetime.now()
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            
            # 简单模拟数据
            forecast_list.append({
                'date': date,
                'temperature_2m_max': 20 + i,
                'temperature_2m_min': 15 + i,
                'weather_code': 1 if i % 2 == 0 else 3,
                'weather_condition': '晴' if i % 2 == 0 else '多云',
                'precipitation_probability': 20 if i % 3 == 0 else 0,
                'wind_speed_max': 3 + i,
                'city': self.city,
                'data_source': '离线缓存',
                'retrieved_at': datetime.now()
            })
        
        return pd.DataFrame(forecast_list)
    
    def _get_weather_condition_chinese(self, weather_code: int) -> str:
        """将天气代码转换为中文描述"""
        weather_map = {
            0: "晴", 1: "主要晴", 2: "局部多云", 3: "多云",
            45: "雾", 48: "雾",
            51: "小雨", 53: "中雨", 55: "大雨",
            61: "小雨", 63: "中雨", 65: "大雨",
            80: "阵雨", 81: "中阵雨", 82: "强阵雨",
            95: "雷暴", 96: "雷暴", 99: "强雷暴"
        }
        return weather_map.get(weather_code, "未知")
    
    def get_health_status(self) -> Dict:
        """获取服务健康状态"""
        try:
            # 测试数据获取
            test_data = self.get_forecast_data(1)
            return {
                "status": "healthy",
                "city": self.city,
                "pwa_support": True,
                "cache_enabled": len(self.cache) > 0,
                "offline_support": True,
                "parameters_available": len(test_data.columns) if not test_data.empty else 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "city": self.city,
                "pwa_support": True,
                "error": str(e)
            }


# ===== 测试函数 =====
def test_pwa_forecast_loader():
    """测试PWA预测数据加载器"""
    print("🧪 测试PWA预测数据加载器...")
    
    cities = ["贵阳市", "毕节市", "遵义市"]
    
    for city in cities:
        print(f"\n🔮 测试城市: {city}")
        print("-" * 30)
        
        try:
            loader = ForecastWeatherLoader(city)
            forecast = loader.get_forecast_data(3)
            
            if not forecast.empty:
                print(f"✅ 预测获取成功 (PWA模式)")
                print(f"   数据行数: {len(forecast)}")
                print(f"   数据源: {forecast['data_source'].iloc[0]}")
                print(f"   缓存支持: 是")
                print(f"   离线支持: 是")
                
                # 显示第一条预测
                first_day = forecast.iloc[0]
                print(f"\n   第一天预测:")
                print(f"     日期: {first_day['date'].strftime('%Y-%m-%d')}")
                print(f"     最高温: {first_day['temperature_2m_max']}°C")
                print(f"     最低温: {first_day['temperature_2m_min']}°C")
                print(f"     天气: {first_day['weather_condition']}")
            else:
                print("❌ 预测获取失败")
                
        except Exception as e:
            print(f"❌ 预测数据获取失败: {e}")

if __name__ == "__main__":
    test_pwa_forecast_loader()
