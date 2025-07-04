#!/usr/bin/env python3
"""简化的三层架构测试"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages/prompt/src'))

def test_basic_functionality():
    """测试基本功能"""
    print("🚀 测试Republic Prompt三层架构基本功能...\n")
    
    # 测试Simple层
    print("📦 Simple层测试:")
    from republic_prompt.simple import format_template
    result = format_template("Hello {{name}}!", name="World")
    assert result == "Hello World!"
    print("  ✅ 基本模板渲染")
    
    # 测试创建工作空间
    print("\n📦 Workspace层测试:")
    import tempfile
    from pathlib import Path
    from republic_prompt.workspace import Workspace, WorkspaceConfig
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        (workspace_path / "templates").mkdir()
        
        # 创建简单模板
        (workspace_path / "templates" / "test.md").write_text("Hello {{name}}!")
        
        # 创建工作空间
        workspace = Workspace(workspace_path)
        result = workspace.render("test", name="Workspace")
        assert "Hello Workspace!" in result.content
        print("  ✅ 工作空间渲染")
    
    # 测试Plugin层
    print("\n📦 Plugin层测试:")
    from republic_prompt.plugin import create_plugin_manager, create_function_plugin
    
    plugin_manager = create_plugin_manager()
    
    def double(x):
        return x * 2
    
    plugin = create_function_plugin("math", {"double": double})
    plugin_manager.register_plugin("math", plugin)
    
    assert "math" in plugin_manager.list_plugins()
    print("  ✅ 插件管理")
    
    print("\n🎉 所有基本功能测试通过！")
    print("\n🏗️ 三层架构成功实现:")
    print("  📦 Simple层 ✅")
    print("  📦 Workspace层 ✅") 
    print("  📦 Plugin层 ✅")
    
    print("\n🎯 架构特点:")
    print("  • 清晰的层次边界")
    print("  • 每层只依赖下层接口")
    print("  • 遵循Python哲学")
    print("  • 接口优于实现")

if __name__ == "__main__":
    test_basic_functionality()