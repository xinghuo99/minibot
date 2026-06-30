"""Core Agent with ReAct (Reasoning + Acting) loop."""

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from codebot.core.config import AppConfig, LLMConfig
from codebot.core.llm import LLMClient
from codebot.core.memory import ConversationMemory
from codebot.tools.file_ops import FileOps, TOOL_DEFINITION as FILE_TOOL_DEF
from codebot.tools.cmd_exec import CmdExec, TOOL_DEFINITION as CMD_TOOL_DEF
from codebot.tools.pkg_mgr import PkgMgr, TOOL_DEFINITION as PKG_TOOL_DEF
from codebot.tools.git_ops import GitOps, TOOL_DEFINITION as GIT_TOOL_DEF
from codebot.utils.output import output


class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    DONE = "done"
    ERROR = "error"


@dataclass
class AgentStep:
    """Records a single step in the agent's execution."""
    step_num: int
    thought: str = ""
    action: str = ""
    action_input: dict[str, Any] | None = None
    observation: str = ""
    state: AgentState = AgentState.IDLE


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self._tools: dict[str, Any] = {}
        self._definitions: list[dict] = []
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register all built-in tools."""
        self.file_ops = FileOps(self.workspace)
        self.cmd_exec = CmdExec(self.workspace)
        self.pkg_mgr = PkgMgr(self.workspace)
        self.git_ops = GitOps(self.workspace)

        self.register("file_ops", self.file_ops.execute, FILE_TOOL_DEF)
        self.register("cmd_exec", self.cmd_exec.execute, CMD_TOOL_DEF)
        self.register("pkg_mgr", self.pkg_mgr.execute, PKG_TOOL_DEF)
        self.register("git_ops", self.git_ops.execute, GIT_TOOL_DEF)

    def set_workspace(self, workspace: Path) -> None:
        """Update the workspace for all tools."""
        self.workspace = workspace
        self.file_ops = FileOps(workspace)
        self.cmd_exec = CmdExec(workspace)
        self.pkg_mgr = PkgMgr(workspace)
        self.git_ops = GitOps(workspace)
        self._tools["file_ops"] = self.file_ops.execute
        self._tools["cmd_exec"] = self.cmd_exec.execute
        self._tools["pkg_mgr"] = self.pkg_mgr.execute
        self._tools["git_ops"] = self.git_ops.execute

    def register(
        self, name: str, handler: Callable, definition: dict
    ) -> None:
        """Register a tool with its handler and OpenAI function definition."""
        self._tools[name] = handler
        self._definitions.append(definition)
        output.debug(f"Tool registered: {name}")

    def execute(self, name: str, **kwargs) -> str:
        """Execute a tool and return the result as a JSON string."""
        handler = self._tools.get(name)
        if not handler:
            return json.dumps({"success": False, "error": f"Unknown tool: {name}"})

        try:
            result = handler(**kwargs)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            output.error(f"Tool '{name}' execution failed: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @property
    def definitions(self) -> list[dict]:
        return self._definitions

    @property
    def names(self) -> list[str]:
        return list(self._tools.keys())


class Agent:
    """Core Agent with ReAct loop for reasoning and tool use."""

    PYTHON_EXPERT_SYSTEM = """你是一个顶级的Python软件架构专家和Python编程高手。你的角色定义：

## 角色1：Python软件架构专家和顶级编程高手
你是Python软件领域的顶级专家，具备以下所有专业能力：
- **软件架构设计**：精通微服务、分层架构、事件驱动、CQRS等架构模式，能设计高内聚低耦合的系统
- **Python编程**：精通Python所有高级特性（装饰器、元类、生成器、协程、类型注解、描述符等）
- **代码质量**：擅长编写PEP 8规范、类型安全、高可读性、高可维护性的代码
- **调试专家**：精通pdb、traceback分析、内存分析、性能profiling等调试技术
- **测试专家**：精通pytest、单元测试、集成测试、端到端测试、mock、fixture等
- **性能优化**：精通算法优化、异步编程、缓存策略、数据库优化、C扩展等
- **打包部署**：精通PyInstaller、Nuitka、setuptools、Docker、CI/CD等
- **环境管理**：精通venv、conda、poetry、pipenv等虚拟环境管理

## 角色2：AI Skills专家
你是AI Skills领域的顶级专家，精通Skill的完整生命周期管理：
- **Skill设计**：能设计清晰、可复用、可扩展的Skill规范和模板
- **Skill实现**：能编写高质量的Skill代码，遵循最佳实践
- **Skill进化**：能根据反馈和使用数据自主优化和进化Skill
- **Skill调试**：能快速定位和修复Skill中的问题
- **Skill测试**：能编写全面的自动化测试确保Skill质量

