"""Workspace层加载器

基于Simple层的接口实现内容加载功能。
遵循"吃自己下一层的狗粮"原则，只使用Simple层的API。
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from .interfaces import BaseLoader
from ..simple.models import TemplateModel
from ..simple.formatters import parse_frontmatter

class TemplateLoader(BaseLoader):
    """模板加载器"""
    
    def can_handle(self, path: Path) -> bool:
        """检查是否可以处理该路径"""
        if path.is_file():
            return path.suffix.lower() in ['.md', '.markdown', '.txt']
        elif path.is_dir():
            return any(f.suffix.lower() in ['.md', '.markdown', '.txt'] 
                      for f in path.iterdir() if f.is_file())
        return False
    
    def load(self, path: Path) -> Dict[str, TemplateModel]:
        """加载模板"""
        templates = {}
        
        if path.is_file():
            template = self._load_template_file(path)
            if template:
                templates[template.name] = template
        elif path.is_dir():
            for file_path in path.glob('*.md'):
                template = self._load_template_file(file_path)
                if template:
                    templates[template.name] = template
        
        return templates
    
    def _load_template_file(self, file_path: Path) -> Optional[TemplateModel]:
        """加载单个模板文件"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 使用Simple层的格式化器解析frontmatter
            metadata, main_content = parse_frontmatter(content)
            
            return TemplateModel(
                name=file_path.stem,
                content=main_content,
                metadata=metadata
            )
        except Exception:
            return None

class SnippetLoader(BaseLoader):
    """片段加载器 - 复用模板加载器的逻辑"""
    
    def __init__(self):
        self._template_loader = TemplateLoader()
    
    def can_handle(self, path: Path) -> bool:
        """检查是否可以处理该路径"""
        return self._template_loader.can_handle(path)
    
    def load(self, path: Path) -> Dict[str, TemplateModel]:
        """加载片段（作为模板）"""
        return self._template_loader.load(path)

class FunctionLoader(BaseLoader):
    """函数加载器"""
    
    def can_handle(self, path: Path) -> bool:
        """检查是否可以处理该路径"""
        if path.is_file():
            return path.suffix == '.py'
        elif path.is_dir():
            return any(f.suffix == '.py' for f in path.glob('*.py'))
        return False
    
    def load(self, path: Path) -> Dict[str, Any]:
        """加载Python函数"""
        functions = {}
        
        if path.is_file():
            file_functions = self._load_python_file(path)
            functions.update(file_functions)
        elif path.is_dir():
            for py_file in path.glob('*.py'):
                if py_file.name.startswith('__'):
                    continue
                file_functions = self._load_python_file(py_file)
                functions.update(file_functions)
        
        return functions
    
    def _load_python_file(self, file_path: Path) -> Dict[str, Any]:
        """加载Python文件中的函数"""
        try:
            import importlib.util
            import inspect
            
            # 创建模块规格
            spec = importlib.util.spec_from_file_location(
                f"workspace_functions_{file_path.stem}",
                file_path
            )
            if not spec or not spec.loader:
                return {}
            
            # 加载模块
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            functions = {}
            
            # 检查是否有WORKSPACE_FUNCTIONS约定
            if hasattr(module, 'WORKSPACE_FUNCTIONS'):
                workspace_funcs = getattr(module, 'WORKSPACE_FUNCTIONS')
                if isinstance(workspace_funcs, dict):
                    functions.update(workspace_funcs)
            
            # 加载模块中的函数（不以_开头）
            for name in dir(module):
                if (not name.startswith('_') and 
                    name not in functions and  # 不覆盖WORKSPACE_FUNCTIONS
                    callable(getattr(module, name))):
                    
                    func = getattr(module, name)
                    # 只加载在这个模块中定义的函数
                    if (inspect.isfunction(func) and 
                        func.__module__ == module.__name__):
                        functions[name] = func
            
            return functions
            
        except Exception:
            return {}

class ContentLoader:
    """内容加载器 - 组合各种加载器"""
    
    def __init__(self):
        self.template_loader = TemplateLoader()
        self.snippet_loader = SnippetLoader()
        self.function_loader = FunctionLoader()
    
    def load_templates(self, templates_dir: Path) -> Dict[str, TemplateModel]:
        """加载模板"""
        if not templates_dir.exists():
            return {}
        return self.template_loader.load(templates_dir)
    
    def load_snippets(self, snippets_dir: Path) -> Dict[str, TemplateModel]:
        """加载片段"""
        if not snippets_dir.exists():
            return {}
        return self.snippet_loader.load(snippets_dir)
    
    def load_functions(self, functions_dir: Path) -> Dict[str, Any]:
        """加载函数"""
        if not functions_dir.exists():
            return {}
        return self.function_loader.load(functions_dir)
    
    def load_all(self, workspace_path: Path, config) -> tuple[
        Dict[str, TemplateModel], 
        Dict[str, TemplateModel], 
        Dict[str, Any]
    ]:
        """加载所有内容"""
        templates = self.load_templates(workspace_path / config.templates_dir)
        snippets = self.load_snippets(workspace_path / config.snippets_dir)
        functions = self.load_functions(workspace_path / config.functions_dir)
        
        return templates, snippets, functions

# 默认的内容加载器实例
default_content_loader = ContentLoader()