"""统一输出模块：同时打印到控制台（Rich）和写入日志文件。

用法：
    from codebot.utils.output import output

    output.info("普通信息")
    output.success("成功信息")
    output.error("错误信息")
    output.warning("警告信息")
    output.debug("调试信息")
    output.print("[bold]带样式的Rich输出[/bold]")
    output.print("纯文本", style="green")
"""

import logging
import re
from typing import Optional

from rich.console import Console

from codebot.utils.logger import get_logger, get_console

__all__ = ["output"]


def _strip_rich_markup(text: str) -> str:
    """移除 Rich 标记，用于写入纯文本日志。"""
    return re.sub(r"\[/?[^\]]+\]", "", text)


class UnifiedOutput:
    """统一输出：一份代码同时完成控制台打印和日志写入。

    所有消息自动：
    - 打印到控制台（Rich格式化）
    - 写入日志文件（带级别和行号，纯文本）

    注意：不使用 logger 的控制台 handler，避免重复输出。
    """

    def __init__(self):
        self._logger: Optional[logging.Logger] = None
        self._console: Optional[Console] = None

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = get_logger()
        return self._logger

    @property
    def console(self) -> Console:
        if self._console is None:
            self._console = get_console()
        return self._console

    def _write_log(self, level: int, msg: str) -> None:
        """将消息写入日志文件（不经过控制台 handler）。"""
        clean_msg = _strip_rich_markup(msg)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                record = self.logger.makeRecord(
                    self.logger.name, level, "", 0, clean_msg, (), None
                )
                handler.emit(record)
                return
        self.logger.log(level, clean_msg)

    # ─── 带级别的输出 ───────────────────────────────────────

    def info(self, msg: str) -> None:
        """普通信息：蓝色控制台 + INFO日志。"""
        self.console.print(f"[blue]{msg}[/blue]")
        self._write_log(logging.INFO, msg)

    def success(self, msg: str) -> None:
        """成功信息：绿色控制台 + INFO日志。"""
        self.console.print(f"[green]{msg}[/green]")
        self._write_log(logging.INFO, msg)

    def error(self, msg: str) -> None:
        """错误信息：红色控制台 + ERROR日志。"""
        self.console.print(f"[red]{msg}[/red]")
        self._write_log(logging.ERROR, msg)

    def warning(self, msg: str) -> None:
        """警告信息：黄色控制台 + WARNING日志。"""
        self.console.print(f"[yellow]{msg}[/yellow]")
        self._write_log(logging.WARNING, msg)

    def debug(self, msg: str) -> None:
        """调试信息：灰色控制台 + DEBUG日志。"""
        self.console.print(f"[dim]{msg}[/dim]")
        self._write_log(logging.DEBUG, msg)

    # ─── 通用打印 ────────────────────────────────────────────

    def print(self, msg: str, style: Optional[str] = None, markup: bool = True) -> None:
        """通用打印：支持Rich样式标记，同时写入INFO日志。

        Args:
            msg: 消息内容，可包含Rich标记如 [bold red]...[/bold red]
            style: 可选的颜色样式，如 "green"、"red"、"yellow" 等
            markup: 是否解析Rich标记，默认True。设为False可安全打印含[ ]的内容
        """
        if style:
            self.console.print(f"[{style}]{msg}[/{style}]")
        else:
            self.console.print(msg, markup=markup)
        self._write_log(logging.INFO, msg)

    def code(self, msg: str, language: str = "python", title: str = "") -> None:
        """打印代码块：语法高亮 + 行号 + 正确换行。

        解决普通 print 打印代码时 \\n 不换行、Rich 标记冲突等问题。

        Args:
            msg: 代码内容（含真实 \\n 换行符）
            language: 语言类型，用于语法高亮，如 "python"、"json"、"bash" 等
            title: 可选的标题
        """
        from rich.panel import Panel
        from rich.syntax import Syntax

        syntax = Syntax(msg, language, theme="monokai", line_numbers=True)
        if title:
            self.console.print(Panel(syntax, title=title))
        else:
            self.console.print(syntax)
        self._write_log(logging.INFO, msg)

    def text(self, msg: str) -> None:
        """打印纯文本：不解析Rich标记，适合打印含 [ ] 的普通内容。

        等同于 print(msg, markup=False) 的快捷方式。
        """
        self.console.print(msg, markup=False)
        self._write_log(logging.INFO, msg)

    def rule(self, title: str = "") -> None:
        """打印分隔线。"""
        self.console.rule(title)
        if title:
            self._write_log(logging.INFO, f"─── {title} ───")

    def panel(self, msg: str, title: str = "") -> None:
        """打印面板。"""
        from rich.panel import Panel
        self.console.print(Panel(msg, title=title))
        self._write_log(logging.INFO, f"[{title}] {msg}")

    # ─── 导出原始的 console 和 logger 供高级用法 ─────────────

    def raw_console(self) -> Console:
        return self.console

    def raw_logger(self) -> logging.Logger:
        return self.logger


# 全局单例
output = UnifiedOutput()
