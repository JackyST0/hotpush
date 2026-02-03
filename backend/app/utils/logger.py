"""
日志配置模块
"""
import sys
import re
import logging
from app.config import settings


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # ANSI 颜色码
    COLORS = {
        'DEBUG': '\033[90m',     # 灰色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    GRAY = '\033[90m'
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    
    def format(self, record):
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # 格式化时间（灰色）
        time_str = f"{self.GRAY}{self.formatTime(record, '%H:%M:%S')}{self.RESET}"
        
        # 格式化消息
        message = record.getMessage()
        
        # 处理 [平台名称] 格式，高亮显示
        message = self._format_source_name(message, record.levelname)
        
        # 根据消息内容添加图标
        icon = self._get_icon(record.levelname, record.getMessage())
        
        return f"{time_str} {icon} {message}"
    
    def _format_source_name(self, message: str, level: str) -> str:
        """格式化消息中的 [平台名称]"""
        # 匹配 [xxx] 格式
        match = re.match(r'\[([^\]]+)\]\s*(.*)', message)
        if match:
            source_name = match.group(1)
            rest_msg = match.group(2)
            
            # 根据级别选择颜色
            if level == "ERROR":
                return f"{self.CYAN}[{source_name}]{self.RESET} {self.RED}{rest_msg}{self.RESET}"
            elif "成功" in rest_msg:
                return f"{self.CYAN}[{source_name}]{self.RESET} {self.GREEN}{rest_msg}{self.RESET}"
            else:
                return f"{self.CYAN}[{source_name}]{self.RESET} {rest_msg}"
        return message
    
    def _get_icon(self, level: str, message: str) -> str:
        """根据日志内容返回图标"""
        if "成功" in message:
            return f"{self.GREEN}✓{self.RESET}"
        elif "失败" in message or level == "ERROR":
            return f"{self.RED}✗{self.RESET}"
        elif level == "WARNING":
            return f"{self.YELLOW}!{self.RESET}"
        elif "启动" in message:
            return f"{self.CYAN}→{self.RESET}"
        elif "定时" in message or "任务" in message:
            return f"{self.GRAY}⏱{self.RESET}"
        else:
            return " "


def setup_logger(name: str = "hotpush") -> logging.Logger:
    """
    配置并返回 logger 实例

    Args:
        name: logger 名称

    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 根据 debug 设置日志级别
    level = logging.DEBUG if settings.debug else logging.INFO
    logger.setLevel(level)

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # 使用带颜色的格式化器
    console_handler.setFormatter(ColoredFormatter())

    logger.addHandler(console_handler)

    return logger


# 全局 logger 实例
logger = setup_logger()
