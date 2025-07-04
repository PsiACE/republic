"""Plugin层插件管理器

基于Workspace层构建插件管理功能。
遵循"吃自己下一层的狗粮"原则，只使用Workspace层的接口。
"""

from typing import Dict, Any, List, Optional
from .interfaces import IPlugin, IPluginManager, BasePlugin
from ..workspace.interfaces import IWorkspace

class PluginError(Exception):
    """插件异常"""
    pass

class PluginManager:
    """插件管理器实现"""
    
    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}
        self._plugin_registry: Dict[str, type] = {}
        self._context: Dict[str, Any] = {}
        
        # 注册内置插件
        self._register_builtin_plugins()
    
    def _register_builtin_plugins(self):
        """注册内置插件"""
        # 注册一些常用的插件类型
        self._plugin_registry["function_plugin"] = FunctionPlugin
        self._plugin_registry["filter_plugin"] = FilterPlugin
        self._plugin_registry["template_plugin"] = TemplatePlugin
    
    def register_plugin(self, name: str, plugin: IPlugin) -> None:
        """注册插件"""
        if name in self._plugins:
            raise PluginError(f"Plugin '{name}' already registered")
        
        self._plugins[name] = plugin
        
        # 初始化插件
        plugin.initialize(self._context)
    
    def unregister_plugin(self, name: str) -> bool:
        """取消注册插件"""
        if name not in self._plugins:
            return False
        
        plugin = self._plugins[name]
        plugin.cleanup()
        del self._plugins[name]
        
        return True
    
    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """获取插件"""
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """列出所有插件"""
        return list(self._plugins.keys())
    
    def apply_plugins(self, workspace: IWorkspace) -> IWorkspace:
        """应用所有插件到工作空间"""
        result_workspace = workspace
        
        for plugin_name, plugin in self._plugins.items():
            try:
                result_workspace = plugin.apply_to_workspace(result_workspace)
            except Exception as e:
                raise PluginError(f"Failed to apply plugin '{plugin_name}': {e}")
        
        return result_workspace
    
    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件（从注册表）"""
        if plugin_name in self._plugin_registry:
            plugin_class = self._plugin_registry[plugin_name]
            plugin = plugin_class(plugin_name)
            self.register_plugin(plugin_name, plugin)
            return True
        
        return False
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """设置全局上下文"""
        self._context.update(context)
        
        # 重新初始化所有插件
        for plugin in self._plugins.values():
            plugin.initialize(self._context)
    
    def register_plugin_type(self, name: str, plugin_class: type) -> None:
        """注册插件类型"""
        self._plugin_registry[name] = plugin_class

# 内置插件实现

class FunctionPlugin(BasePlugin):
    """函数插件 - 添加自定义函数到工作空间"""
    
    def __init__(self, name: str, functions: Optional[Dict[str, Any]] = None):
        super().__init__(name)
        self.functions = functions or {}
    
    def apply_to_workspace(self, workspace: IWorkspace) -> IWorkspace:
        """应用插件到工作空间"""
        for name, func in self.functions.items():
            workspace.add_function(name, func)
        
        return workspace
    
    def add_function(self, name: str, func: Any) -> None:
        """添加函数"""
        self.functions[name] = func

class FilterPlugin(BasePlugin):
    """过滤器插件 - 添加Jinja2过滤器"""
    
    def __init__(self, name: str, filters: Optional[Dict[str, Any]] = None):
        super().__init__(name)
        self.filters = filters or {}
    
    def apply_to_workspace(self, workspace: IWorkspace) -> IWorkspace:
        """应用插件到工作空间"""
        # 由于我们只能访问IWorkspace接口，这里需要一些方法来添加过滤器
        # 在实际实现中，可能需要扩展IWorkspace接口或者通过其他方式
        
        # 暂时通过添加函数的方式实现过滤器功能
        for name, filter_func in self.filters.items():
            workspace.add_function(f"filter_{name}", filter_func)
        
        return workspace
    
    def add_filter(self, name: str, filter_func: Any) -> None:
        """添加过滤器"""
        self.filters[name] = filter_func

class TemplatePlugin(BasePlugin):
    """模板插件 - 添加预定义模板"""
    
    def __init__(self, name: str, templates: Optional[Dict[str, str]] = None):
        super().__init__(name)
        self.templates = templates or {}
    
    def apply_to_workspace(self, workspace: IWorkspace) -> IWorkspace:
        """应用插件到工作空间"""
        # 由于IWorkspace接口可能不支持直接添加模板，
        # 这里需要扩展接口或者通过其他方式实现
        
        # 暂时将模板作为函数添加
        for name, template_content in self.templates.items():
            def create_template_func(content):
                def template_func(**kwargs):
                    from ..simple import format_template
                    return format_template(content, **kwargs)
                return template_func
            
            workspace.add_function(f"template_{name}", create_template_func(template_content))
        
        return workspace
    
    def add_template(self, name: str, content: str) -> None:
        """添加模板"""
        self.templates[name] = content

# 全局插件管理器实例
global_plugin_manager = PluginManager()