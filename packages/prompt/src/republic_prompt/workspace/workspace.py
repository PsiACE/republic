"""Workspace层核心实现

基于Simple层构建工作空间功能。
遵循"吃自己下一层的狗粮"原则，只使用Simple层的接口。
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from .interfaces import BaseWorkspace
from .config import WorkspaceConfig, load_workspace_config
from .loaders import ContentLoader
from .registry import Registry
from ..simple.interfaces import IRenderer
from ..simple.models import RenderResult, TemplateModel
from ..simple import create_renderer

class WorkspaceError(Exception):
    """工作空间异常"""
    pass

class Workspace(BaseWorkspace):
    """工作空间实现"""
    
    def __init__(self, path: Union[str, Path], config: Optional[WorkspaceConfig] = None):
        """初始化工作空间
        
        Args:
            path: 工作空间路径
            config: 工作空间配置，如果为None则自动加载
        """
        self.path = Path(path).resolve()
        
        if not self.path.exists():
            raise WorkspaceError(f"Workspace directory not found: {self.path}")
        
        if not self.path.is_dir():
            raise WorkspaceError(f"Workspace path is not a directory: {self.path}")
        
        # 加载配置
        if config is None:
            config = load_workspace_config(self.path)
        
        super().__init__(self.path, config)
        
        # 初始化组件
        self._loader = ContentLoader()
        self._registry = Registry()
        self._renderer: Optional[IRenderer] = None
        
        # 加载内容
        self._templates: Dict[str, TemplateModel] = {}
        self._snippets: Dict[str, TemplateModel] = {}
        self._functions: Dict[str, Any] = {}
        
        self._load_content()
        self._setup_renderer()
    
    def _load_content(self):
        """加载工作空间内容"""
        try:
            templates, snippets, functions = self._loader.load_all(self.path, self.config)
            
            self._templates = templates
            self._snippets = snippets
            self._functions = functions
            
            # 注册到注册表（注意：这里应该注册内容，而不是loader）
            # 实际上我们不需要在这里注册，因为内容已经存储在对象属性中了
            for name, func in functions.items():
                self._registry.register_function(name, func)
            
        except Exception as e:
            raise WorkspaceError(f"Failed to load workspace content: {e}")
    
    def _setup_renderer(self):
        """设置渲染器"""
        # 使用Simple层的API创建渲染器
        self._renderer = create_renderer(
            auto_escape=self.config.auto_escape
        )
        
        # 添加自定义函数
        for name, func in self._functions.items():
            self._renderer.add_function(name, func)
        
        # 添加片段访问函数
        def include_snippet(snippet_name: str) -> str:
            """包含片段"""
            if snippet_name in self._snippets:
                return self._snippets[snippet_name].content
            return f"<!-- Snippet '{snippet_name}' not found -->"
        
        self._renderer.add_function('include_snippet', include_snippet)
        self._renderer.add_filter('snippet', include_snippet)
    
    def render(self, template_name: str, **context) -> RenderResult:
        """渲染模板"""
        if template_name not in self._templates:
            available = ", ".join(self._templates.keys())
            raise WorkspaceError(
                f"Template '{template_name}' not found. Available templates: {available}"
            )
        
        template = self._templates[template_name]
        
        # 合并默认变量和上下文
        render_context = {}
        if self.config.defaults:
            render_context.update(self.config.defaults)
        render_context.update(context)
        
        # 使用Simple层的渲染器进行渲染
        if self._renderer is None:
            raise WorkspaceError("Renderer not initialized")
        
        result = self._renderer.render_template(template, render_context)
        
        return result
    
    def get_template(self, name: str) -> Optional[TemplateModel]:
        """获取模板"""
        return self._templates.get(name)
    
    def get_snippet(self, name: str) -> Optional[TemplateModel]:
        """获取片段"""
        return self._snippets.get(name)
    
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self._templates.keys())
    
    def list_snippets(self) -> List[str]:
        """列出所有片段"""
        return list(self._snippets.keys())
    
    def list_functions(self) -> List[str]:
        """列出所有函数"""
        return list(self._functions.keys())
    
    def add_function(self, name: str, func: Any) -> None:
        """添加自定义函数"""
        self._functions[name] = func
        self._registry.register_function(name, func)
        
        # 更新渲染器
        if self._renderer:
            self._renderer.add_function(name, func)
    
    def reload(self) -> None:
        """重新加载工作空间"""
        self._load_content()
        self._setup_renderer()
    
    def info(self) -> Dict[str, Any]:
        """获取工作空间信息"""
        return {
            "name": self.config.name,
            "description": self.config.description,
            "version": self.config.version,
            "path": str(self.path),
            "templates": len(self._templates),
            "snippets": len(self._snippets),
            "functions": len(self._functions),
            "config": {
                "templates_dir": self.config.templates_dir,
                "snippets_dir": self.config.snippets_dir,
                "functions_dir": self.config.functions_dir,
                "auto_escape": self.config.auto_escape,
            }
        }
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (f"Workspace(path='{self.path}', "
                f"templates={len(self._templates)}, "
                f"snippets={len(self._snippets)}, "
                f"functions={len(self._functions)})")
    
    @classmethod
    def load(cls, path: Union[str, Path], **config_overrides) -> "Workspace":
        """加载工作空间的便捷方法
        
        Args:
            path: 工作空间路径
            **config_overrides: 配置覆盖
            
        Returns:
            工作空间实例
        """
        workspace_path = Path(path)
        
        # 加载基础配置
        config = load_workspace_config(workspace_path)
        
        # 应用配置覆盖
        if config_overrides:
            # 创建新的配置对象
            config_dict = {
                "name": config.name,
                "description": config.description,
                "version": config.version,
                "templates_dir": config.templates_dir,
                "snippets_dir": config.snippets_dir,
                "functions_dir": config.functions_dir,
                "auto_escape": config.auto_escape,
                "template_engine": config.template_engine,
                "extensions": config.extensions.copy(),
                "defaults": config.defaults.copy(),
                "external_workspaces": config.external_workspaces.copy(),
            }
            config_dict.update(config_overrides)
            config = WorkspaceConfig(**config_dict)
        
        return cls(workspace_path, config)

# 便捷函数
def load_workspace(path: Union[str, Path], **config) -> Workspace:
    """加载工作空间
    
    Args:
        path: 工作空间路径
        **config: 配置选项
        
    Returns:
        工作空间实例
    """
    return Workspace.load(path, **config)

def create_workspace(path: Union[str, Path], config: WorkspaceConfig) -> Workspace:
    """创建工作空间
    
    Args:
        path: 工作空间路径
        config: 工作空间配置
        
    Returns:
        工作空间实例
    """
    return Workspace(path, config)