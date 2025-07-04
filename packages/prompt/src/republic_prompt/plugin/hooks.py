"""Plugin层钩子系统

提供灵活的钩子机制，支持在关键点执行自定义逻辑。
"""

from typing import Dict, Any, List, Optional, Callable
from .interfaces import BaseHook, IHook

class HookRegistry:
    """钩子注册表"""
    
    def __init__(self):
        self._hooks: Dict[str, List[IHook]] = {}
    
    def register_hook(self, hook_point: str, hook: IHook) -> None:
        """注册钩子"""
        if hook_point not in self._hooks:
            self._hooks[hook_point] = []
        
        self._hooks[hook_point].append(hook)
    
    def unregister_hook(self, hook_point: str, hook_name: str) -> bool:
        """取消注册钩子"""
        if hook_point not in self._hooks:
            return False
        
        hooks = self._hooks[hook_point]
        for i, hook in enumerate(hooks):
            if hook.name == hook_name:
                del hooks[i]
                return True
        
        return False
    
    def execute_hooks(self, hook_point: str, *args, **kwargs) -> List[Any]:
        """执行钩子点的所有钩子"""
        results = []
        
        if hook_point in self._hooks:
            for hook in self._hooks[hook_point]:
                try:
                    result = hook.execute(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    # 钩子执行失败时记录错误但继续执行其他钩子
                    print(f"Hook {hook.name} failed at {hook_point}: {e}")
        
        return results
    
    def list_hooks(self, hook_point: Optional[str] = None) -> Dict[str, List[str]]:
        """列出钩子"""
        if hook_point:
            hooks = self._hooks.get(hook_point, [])
            return {hook_point: [hook.name for hook in hooks]}
        
        return {
            point: [hook.name for hook in hooks]
            for point, hooks in self._hooks.items()
        }

class FunctionHook(BaseHook):
    """函数钩子 - 包装普通函数为钩子"""
    
    def __init__(self, name: str, func: Callable):
        super().__init__(name)
        self.func = func
    
    def execute(self, *args, **kwargs) -> Any:
        """执行钩子"""
        return self.func(*args, **kwargs)

class ConditionalHook(BaseHook):
    """条件钩子 - 只在满足条件时执行"""
    
    def __init__(self, name: str, hook: IHook, condition: Callable[..., bool]):
        super().__init__(name)
        self.hook = hook
        self.condition = condition
    
    def execute(self, *args, **kwargs) -> Any:
        """执行钩子"""
        if self.condition(*args, **kwargs):
            return self.hook.execute(*args, **kwargs)
        return None

class ChainHook(BaseHook):
    """链式钩子 - 将多个钩子链接在一起"""
    
    def __init__(self, name: str, hooks: List[IHook]):
        super().__init__(name)
        self.hooks = hooks
    
    def execute(self, *args, **kwargs) -> List[Any]:
        """执行钩子"""
        results = []
        for hook in self.hooks:
            result = hook.execute(*args, **kwargs)
            results.append(result)
        return results

# 预定义的钩子点
class HookPoints:
    """预定义的钩子点"""
    
    # 工作空间生命周期钩子
    WORKSPACE_BEFORE_LOAD = "workspace_before_load"
    WORKSPACE_AFTER_LOAD = "workspace_after_load"
    WORKSPACE_BEFORE_RENDER = "workspace_before_render"
    WORKSPACE_AFTER_RENDER = "workspace_after_render"
    
    # 模板生命周期钩子
    TEMPLATE_BEFORE_PARSE = "template_before_parse"
    TEMPLATE_AFTER_PARSE = "template_after_parse"
    TEMPLATE_BEFORE_RENDER = "template_before_render"
    TEMPLATE_AFTER_RENDER = "template_after_render"
    
    # 插件生命周期钩子
    PLUGIN_BEFORE_APPLY = "plugin_before_apply"
    PLUGIN_AFTER_APPLY = "plugin_after_apply"
    PLUGIN_BEFORE_INITIALIZE = "plugin_before_initialize"
    PLUGIN_AFTER_INITIALIZE = "plugin_after_initialize"

# 全局钩子注册表
global_hook_registry = HookRegistry()

# 便捷函数
def register_hook(hook_point: str, hook: IHook) -> None:
    """注册钩子到全局注册表"""
    global_hook_registry.register_hook(hook_point, hook)

def register_function_hook(hook_point: str, name: str, func: Callable) -> None:
    """注册函数钩子到全局注册表"""
    hook = FunctionHook(name, func)
    global_hook_registry.register_hook(hook_point, hook)

def execute_hooks(hook_point: str, *args, **kwargs) -> List[Any]:
    """执行全局钩子"""
    return global_hook_registry.execute_hooks(hook_point, *args, **kwargs)