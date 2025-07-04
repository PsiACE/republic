#!/usr/bin/env python3
"""测试Simple层的基本功能

这个测试文件验证Simple层的基本功能是否正常工作。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages/prompt/src'))

def test_simple_layer():
    """测试Simple层的基本功能"""
    print("🧪 测试Simple层功能...")
    
    try:
        # 测试基本的模板渲染
        from republic_prompt.simple import format_template
        
        # 测试1：基本模板渲染
        result = format_template("Hello {{name}}!", name="World")
        assert result == "Hello World!", f"Expected 'Hello World!', got '{result}'"
        print("✅ 基本模板渲染测试通过")
        
        # 测试2：带条件的模板
        template = "{% if count > 1 %}{{count}} items{% else %}1 item{% endif %}"
        result = format_template(template, count=3)
        assert result == "3 items", f"Expected '3 items', got '{result}'"
        print("✅ 条件模板测试通过")
        
        # 测试3：测试渲染器
        from republic_prompt.simple import create_renderer
        renderer = create_renderer()
        result = renderer.render("Hello {{name}}!", {"name": "Alice"})
        assert result.content == "Hello Alice!", f"Expected 'Hello Alice!', got '{result.content}'"
        print("✅ 渲染器测试通过")
        
        # 测试4：测试模型
        from republic_prompt.simple.models import TemplateModel
        template_model = TemplateModel(name="test", content="Hello {{name}}!")
        variables = template_model.get_variables()
        assert "name" in variables, f"Expected 'name' in variables, got {variables}"
        print("✅ 模型测试通过")
        
        print("🎉 Simple层所有测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_formatters():
    """测试格式化器"""
    print("\n🧪 测试格式化器...")
    
    try:
        from republic_prompt.simple.formatters import parse_frontmatter
        
        # 测试YAML frontmatter
        yaml_content = """---
title: Test
description: A test template
---
Hello {{name}}!"""
        
        metadata, content = parse_frontmatter(yaml_content)
        assert metadata.get("title") == "Test", f"Expected title 'Test', got {metadata.get('title')}"
        assert content.strip() == "Hello {{name}}!", f"Expected 'Hello {{name}}!', got '{content.strip()}'"
        print("✅ YAML frontmatter测试通过")
        
        # 测试没有frontmatter的情况
        plain_content = "Hello {{name}}!"
        metadata, content = parse_frontmatter(plain_content)
        assert metadata == {}, f"Expected empty metadata, got {metadata}"
        assert content == plain_content, f"Expected unchanged content, got '{content}'"
        print("✅ 纯文本测试通过")
        
        print("🎉 格式化器测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 格式化器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compatibility():
    """测试兼容性API"""
    print("\n🧪 测试兼容性API...")
    
    try:
        # 测试兼容的format函数
        from republic_prompt.compat import format
        
        # 这应该会显示警告但仍然工作
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = format("Hello {{name}}!", name="World")
            assert result == "Hello World!", f"Expected 'Hello World!', got '{result}'"
            assert len(w) > 0, "Expected deprecation warning"
            print("✅ 兼容性API测试通过（带警告）")
        
        print("🎉 兼容性测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始测试Republic Prompt新架构...")
    
    success = True
    success &= test_simple_layer()
    success &= test_formatters()
    success &= test_compatibility()
    
    if success:
        print("\n🎉 所有测试通过！新架构工作正常。")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，请检查实现。")
        sys.exit(1)