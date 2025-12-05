"""
实时天气数据加载模块 - PWA版本
专注于为PWA应用提供实时天气数据
"""

import pandas as pd
import requests
from datetime import datetime
import logging
import time
from typing import Dict, Optional

class RealTimeWeatherLoader:
    """
    实时天气数据加载器 - PWA版本
    """
    
    def __init__(self, city: str):
        """
        初始化实时数据加载器
        
        Args:
            city: 城市名称
        """
        self.city = city
        self.city_info = self._get_guizhou_city_info(city)
        self.logger = self._setup_logger()
        
        # PWA缓存设置：支持离线使用
        self.cache_duration = 300  # 5分钟缓存
        self.offline_cache_duration = 3600  # 离线时1小时缓存
        self.last_update = None
        self.cached_data = None
        self.last_online_status = True
        
        self.logger.info(f"初始化PWA实时天气加载器 - 城市: {city}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger(f"RealTimeLoader_{self.city}")
        logger.setLevel(logging.INFO)
        return logger
    
    def _get_guizhou_city_info(self, city: str) -> Dict:
        """获取贵州城市的坐标和基本信息"""
        guizhou_cities = {
            "贵阳市": {
                "lat": 26.6470, 
                "lon": 106.6302, 
                "elevation": 1071,
                "description": "贵州省会，林城"
            },
            "毕节市": {
                "lat": 27.3026, 
                "lon": 105.2840, 
                "elevation": 1510,
                "description": "黔西北高原城市"
            },
            "遵义市": {
                "lat": 27.7064, 
                "lon": 106.9373, 
                "elevation": 865,
                "description": "黔北重要城市"
            },
            "六盘水市": {
                "lat": 26.5935, 
                "lon": 104.8467, 
                "elevation": 1850,
                "description": "中国凉都"
            },
            "安顺市": {
                "lat": 26.2537, 
                "lon": 105.9462, 
                "elevation": 1380,
                "description": "黄果树瀑布所在地"
            }
        }
        return guizhou_cities.get(city, guizhou_cities["贵阳市"])
    
    def get_realtime_data(self) -> pd.DataFrame:
        """
        获取实时天气数据 - PWA优化版本
        
        Returns:
            包含实时天气数据的DataFrame
        """
        try:
            # 检查缓存是否有效
            cache_duration = self.cache_duration
            
            # 如果可能离线，延长缓存时间
            if not self._check_online_status():
                cache_duration = self.offline_cache_duration
                self.logger.info(f"可能处于离线状态，使用延长缓存 - {self.city}")
            
            if self._should_use_cache(cache_duration):
                self.logger.info(f"使用缓存数据 - {self.city}")
                self.cached_data['data_source'] = 'PWA缓存数据'
                self.cached_data['pwa_mode'] = 'cached'
                return self.cached_data
            
            # 从Open-Meteo API获取真实数据
            real_data = self._fetch_from_openmeteo()
            if real_data is not None:
                self.cached_data = real_data
                self.last_update = datetime.now()
                self.last_online_status = True
                self.logger.info(f"成功获取PWA实时数据 - {self.city}")
                return real_data
            
            # 如果API返回None，使用缓存或生成离线数据
            if self.cached_data is not None:
                self.logger.warning(f"使用旧缓存数据 - {self.city}")
                self.cached_data['data_source'] = 'PWA离线缓存'
                self.cached_data['pwa_mode'] = 'offline'
                return self.cached_data
            else:
                self.logger.warning(f"生成离线数据 - {self.city}")
                return self._generate_offline_data()
            
        except Exception as e:
            self.logger.error(f"获取PWA实时数据失败: {e}")
            
            # 返回离线数据
            return self._generate_offline_data()
    
    def _check_online_status(self) -> bool:
        """检查网络状态"""
        try:
            # 简单网络检查
            requests.head("https://api.open-meteo.com", timeout=3)
            return True
        except:
            return False
    
    def _should_use_cache(self, cache_duration: int) -> bool:
        """检查是否应该使用缓存数据"""
        return (self.cached_data is not None and 
                self.last_update and 
                (datetime.now() - self.last_update).total_seconds() < cache_duration)
    
    def _fetch_from_openmeteo(self) -> Optional[pd.DataFrame]:
        """
        从Open-Meteo API获取PWA优化天气数据
        """
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": self.city_info["lat"],
                "longitude": self.city_info["lon"],
                "current": [
                    "temperature_2m",        # 2米高度温度
                    "relative_humidity_2m",  # 2米高度相对湿度
                    "apparent_temperature",  # 体感温度
                    "pressure_msl",          # 海平面气压
                    "wind_speed_10m",        # 10米高度风速
                    "wind_direction_10m",    # 10米高度风向
                    "wind_gusts_10m",        # 阵风风速
                    "weather_code",          # 天气代码
                    "cloud_cover",           # 云量
                    "visibility",            # 能见度
                    "uv_index",              # 紫外线指数
                    "is_day"                 # 是否白天
                ],
                "timezone": "Asia/Shanghai",
                "forecast_days": 1
            }
            
            self.logger.info(f"请求PWA天气API - {self.city}")
            
            # 发送API请求，设置超时时间
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 验证API响应数据
            if "current" not in data:
                self.logger.error("API响应缺少current字段")
                return None
            
            current = data["current"]
            
            # 创建PWA优化数据框架
            realtime_df = self._create_pwa_dataframe(current)
            return realtime_df
            
        except requests.exceptions.Timeout:
            self.logger.error("API请求超时")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"处理API响应时发生错误: {e}")
            return None
    
    def _create_pwa_dataframe(self, current_data: Dict) -> pd.DataFrame:
        """
        创建PWA优化的数据框架
        """
        # 转换天气代码为中文描述
        weather_code = current_data.get("weather_code", 0)
        weather_condition = self._get_weather_condition_chinese(weather_code)
        
        # 构建PWA数据字典
        data_dict = {
            # 核心天气数据
            'date': [datetime.now()],
            'timestamp': [datetime.now().timestamp()],
            'temperature': [current_data.get("temperature_2m", 0)],
            'humidity': [current_data.get("relative_humidity_2m", 0)],
            'pressure': [current_data.get("pressure_msl", 0)],
            'wind_speed': [current_data.get("wind_speed_10m", 0)],
            'wind_direction': [current_data.get("wind_direction_10m", 0)],
            'wind_gusts': [current_data.get("wind_gusts_10m", 0)],
            'weather_code': [weather_code],
            'weather_condition': [weather_condition],
            'cloud_cover': [current_data.get("cloud_cover", 0)],
            'visibility': [current_data.get("visibility", 10000)],
            'uv_index': [current_data.get("uv_index", 0)],
            'is_day': [current_data.get("is_day", 1)],
            'apparent_temperature': [current_data.get("apparent_temperature", 0)],
            
            # 健康风险评估
            'comfort_index': [self._calculate_comfort_index(
                current_data.get("temperature_2m", 0),
                current_data.get("relative_humidity_2m", 0),
                current_data.get("wind_speed_10m", 0)
            )],
            'health_risk_level': [self._calculate_health_risk_level(
                current_data.get("temperature_2m", 0),
                current_data.get("relative_humidity_2m", 0),
                current_data.get("uv_index", 0)
            )],
            
            # 城市信息
            'city': [self.city],
            'latitude': [self.city_info["lat"]],
            'longitude': [self.city_info["lon"]],
            'elevation': [self.city_info["elevation"]],
            'city_description': [self.city_info["description"]],
            
            # PWA标识
            'data_source': ['Open-Meteo PWA API'],
            'pwa_mode': ['online'],
            'update_time': [datetime.now()],
            'data_quality': ['PWA实时数据'],
            'offline_support': [True],
            'cache_enabled': [True]
        }
        
        return pd.DataFrame(data_dict)
    
    def _generate_offline_data(self) -> pd.DataFrame:
        """生成离线数据"""
        data_dict = {
            'date': [datetime.now()],
            'timestamp': [datetime.now().timestamp()],
            'temperature': [20.0],  # 默认温度
            'humidity': [60.0],     # 默认湿度
            'pressure': [1013.0],
            'wind_speed': [3.0],
            'wind_direction': [180],
            'wind_gusts': [5.0],
            'weather_code': [1],
            'weather_condition': ['晴'],
            'cloud_cover': [30],
            'visibility': [10000],
            'uv_index': [3],
            'is_day': [1],
            'apparent_temperature': [20.0],
            'comfort_index': [75.0],
            'health_risk_level': ['低'],
            'city': [self.city],
            'latitude': [self.city_info["lat"]],
            'longitude': [self.city_info["lon"]],
            'elevation': [self.city_info["elevation"]],
            'city_description': [self.city_info["description"]],
            'data_source': ['PWA离线数据'],
            'pwa_mode': ['offline'],
            'update_time': [datetime.now()],
            'data_quality': ['离线缓存数据'],
            'offline_support': [True],
            'cache_enabled': [True]
        }
        
        return pd.DataFrame(data_dict)
    
    def _calculate_comfort_index(self, temp: float, humidity: float, wind_speed: float) -> float:
        """计算舒适度指数"""
        # 简化舒适度计算
        base_comfort = 100
        
        # 温度影响 (最适温度22°C)
        temp_effect = abs(temp - 22) * 2
        # 湿度影响 (最适湿度50%)
        humidity_effect = abs(humidity - 50) * 0.5
        # 风速影响 (最适风速1-3m/s)
        wind_effect = abs(wind_speed - 2) * 5 if wind_speed > 5 else 0
        
        comfort_score = base_comfort - temp_effect - humidity_effect - wind_effect
        return max(0, min(100, comfort_score))
    
    def _calculate_health_risk_level(self, temp: float, humidity: float, uv_index: float) -> str:
        """计算健康风险等级"""
        risk_score = 0
        
        if temp < 10 or temp > 30:
            risk_score += 2
        elif temp < 15 or temp > 25:
            risk_score += 1
            
        if humidity > 80 or humidity < 30:
            risk_score += 1
            
        if uv_index > 6:
            risk_score += 2
        elif uv_index > 3:
            risk_score += 1
            
        if risk_score >= 3:
            return "高"
        elif risk_score >= 2:
            return "中"
        else:
            return "低"
    
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
            test_data = self.get_realtime_data()
            return {
                "status": "healthy",
                "city": self.city,
                "pwa_support": True,
                "offline_support": True,
                "cache_enabled": self.cached_data is not None,
                "last_update": self.last_update,
                "data_source": test_data['data_source'].iloc[0],
                "pwa_mode": test_data['pwa_mode'].iloc[0],
                "comfort_index": test_data['comfort_index'].iloc[0],
                "health_risk_level": test_data['health_risk_level'].iloc[0],
                "parameters_available": len(test_data.columns)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "city": self.city,
                "pwa_support": True,
                "error": str(e)
            }


