import os
import random
from typing import ClassVar
from maibot_sdk import MaiBotPlugin, Command, PluginConfigBase, Field


# 1. 定义内层 [plugin] 配置节
class PluginConfig(PluginConfigBase):
    enabled: bool = Field(default=True, description="是否启用插件")
    config_version: str = Field(default="1.1.0", description="配置文件版本")


# 2. 定义外层配置模型
class SanguoshaConfig(PluginConfigBase):
    plugin: PluginConfig = Field(default_factory=PluginConfig, description="插件配置")


class SanguoshaPlugin(MaiBotPlugin):
    # 3. 绑定配置模型
    config_model: ClassVar[type[PluginConfigBase]] = SanguoshaConfig

    def __init__(self):
        super().__init__()
        self.general_quotes = {}
        self.general_names = []
        self.all_quotes = []
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

    async def on_load(self) -> None:
        self.ctx.logger.info("三国杀台词插件已加载，正在读取台词库...")
        txt_path = os.path.join(self.plugin_dir, "sanguosha_quotes.txt")

        if not os.path.exists(txt_path):
            self.ctx.logger.error(f"台词库文件不存在: {txt_path}")
            return

        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or '：' not in line:
                        continue
                    general, quote = line.split('：', 1)
                    general = general.strip()
                    quote = quote.strip()

                    if general not in self.general_quotes:
                        self.general_quotes[general] = []
                    self.general_quotes[general].append(quote)
        except UnicodeDecodeError as e:
            self.ctx.logger.error(f"台词库编码错误（需 UTF-8）: {e}")
            return
        except Exception as e:
            self.ctx.logger.error(f"读取台词文件失败: {e}")
            return

        if not self.general_quotes:
            self.ctx.logger.warning("台词库为空，请检查 sanguosha_quotes.txt 格式")
            return

        # 按名字长度降序排列，配合后续的 startswith 实现最长匹配
        self.general_names = sorted(self.general_quotes.keys(), key=len, reverse=True)
        self.all_quotes = [q for quotes in self.general_quotes.values() for q in quotes]

        self.ctx.logger.info(
            f"成功加载了 {len(self.general_names)} 名武将、{len(self.all_quotes)} 条台词！"
        )

    async def on_unload(self) -> None:
        pass

    async def on_config_update(self, scope: str, config_data: dict, version: str) -> None:
        pass

    # 1. 随机指令：/三国杀
    @Command("sanguosha", pattern=r"^/三国杀$", description="随机抽取一句三国杀武将台词")
    async def handle_sanguosha(self, **kwargs):
        if not self.config.plugin.enabled:
            return False, "插件已禁用", 0

        if not self.all_quotes:
            line = "台词库为空或读取失败！"
        else:
            line = random.choice(self.all_quotes)

        await self.ctx.send.text(line, kwargs["stream_id"])
        return True, line, 2

    # 2. 指定武将指令：/张飞
    # 正则限制在 1-15 个字符，防止系统级死循环。通过代码内逻辑精准过滤！
    @Command("sanguosha_specific", pattern=r"^/(?P<general>[^\s/]{1,15})$", description="抽取指定武将的专属台词（如：/张飞）")
    async def handle_specific_general(self, **kwargs):
        if not self.config.plugin.enabled:
            return False, "插件已禁用", 0

        target_name = ""
        
        # 从宿主传入的 matched_groups 安全获取参数
        matched_groups = kwargs.get("matched_groups", {})
        if isinstance(matched_groups, dict):
            target_name = matched_groups.get("general", "").strip()

        if not target_name:
            return False, "未获取到武将名", 0

        # 如果用户发的刚好是 "/三国杀"，交由第一个指令处理，本指令放行
        if target_name == "三国杀":
            return False, "忽略三国杀指令", 0

        # 【核心修复】通过代码逻辑判断是否为词库中的武将
        # 先查一遍，如果完全不是词库里的前缀，直接光速放行，绝不干涉其他插件的指令！
        is_potential_general = any(target_name.startswith(name) for name in self.general_names)
        if not is_potential_general:
            return False, "非武将指令，放行", 0

        # 按长度降序匹配，排序在这里真正生效了！
        for name in self.general_names:
            if target_name.startswith(name):
                quote = random.choice(self.general_quotes[name])
                await self.ctx.send.text(quote, kwargs["stream_id"])
                return True, quote, 2

        # 如果没有匹配到武将，返回 False 且拦截等级为 0
        return False, "未找到该武将，放行", 0


def create_plugin():
    return SanguoshaPlugin()