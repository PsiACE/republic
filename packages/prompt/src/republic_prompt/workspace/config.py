"""Workspace层配置管理

定义工作空间的配置数据结构和加载逻辑。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class WorkspaceConfig:
    """工作空间配置"""
    name: Optional[str] = None
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # 目录配置
    templates_dir: str = "templates"
    snippets_dir: str = "snippets"
    functions_dir: str = "functions"
    
    # 渲染配置
    auto_escape: bool = False
    template_engine: str = "jinja2"
    
    # 扩展配置
    extensions: Dict[str, Any] = field(default_factory=dict)
    
    # 默认变量
    defaults: Dict[str, Any] = field(default_factory=dict)
    
    # 外部工作空间
    external_workspaces: Dict[str, str] = field(default_factory=dict)

def load_config_from_file(config_path: Path) -> WorkspaceConfig:
    """从文件加载配置"""
    if not config_path.exists():
        return WorkspaceConfig()
    
    try:
        # 尝试导入TOML解析器
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                # 如果没有TOML解析器，返回默认配置
                return WorkspaceConfig()
        
        content = config_path.read_text(encoding='utf-8')
        data = tomllib.loads(content)
        
        # 如果是republic.toml，提取prompts段
        if 'prompts' in data:
            data = data['prompts']
        
        return WorkspaceConfig(**data)
        
    except Exception:
        # 如果解析失败，返回默认配置
        return WorkspaceConfig()

def find_config_file(workspace_path: Path) -> Optional[Path]:
    """查找配置文件"""
    config_files = ['prompts.toml', 'republic.toml', '.prompts.toml']
    
    for config_file in config_files:
        config_path = workspace_path / config_file
        if config_path.exists():
            return config_path
    
    return None

def load_workspace_config(workspace_path: Path) -> WorkspaceConfig:
    """加载工作空间配置"""
    config_file = find_config_file(workspace_path)
    
    if config_file:
        return load_config_from_file(config_file)
    else:
        return WorkspaceConfig()