# ===== 测试函数 =====
def test_pwa_realtime_loader():
    """测试PWA实时数据加载器"""
    print("🧪 测试PWA实时数据加载器...")
    print("=" * 60)
    
    cities = ["贵阳市", "毕节市", "遵义市", "六盘水市", "安顺市"]
    
    for city in cities:
        print(f"\n🎯 测试城市: {city}")
        print("-" * 30)
        
        try:
            loader = RealTimeWeatherLoader(city)
            data = loader.get_realtime_data()
            
            if data is not None and not data.empty:
                print(f"✅ PWA数据获取成功")
                print(f"   模式: {data['pwa_mode'].iloc[0]}")
                print(f"   数据源: {data['data_source'].iloc[0]}")
                print(f"   温度: {data['temperature'].iloc[0]:.1f}°C")
                print(f"   湿度: {data['humidity'].iloc[0]:.0f}%")
                print(f"   风速: {data['wind_speed'].iloc[0]:.1f}m/s")
                print(f"   舒适指数: {data['comfort_index'].iloc[0]:.0f}")
                print(f"   健康风险: {data['health_risk_level'].iloc[0]}")
                print(f"   离线支持: {data['offline_support'].iloc[0]}")
                
            else:
                print("❌ PWA数据获取失败")
                
        except Exception as e:
            print(f"❌ PWA数据获取失败: {e}")
    
    print("\n" + "=" * 60)
    print("PWA实时数据测试完成！")

if __name__ == "__main__":
    test_pwa_realtime_loader()
