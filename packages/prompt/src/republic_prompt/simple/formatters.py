"""Simple层格式化器

提供frontmatter解析功能，支持YAML和TOML格式。
"""

from typing import Dict, Any, Optional
from .interfaces import BaseFormatter
from .exceptions import FormatError

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import yaml
except ImportError:
    yaml = None

class YamlFormatter(BaseFormatter):
    """YAML格式化器"""
    
    @property
    def format_name(self) -> str:
        return "yaml"
    
    def can_handle(self, content: str) -> bool:
        """检查是否为YAML frontmatter"""
        return content.strip().startswith('---')
    
    def parse(self, content: str) -> tuple[Dict[str, Any], str]:
        """解析YAML frontmatter"""
        if not yaml:
            raise FormatError("PyYAML is required for YAML frontmatter support", "yaml")
        
        if not self.can_handle(content):
            return {}, content
        
        try:
            # 按---分割
            parts = content.split('---', 2)
            if len(parts) < 3:
                return {}, content
            
            yaml_content = parts[1].strip()
            main_content = parts[2].lstrip('\n')
            
            if not yaml_content:
                return {}, main_content
            
            metadata = yaml.safe_load(yaml_content) or {}
            return metadata, main_content
            
        except Exception as e:
            raise FormatError(f"Failed to parse YAML frontmatter: {e}", "yaml")

class TomlFormatter(BaseFormatter):
    """TOML格式化器"""
    
    @property
    def format_name(self) -> str:
        return "toml"
    
    def can_handle(self, content: str) -> bool:
        """检查是否为TOML frontmatter"""
        return content.strip().startswith('+++')
    
    def parse(self, content: str) -> tuple[Dict[str, Any], str]:
        """解析TOML frontmatter"""
        if not tomllib:
            raise FormatError("tomllib/tomli is required for TOML frontmatter support", "toml")
        
        if not self.can_handle(content):
            return {}, content
        
        try:
            # 按+++分割
            parts = content.split('+++', 2)
            if len(parts) < 3:
                return {}, content
            
            toml_content = parts[1].strip()
            main_content = parts[2].lstrip('\n')
            
            if not toml_content:
                return {}, main_content
            
            metadata = tomllib.loads(toml_content)
            return metadata, main_content
            
        except Exception as e:
            raise FormatError(f"Failed to parse TOML frontmatter: {e}", "toml")

class NoOpFormatter(BaseFormatter):
    """无操作格式化器 - 用于没有frontmatter的内容"""
    
    @property
    def format_name(self) -> str:
        return "none"
    
    def can_handle(self, content: str) -> bool:
        """总是可以处理"""
        return True
    
    def parse(self, content: str) -> tuple[Dict[str, Any], str]:
        """不进行任何解析"""
        return {}, content

# 全局格式化器注册表
_formatters: Dict[str, BaseFormatter] = {
    "yaml": YamlFormatter(),
    "toml": TomlFormatter(),
    "none": NoOpFormatter(),
}

def register_formatter(name: str, formatter: BaseFormatter) -> None:
    """注册格式化器"""
    _formatters[name] = formatter

def get_formatter(name: str) -> Optional[BaseFormatter]:
    """获取格式化器"""
    return _formatters.get(name)

def get_all_formatters() -> Dict[str, BaseFormatter]:
    """获取所有格式化器"""
    return _formatters.copy()

def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """自动检测并解析frontmatter"""
    # 按优先级尝试不同的格式化器
    for formatter_name in ["yaml", "toml"]:
        formatter = _formatters.get(formatter_name)
        if formatter and formatter.can_handle(content):
            return formatter.parse(content)
    
    # 如果都不能处理，使用NoOpFormatter
    return _formatters["none"].parse(content)