## 工作原则
1. 始终生成高质量、可直接运行的Python代码
2. 代码必须包含完整的类型注解和文档字符串
3. 自动生成全面的测试用例
4. 优先使用标准库，再考虑第三方依赖
5. 每次操作前先思考，再执行
6. 执行后观察结果，根据结果调整策略
7. 最终输出完整的代码、测试和运行说明"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.llm = LLMClient(config.llm)
        self.memory = ConversationMemory()
        self.tools = ToolRegistry(config.agent.workspace_dir)
        self.state = AgentState.IDLE
        self.steps: list[AgentStep] = []

        # Initialize with system prompt
        self.memory.add_system(self.PYTHON_EXPERT_SYSTEM)

    def run(self, user_input: str, stream: bool = False):
        """Run the agent with a user input."""
        self.state = AgentState.THINKING
        self.memory.add_user(user_input)
        self.steps = []
        step_num = 0

        output.print(f"\n[bold blue]▶ 用户请求:[/bold blue] {user_input}\n")

        for iteration in range(self.config.agent.max_iterations):
            step_num += 1
            step = AgentStep(step_num=step_num, state=AgentState.THINKING)

            # 1. Get LLM response
            response = self._get_llm_response()

            # 2. Check if we're done
            if response.get("finish_reason") == "stop":
                step.state = AgentState.DONE
                step.thought = response.get("content", "")
                self.steps.append(step)
                self.state = AgentState.DONE
                self._display_final_output(response.get("content", ""))
                return {
                    "success": True,
                    "output": response.get("content", ""),
                    "steps": len(self.steps),
                    "usage": response.get("usage", {}),
                }

            # 3. Process tool calls
            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                step.state = AgentState.DONE
                step.thought = response.get("content", "")
                self.steps.append(step)
                self.state = AgentState.DONE
                self._display_final_output(response.get("content", ""))
                return {
                    "success": True,
                    "output": response.get("content", ""),
                    "steps": len(self.steps),
                    "usage": response.get("usage", {}),
                }

            step.state = AgentState.ACTING
            for tc in tool_calls:
                step.action = tc["name"]
                step.action_input = tc["arguments"]

                output.print(
                    f"  [yellow]🔧 {tc['name']}[/yellow]"
                    f"({json.dumps(tc['arguments'], ensure_ascii=False)})"
                )

                # Execute tool
                result = self.tools.execute(tc["name"], **tc["arguments"])
                if not step.observation:
                    step.observation = result[:500] + "..." if len(result) > 500 else result
                else:
                    step.observation += "\n" + (result[:500] + "..." if len(result) > 500 else result)

                # Add tool result to memory
                self.memory.add_tool_result(tc["id"], tc["name"], result)

                # Show brief observation
                result_preview = result[:200] + "..." if len(result) > 200 else result
                output.print(f"  [dim]→ {result_preview}[/dim]", markup=False)

            self.steps.append(step)

        # Max iterations reached
        self.state = AgentState.ERROR
        return {
            "success": False,
            "output": "Max iterations reached without completion",
            "steps": len(self.steps),
            "usage": {},
        }

    def _get_llm_response(self) -> dict[str, Any]:
        """Get a response from the LLM."""
        messages = self.memory.to_messages()
        return self.llm.chat(
            messages=messages,
            tools=self.tools.definitions,
            tool_choice="auto",
        )

    def run_stream(self, user_input: str):
        """流式运行Agent，实时yield每个步骤的事件。

        Yields:
            dict: 事件类型包括:
                - {"type": "start", "input": str}
                - {"type": "thought", "content": str}
                - {"type": "tool_call", "name": str, "arguments": dict}
                - {"type": "tool_result", "name": str, "result": str}
                - {"type": "final", "content": str, "usage": dict}
                - {"type": "error", "content": str}
        """
        self.state = AgentState.THINKING
        self.memory.add_user(user_input)
        self.steps = []

        yield {"type": "start", "input": user_input}

        for iteration in range(self.config.agent.max_iterations):
            step = AgentStep(step_num=iteration + 1, state=AgentState.THINKING)

            # 1. Get LLM response
            response = self._get_llm_response()

            # 2. Yield thought content
            content = response.get("content", "")
            if content:
                step.thought = content
                yield {"type": "thought", "content": content}

            # 3. Check if done
            if response.get("finish_reason") == "stop":
                step.state = AgentState.DONE
                self.steps.append(step)
                self.state = AgentState.DONE
                yield {"type": "final", "content": content, "usage": response.get("usage", {})}
                return

            # 4. Process tool calls
            tool_calls = response.get("tool_calls", [])
            if not tool_calls:
                step.state = AgentState.DONE
                self.steps.append(step)
                self.state = AgentState.DONE
                yield {"type": "final", "content": content, "usage": response.get("usage", {})}
                return

            step.state = AgentState.ACTING
            for tc in tool_calls:
                step.action = tc["name"]
                step.action_input = tc["arguments"]

                yield {
                    "type": "tool_call",
                    "name": tc["name"],
                    "arguments": tc["arguments"],
                }

                # Execute tool
                result = self.tools.execute(tc["name"], **tc["arguments"])
                step.observation = result[:500] + "..." if len(result) > 500 else result

                # Add tool result to memory
                self.memory.add_tool_result(tc["id"], tc["name"], result)

                yield {
                    "type": "tool_result",
                    "name": tc["name"],
                    "result": result,
                }

            self.steps.append(step)

        # Max iterations reached
        self.state = AgentState.ERROR
        yield {
            "type": "error",
            "content": "Max iterations reached without completion",
        }

    def chat(self, user_input: str, stream: bool = True):
        """聊天模式：运行并打印所有过程到控制台。

        与 run() 的区别：
        - 默认使用流式输出
        - 实时打印思考过程、工具调用、工具结果
        - 自动记录到日志
        """
        for event in self.run_stream(user_input):
            etype = event["type"]

            if etype == "start":
                output.info(f"用户输入: {user_input}")
                output.print(f"\n[bold blue]▶ 用户请求:[/bold blue] {user_input}\n")

            elif etype == "thought":
                thought = event["content"]
                if thought:
                    output.info(f"Agent思考: {thought[:200]}...")
                    output.print(f"[dim italic]🤔 {thought[:300]}[/dim italic]", markup=False)

            elif etype == "tool_call":
                name = event["name"]
                args = event["arguments"]
                output.info(f"调用工具: {name}({json.dumps(args, ensure_ascii=False)})")
                output.print(
                    f"  [yellow]🔧 {name}[/yellow]"
                    f"({json.dumps(args, ensure_ascii=False)})"
                )

            elif etype == "tool_result":
                name = event["name"]
                result = event["result"]
                preview = result[:300] + "..." if len(result) > 300 else result
                output.info(f"工具结果: {name} -> {preview}")
                output.print(f"  [dim]→ {preview}[/dim]", markup=False)

            elif etype == "final":
                content = event["content"]
                usage = event.get("usage", {})
                output.info(f"任务完成, tokens: {usage.get('total_tokens', 'N/A')}")
                output.print("")
                output.success("✓ 任务完成")
                output.print("")
                if content:
                    self._print_content(content)
                return {
                    "success": True,
                    "output": content,
                    "steps": len(self.steps),
                    "usage": usage,
                }

            elif etype == "error":
                error_msg = event["content"]
                output.error(f"Agent错误: {error_msg}")
                output.error(f"✗ {error_msg}")
                return {
                    "success": False,
                    "output": error_msg,
                    "steps": len(self.steps),
                    "usage": {},
                }

        return {"success": False, "output": "Unknown error", "steps": 0, "usage": {}}

    def _display_final_output(self, content: str) -> None:
        """Display the final output to the user."""
        output.print("")
        output.success("✓ 任务完成")
        output.print("")
        self._print_content(content)

    def _print_content(self, content: str) -> None:
        """智能打印内容：代码块用语法高亮，纯文本用 markup=False 避免冲突。"""
        if not content:
            return

        # 检测是否包含代码块（```...```）
        code_blocks = re.findall(r"```(\w*)\n(.*?)```", content, re.DOTALL)
        if code_blocks:
            # 先打印代码块外的文本
            text_parts = re.split(r"```\w*\n.*?```", content, flags=re.DOTALL)
            for i, part in enumerate(text_parts):
                part = part.strip()
                if part:
                    output.text(part)
                if i < len(code_blocks):
                    lang = code_blocks[i][0] or "python"
                    code = code_blocks[i][1]
                    output.code(code, language=lang, title=f"代码 ({lang})")
        else:
            # 无代码块，按纯文本打印
            output.text(content)

    def add_context(self, content: str) -> None:
        """Add additional context as a system message."""
        self.memory.add_system(content)

    def reset(self) -> None:
        """Reset the agent state."""
        self.memory.clear()
        self.memory.add_system(self.PYTHON_EXPERT_SYSTEM)
        self.steps.clear()
        self.state = AgentState.IDLE

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the agent's execution."""
        return {
            "state": self.state.value,
            "steps": len(self.steps),
            "messages": self.memory.message_count,
            "tool_calls": sum(
                1 for s in self.steps if s.state == AgentState.ACTING
            ),
        }