# Republic Prompt 迁移指南

## 概述

Republic Prompt 已经重构为更清晰的三层架构：`plugin -> workspace -> simple`。新架构符合Python哲学，具有更清晰的边界和更好的可扩展性。

## 新架构优势

1. **清晰的层次边界**：每一层只依赖下一层的接口
2. **更好的可测试性**：每层都可以独立测试
3. **更强的可扩展性**：通过接口和注册机制支持扩展
4. **更符合Python哲学**：简单、直接、易用

## 迁移步骤

### 1. 简单模板渲染迁移

**旧代码：**
```python
from republic_prompt import format
result = format("Hello {{name}}!", name="World")
```

**新代码：**
```python
from republic_prompt.simple import format_template
result = format_template("Hello {{name}}!", name="World")
```

### 2. 自定义函数迁移

**旧代码：**
```python
from republic_prompt import format

def upper(text):
    return text.upper()

result = format(
    "Hello {{upper(name)}}!",
    custom_functions={"upper": upper},
    name="world"
)
```

**新代码：**
```python
from republic_prompt.simple import create_renderer

def upper(text):
    return text.upper()

renderer = create_renderer()
renderer.add_function("upper", upper)
result = renderer.render("Hello {{upper(name)}}!", {"name": "world"})
```

### 3. 工作空间迁移

**旧代码：**
```python
from republic_prompt import PromptWorkspace

workspace = PromptWorkspace.load("./workspace")
result = workspace.render("my-template", name="World")
```

**新代码：**
```python
from republic_prompt.workspace import load_workspace

workspace = load_workspace("./workspace")
result = workspace.render("my-template", name="World")
```

### 4. 插件系统迁移

**旧代码：**
```python
from republic_prompt import PromptWorkspace
from republic_prompt.loaders import function_loaders

function_loaders.register("rust", RustFunctionLoader())
workspace = PromptWorkspace.load("./workspace", function_loaders=["python", "rust"])
```

**新代码：**
```python
from republic_prompt.plugin import load_workspace_with_plugins

workspace = load_workspace_with_plugins("./workspace", plugins=["rust-functions"])
```

## 新架构详细说明

### Simple层（最底层）

**职责：** 基础模板渲染和数据模型

**主要API：**
- `format_template(template, **context)` - 最简单的模板渲染
- `create_renderer(**config)` - 创建渲染器实例
- `DefaultRenderer` - 基础渲染器实现

**使用场景：**
- 90%的用户只需要基本的模板渲染
- 不需要工作空间管理
- 不需要复杂的功能

**示例：**
```python
from republic_prompt.simple import format_template, create_renderer

# 最简单的使用
result = format_template("Hello {{name}}!", name="World")

# 需要更多控制
renderer = create_renderer(auto_escape=True)
renderer.add_function("upper", str.upper)
result = renderer.render("Hello {{upper(name)}}!", {"name": "world"})
```

### Workspace层（中间层）

**职责：** 工作空间管理、模板加载、配置管理

**主要API：**
- `load_workspace(path, **config)` - 加载工作空间
- `Workspace` - 工作空间类
- `ContentLoader` - 内容加载器
- `Registry` - 注册表

**使用场景：**
- 需要管理多个模板和片段
- 需要配置管理
- 需要模板之间的引用

**示例：**
```python
from republic_prompt.workspace import load_workspace

# 加载工作空间
workspace = load_workspace("./my-workspace")

# 渲染模板
result = workspace.render("greeting", name="World")

# 列出所有模板
templates = workspace.list_templates()
```

### Plugin层（最上层）

**职责：** 插件系统、扩展功能、第三方集成

**主要API：**
- `create_plugin_manager()` - 创建插件管理器
- `load_workspace_with_plugins(path, plugins)` - 加载带插件的工作空间
- `PluginManager` - 插件管理器

**使用场景：**
- 需要扩展功能
- 需要第三方集成
- 需要自定义插件

**示例：**
```python
from republic_prompt.plugin import load_workspace_with_plugins, create_plugin_manager

# 加载带插件的工作空间
workspace = load_workspace_with_plugins("./workspace", plugins=["my-plugin"])

# 自定义插件管理
plugin_manager = create_plugin_manager()
plugin_manager.register_plugin("my-plugin", MyPlugin())
```

## 兼容性说明

### 向后兼容性

所有旧的API仍然可以使用，但会显示废弃警告：

```python
# 这些仍然可以工作，但会显示警告
from republic_prompt import format, PromptWorkspace
```

### 迁移时间线

- **Phase 1（当前）**：新架构可用，旧API显示警告
- **Phase 2（下个版本）**：旧API标记为将废弃
- **Phase 3（未来版本）**：完全移除旧API

## 最佳实践

### 1. 选择合适的层级

- **简单模板渲染**：使用Simple层
- **工作空间管理**：使用Workspace层
- **插件和扩展**：使用Plugin层

### 2. 遵循依赖方向

- Plugin层只依赖Workspace层
- Workspace层只依赖Simple层
- 不要跨层依赖

### 3. 使用接口而非实现

```python
# 推荐：使用接口
from republic_prompt.simple import IRenderer

# 不推荐：直接使用实现
from republic_prompt.simple.renderer import DefaultRenderer
```

### 4. 利用注册机制

```python
# 注册自定义格式化器
from republic_prompt.simple.formatters import register_formatter
register_formatter("my-format", MyFormatter())

# 注册自定义插件
from republic_prompt.plugin import create_plugin_manager
plugin_manager = create_plugin_manager()
plugin_manager.register_plugin("my-plugin", MyPlugin())
```

## 常见问题

### Q: 为什么要重构？

A: 新架构提供了更清晰的边界、更好的可测试性和更强的可扩展性，符合Python哲学。

### Q: 旧代码还能工作吗？

A: 是的，我们提供了完整的向后兼容性，旧代码仍然可以工作，但会显示警告。

### Q: 性能有影响吗？

A: 新架构的性能与旧架构相当，甚至在某些情况下更好。

### Q: 如何逐步迁移？

A: 建议从Simple层开始，逐步迁移到Workspace层和Plugin层。

## 获取帮助

- 查看[API文档](https://github.com/your-repo/republic-prompt/blob/main/docs/api.md)
- 查看[示例代码](https://github.com/your-repo/republic-prompt/tree/main/examples)
- 提交[Issue](https://github.com/your-repo/republic-prompt/issues)
- 加入[讨论](https://github.com/your-repo/republic-prompt/discussions)