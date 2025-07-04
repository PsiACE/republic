"""Plugin层第三方集成

提供与第三方工具和库的集成功能。
"""

from typing import Dict, Any, List, Optional, Type
from .interfaces import BasePlugin
from ..workspace.interfaces import IWorkspace

class IntegrationRegistry:
    """集成注册表"""
    
    def __init__(self):
        self._integrations: Dict[str, Any] = {}
    
    def register_integration(self, name: str, integration: Any) -> None:
        """注册集成"""
        self._integrations[name] = integration
    
    def get_integration(self, name: str) -> Optional[Any]:
        """获取集成"""
        return self._integrations.get(name)
    
    def list_integrations(self) -> List[str]:
        """列出所有集成"""
        return list(self._integrations.keys())

# OpenAI 集成
class OpenAIIntegration(BasePlugin):
    """OpenAI API集成"""
    
    def __init__(self, name: str = "openai", api_key: Optional[str] = None):
        super().__init__(name)
        self.api_key = api_key
        self._client = None
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化OpenAI客户端"""
        super().initialize(context)
        
        # 尝试从上下文获取API密钥
        api_key = self.api_key or context.get("openai_api_key")
        
        if api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=api_key)
            except ImportError:
                print("OpenAI library not installed. Run: pip install openai")
    
    def apply_to_workspace(self, workspace: IWorkspace) -> IWorkspace:
        """应用集成到工作空间"""
        if self._client:
            # 添加OpenAI相关的函数
            def chat_completion(messages, model="gpt-3.5-turbo", **kwargs):
                if self._client:
                    response = self._client.chat.completions.create(
                        model=model,
                        messages=messages,
                        **kwargs
                    )
                    return response.choices[0].message.content
                return "OpenAI client not initialized"
            
            def completion(prompt, model="gpt-3.5-turbo-instruct", **kwargs):
                if self._client:
                    response = self._client.completions.create(
                        model=model,
                        prompt=prompt,
                        **kwargs
                    )
                    return response.choices[0].text
                return "OpenAI client not initialized"
            
            workspace.add_function("openai_chat", chat_completion)
            workspace.add_function("openai_complete", completion)
        
        return workspace

# LangChain 集成
class LangChainIntegration(BasePlugin):
    """LangChain集成"""
    
    def __init__(self, name: str = "langchain"):
        super().__init__(name)
        self._available = False
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化LangChain"""
        super().initialize(context)
        
        try:
            import langchain
            self._available = True
        except ImportError:
            print("LangChain library not installed. Run: pip install langchain")
    
    def apply_to_workspace(self, workspace: IWorkspace) -> IWorkspace:
        """应用集成到工作空间"""
        if self._available:
            def create_prompt_template(template_str):
                from langchain.prompts import PromptTemplate
                return PromptTemplate.from_template(template_str)
            
            def format_langchain_prompt(template_str, **kwargs):
                template = create_prompt_template(template_str)
                return template.format(**kwargs)
            
            workspace.add_function("langchain_template", create_prompt_template)
            workspace.add_function("langchain_format", format_langchain_prompt)
        
        return workspace

# Anthropic 集成
class AnthropicIntegration(BasePlugin):
    """Anthropic Claude集成"""
    
    def __init__(self, name: str = "anthropic", api_key: Optional[str] = None):
        super().__init__(name)
        self.api_key = api_key
        self._client = None
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化Anthropic客户端"""
        super().initialize(context)
        
        api_key = self.api_key or context.get("anthropic_api_key")
        
        if api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                print("Anthropic library not installed. Run: pip install anthropic")
    
    def apply_to_workspace(self, workspace: IWorkspace) -> IWorkspace:
        """应用集成到工作空间"""
        if self._client:
            def claude_completion(prompt, model="claude-3-sonnet-20240229", **kwargs):
                if self._client:
                    response = self._client.messages.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        **kwargs
                    )
                    return response.content[0].text
                return "Anthropic client not initialized"
            
            workspace.add_function("claude_complete", claude_completion)
        
        return workspace

# Ollama 集成（本地模型）
class OllamaIntegration(BasePlugin):
    """Ollama本地模型集成"""
    
    def __init__(self, name: str = "ollama", base_url: str = "http://localhost:11434"):
        super().__init__(name)
        self.base_url = base_url
        self._available = False
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化Ollama"""
        super().initialize(context)
        
        try:
            import requests
            # 测试连接
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self._available = True
        except Exception:
            print(f"Ollama not available at {self.base_url}")
    
    def apply_to_workspace(self, workspace: IWorkspace) -> IWorkspace:
        """应用集成到工作空间"""
        if self._available:
            def ollama_completion(prompt, model="llama2", **kwargs):
                try:
                    import requests
                    response = requests.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": model,
                            "prompt": prompt,
                            "stream": False,
                            **kwargs
                        }
                    )
                    if response.status_code == 200:
                        return response.json().get("response", "")
                    return f"Error: {response.status_code}"
                except Exception as e:
                    return f"Error: {e}"
            
            workspace.add_function("ollama_complete", ollama_completion)
        
        return workspace

# Jinja2 扩展集成
class Jinja2ExtensionIntegration(BasePlugin):
    """Jinja2扩展集成"""
    
    def __init__(self, name: str = "jinja2_ext", extensions: Optional[List[str]] = None):
        super().__init__(name)
        self.extensions = extensions or []
    
    def apply_to_workspace(self, workspace: IWorkspace) -> IWorkspace:
        """应用集成到工作空间"""
        # 这里需要与渲染器集成，但由于我们只能访问IWorkspace接口
        # 实际实现可能需要扩展接口或使用其他方式
        
        # 添加一些常用的Jinja2过滤器
        def markdown_filter(text):
            try:
                import markdown
                return markdown.markdown(text)
            except ImportError:
                return text
        
        def json_filter(obj):
            import json
            return json.dumps(obj)
        
        def base64_filter(text):
            import base64
            return base64.b64encode(text.encode()).decode()
        
        workspace.add_function("filter_markdown", markdown_filter)
        workspace.add_function("filter_json", json_filter)
        workspace.add_function("filter_base64", base64_filter)
        
        return workspace

# 全局集成注册表
global_integration_registry = IntegrationRegistry()

# 注册内置集成
global_integration_registry.register_integration("openai", OpenAIIntegration)
global_integration_registry.register_integration("langchain", LangChainIntegration)
global_integration_registry.register_integration("anthropic", AnthropicIntegration)
global_integration_registry.register_integration("ollama", OllamaIntegration)
global_integration_registry.register_integration("jinja2_ext", Jinja2ExtensionIntegration)

# 便捷函数
def get_integration(name: str) -> Optional[Any]:
    """获取集成"""
    return global_integration_registry.get_integration(name)

def create_integration_plugin(name: str, **kwargs) -> Optional[BasePlugin]:
    """创建集成插件"""
    integration_class = get_integration(name)
    if integration_class:
        return integration_class(**kwargs)
    return None