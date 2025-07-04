# Republic 三层架构重构设计

## 目标

将当前的republic设计重构为一个清晰的三层架构：`plugin -> workspace -> simple`，符合Python哲学和最佳实践。

## 设计原则

1. **明确的层次边界**：每一层只依赖下一层的接口，不跨层依赖
2. **吃自己下一层的狗粮**：每一层都使用下一层的API，验证其完整性
3. **接口优于实现**：使用抽象基类(ABC)和协议(Protocol)定义层间接口
4. **单一职责**：每一层有明确的职责划分
5. **可扩展性**：通过接口和注册机制支持扩展

## 三层架构设计

### 1. Simple层（最底层）
**职责**：提供基础的模板渲染和数据模型

**核心组件**：
- `models.py` - 数据模型定义
- `interfaces.py` - 接口定义
- `renderer.py` - 基础渲染器
- `formatters.py` - 格式化器（YAML/TOML等）
- `exceptions.py` - 异常定义

**对外接口**：
- `IRenderer` - 渲染器接口
- `IFormatter` - 格式化器接口
- `IRenderContext` - 渲染上下文接口

**API示例**：
```python
from republic_prompt.simple import format_template, DefaultRenderer

# 最简单的使用
result = format_template("Hello {{name}}!", name="World")

# 使用渲染器
renderer = DefaultRenderer()
result = renderer.render(template, context)
```

### 2. Workspace层（中间层）
**职责**：基于Simple层构建工作空间管理功能

**核心组件**：
- `workspace.py` - 工作空间管理
- `loaders.py` - 内容加载器
- `registry.py` - 注册表管理
- `config.py` - 配置管理

**依赖关系**：
- 只依赖Simple层的接口
- 使用Simple层的渲染器进行模板渲染
- 使用Simple层的格式化器解析文件

**对外接口**：
- `IWorkspace` - 工作空间接口
- `ILoader` - 加载器接口
- `IRegistry` - 注册表接口

**API示例**：
```python
from republic_prompt.workspace import Workspace

# 使用工作空间
workspace = Workspace.load("./my-workspace")
result = workspace.render("my-template", **context)
```

### 3. Plugin层（最上层）
**职责**：基于Workspace层提供插件系统和高级功能

**核心组件**：
- `plugin_manager.py` - 插件管理器
- `extensions.py` - 扩展功能
- `hooks.py` - 钩子系统
- `integrations.py` - 第三方集成

**依赖关系**：
- 只依赖Workspace层的接口
- 使用Workspace层的工作空间进行操作
- 通过插件系统扩展功能

**对外接口**：
- `IPlugin` - 插件接口
- `IExtension` - 扩展接口
- `IHook` - 钩子接口

**API示例**：
```python
from republic_prompt.plugin import PluginManager, load_workspace_with_plugins

# 使用插件
plugin_manager = PluginManager()
plugin_manager.register_plugin("my-plugin", MyPlugin())

workspace = load_workspace_with_plugins("./workspace", plugins=["my-plugin"])
```

## 实现策略

### 阶段1：重构Simple层
1. 提取核心接口定义
2. 重构模型和渲染器
3. 简化依赖关系
4. 添加单元测试

### 阶段2：重构Workspace层
1. 基于Simple层接口重构工作空间
2. 重构加载器系统
3. 实现配置管理
4. 添加集成测试

### 阶段3：实现Plugin层
1. 设计插件系统
2. 实现扩展机制
3. 添加常用插件
4. 完善文档

## 文件结构设计

```
src/republic_prompt/
├── __init__.py           # 统一入口
├── simple/              # Simple层
│   ├── __init__.py
│   ├── interfaces.py    # 接口定义
│   ├── models.py        # 数据模型
│   ├── renderer.py      # 渲染器
│   ├── formatters.py    # 格式化器
│   └── exceptions.py    # 异常
├── workspace/           # Workspace层
│   ├── __init__.py
│   ├── interfaces.py    # 接口定义
│   ├── workspace.py     # 工作空间
│   ├── loaders.py       # 加载器
│   ├── registry.py      # 注册表
│   └── config.py        # 配置
├── plugin/              # Plugin层
│   ├── __init__.py
│   ├── interfaces.py    # 接口定义
│   ├── manager.py       # 插件管理器
│   ├── extensions.py    # 扩展功能
│   ├── hooks.py         # 钩子系统
│   └── integrations.py  # 第三方集成
└── compat.py           # 兼容性层
```

## 向后兼容性

为了保持向后兼容，我们将：
1. 保留原有的API入口
2. 添加兼容性层(`compat.py`)
3. 提供迁移指南
4. 逐步废弃旧接口

## 测试策略

1. **单元测试**：每个层都有完整的单元测试
2. **集成测试**：测试层间集成
3. **端到端测试**：测试完整的用户场景
4. **性能测试**：确保重构不影响性能

## 文档更新

1. 更新API文档
2. 添加架构说明
3. 提供迁移指南
4. 增加最佳实践示例