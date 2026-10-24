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

        # 按名字长度降序排列（确保正确匹配诸如 "群赵云" 而不是 "赵云"）
        self.general_names = sorted(self.general_quotes.keys(), key=len, reverse=True)
        # 预计算所有台词，提升 /三国杀 全局抽取时的响应速度
        self.all_quotes = [q for quotes in self.general_quotes.values() for q in quotes]

        self.ctx.logger.info(
            f"成功加载了 {len(self.general_names)} 名武将、{len(self.all_quotes)} 条台词！"
        )

    async def on_unload(self) -> None:
        pass

    async def on_config_update(self, scope: str, config_data: dict, version: str) -> None:
        pass

    # 1. 随机指令：/三国杀
    @Command("sanguosha", pattern=r"^/三国杀$")
    async def handle_sanguosha(self, **kwargs):
        # 检查 WebUI 中的开关状态
        if not self.config.plugin.enabled:
            return False, "插件已禁用", 0

        if not self.all_quotes:
            line = "台词库为空或读取失败！"
        else:
            line = random.choice(self.all_quotes)

        await self.ctx.send.text(line, kwargs["stream_id"])
        return True, line, 2

    # 2. 指定武将指令：/张飞
    # 使用命名捕获组，限制放宽到 1-15 个非空格、非斜杠字符，覆盖长名字武将
    @Command("sanguosha_specific", pattern=r"^/(?P<general>[^\s/]{1,15})$")
    async def handle_specific_general(self, **kwargs):
        # 检查 WebUI 中的开关状态（返回 0 代表放行）
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

        # 按长度降序匹配武将名
        for name in self.general_names:
            if name == target_name:
                quote = random.choice(self.general_quotes[name])
                await self.ctx.send.text(quote, kwargs["stream_id"])
                return True, quote, 2

        # 如果没有匹配到武将，返回 False 且拦截等级为 0（放行给正常聊天）
        return False, "未找到该武将，放行", 0


def create_plugin():
    return SanguoshaPlugin()