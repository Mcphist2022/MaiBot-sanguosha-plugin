import os
import random
from maibot_sdk import MaiBotPlugin, Command, PluginConfigBase, Field

# 1. 定义一个空的配置模型（这是关键！）
class SanguoshaConfig(PluginConfigBase):
    """三国杀插件配置"""
    __ui_label__ = "插件设置"
    # 这里可以留空，或者放一个不需要用户修改的占位字段
    enabled: bool = Field(default=True, description="是否启用插件")

class SanguoshaPlugin(MaiBotPlugin):
    # 2. 告诉系统，我的配置模型是上面定义的那个
    config_model = SanguoshaConfig

    def __init__(self):
        super().__init__()
        self.lines = []
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

    async def on_load(self) -> None:
        self.ctx.logger.info("三国杀台词插件已加载，正在读取台词库...")
        txt_path = os.path.join(self.plugin_dir, "sanguosha_quotes_pure.txt")
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                self.lines = [line.strip() for line in f if line.strip()]
            self.ctx.logger.info(f"成功加载了 {len(self.lines)} 条三国杀台词！")
        except Exception as e:
            self.ctx.logger.error(f"读取台词文件失败: {e}")

    async def on_unload(self) -> None:
        pass

    async def on_config_update(self, scope: str, config_data: dict, version: str) -> None:
        pass

    @Command("sanguosha", pattern=r"^/三国杀")
    async def handle_sanguosha(self, **kwargs):
        if not self.lines:
            line = "台词库为空，请检查 sanguosha_quotes_pure.txt 文件！"
        else:
            line = random.choice(self.lines)
        await self.ctx.send.text(line, kwargs["stream_id"])
        return True, line, 2

def create_plugin():
    return SanguoshaPlugin()