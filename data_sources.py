"""
数据源整合模块 - PWA版本
为PWA应用提供数据支持
"""

import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, Any

class RealWeatherDataLoader:
    """
    真实天气数据加载器 - PWA版本
    """
    
    def __init__(self, city: str):
        """
        初始化真实数据加载器
        
        Args:
            city: 城市名称
        """
        self.city = city
        self.modules = {}
        self.module_status = {}
        self.logger = self._setup_logger()
        self._initialize_all_modules()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger(f"RealDataLoader_{self.city}")
        logger.setLevel(logging.INFO)
        return logger
    
    def _initialize_all_modules(self):
        """初始化所有真实数据模块"""
        self.logger.info(f"开始初始化数据模块 - 城市: {self.city}")
        
        # 实时数据模块
        try:
            from realtime_loader import RealTimeWeatherLoader
            self.modules['realtime'] = RealTimeWeatherLoader(self.city)
            test_data = self.modules['realtime'].get_realtime_data()
            self.module_status['realtime'] = '✅ 实时数据'
            self.logger.info(f"实时数据模块初始化成功")
            
        except Exception as e:
            self.modules['realtime'] = None
            self.module_status['realtime'] = f'❌ 实时数据: {str(e)[:50]}'
            self.logger.error(f"实时数据模块初始化失败: {e}")
        
        # 预测数据模块
        try:
            from forecast_loader import ForecastWeatherLoader
            self.modules['forecast'] = ForecastWeatherLoader(self.city)
            test_data = self.modules['forecast'].get_forecast_data(3)
            self.module_status['forecast'] = '✅ 预测数据'
            self.logger.info(f"预测数据模块初始化成功")
            
        except Exception as e:
            self.modules['forecast'] = None
            self.module_status['forecast'] = f'❌ 预测数据: {str(e)[:50]}'
            self.logger.error(f"预测数据模块初始化失败: {e}")
        
        self.logger.info(f"数据模块初始化完成 - 城市: {self.city}")
    
    def get_realtime_data(self) -> pd.DataFrame:
        """
        获取实时天气数据
        
        Returns:
            实时天气数据DataFrame
            
        Raises:
            Exception: 当无法获取真实数据时抛出异常
        """
        if not self.modules.get('realtime'):
            raise Exception("实时数据模块未初始化")
        
        return self.modules['realtime'].get_realtime_data()
    
    def get_forecast_data(self, days: int = 3, target_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        获取天气预测数据
        
        Args:
            days: 预测天数
            target_date: 特定预测日期
            
        Returns:
            预测天气数据DataFrame
            
        Raises:
            Exception: 当无法获取真实数据时抛出异常
        """
        if not self.modules.get('forecast'):
            raise Exception("预测数据模块未初始化")
        
        return self.modules['forecast'].get_forecast_data(
            days=days, target_date=target_date
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取系统健康状态
        
        Returns:
            包含各模块健康状态的字典
        """
        health_status = {}
        
        # 实时模块健康状态
        if self.modules.get('realtime'):
            try:
                health_status['realtime'] = self.modules['realtime'].get_health_status()
                health_status['realtime']['data_type'] = '实时天气数据'
            except Exception as e:
                health_status['realtime'] = {
                    "status": "error",
                    "error": str(e),
                    "data_type": "实时天气数据"
                }
        else:
            health_status['realtime'] = {
                "status": "unavailable", 
                "error": "模块未加载",
                "data_type": "实时天气数据"
            }
        
        # 预测模块健康状态
        if self.modules.get('forecast'):
            try:
                health_status['forecast'] = self.modules['forecast'].get_health_status()
                health_status['forecast']['data_type'] = '预测数据'
            except Exception as e:
                health_status['forecast'] = {
                    "status": "error",
                    "error": str(e),
                    "data_type": "预测数据"
                }
        else:
            health_status['forecast'] = {
                "status": "unavailable",
                "error": "模块未加载", 
                "data_type": "预测数据"
            }
        
        # 总体系统状态
        healthy_modules = sum(1 for status in health_status.values() 
                            if status.get('status') == 'healthy')
        total_modules = len(health_status)
        
        health_status['system'] = {
            "status": "healthy" if healthy_modules == total_modules else "degraded",
            "healthy_modules": healthy_modules,
            "total_modules": total_modules,
            "overall_health": f"{healthy_modules}/{total_modules}",
            "service": "PWA天气健康分析",
            "pwa_support": True
        }
        
        return health_status


# ===== 测试函数 =====
def test_pwa_data_loader():
    """测试PWA数据加载器"""
    print("🧪 测试PWA数据加载器...")
    
    cities = ["贵阳市", "毕节市", "遵义市"]
    
    for city in cities:
        print(f"\n🌆 城市: {city}")
        print("-" * 30)
        
        try:
            loader = RealWeatherDataLoader(city)
            
            # 测试实时数据
            try:
                realtime_data = loader.get_realtime_data()
                print(f"✅ 数据获取成功")
                print(f"   温度: {realtime_data['temperature'].iloc[0]:.1f}°C")
                print(f"   湿度: {realtime_data['humidity'].iloc[0]:.0f}%")
                print(f"   PWA支持: 已启用")
            except Exception as e:
                print(f"❌ 数据获取失败: {e}")
            
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")

if __name__ == "__main__":
    test_pwa_data_loader()
