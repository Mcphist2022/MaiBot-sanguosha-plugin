import os
import random
from maibot_sdk import MaiBotPlugin, Command

class SanguoshaPlugin(MaiBotPlugin):
    def __init__(self):
        super().__init__()
        self.lines = []
        # 获取当前插件所在目录
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

    async def on_load(self) -> None:
        self.ctx.logger.info("三国杀台词插件已加载，正在读取台词库...")
        txt_path = os.path.join(self.plugin_dir, "sanguosha_quotes_pure.txt")
        
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                # 读取所有行，去掉空白行，并存入列表
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
            line = "台词库为空或读取失败，请检查 sanguosha_quotes_pure.txt 文件！"
        else:
            line = random.choice(self.lines)
            
        await self.ctx.send.text(line, kwargs["stream_id"])
        return True, line, 2

def create_plugin():
    return SanguoshaPlugin()