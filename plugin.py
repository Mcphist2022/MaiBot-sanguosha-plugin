import os
import random
from maibot_sdk import MaiBotPlugin, Command, EventHandler, PluginConfigBase, Field
from maibot_sdk.types import EventType

# 1. 声明配置模型
class SanguoshaConfig(PluginConfigBase):
    enabled: bool = Field(default=True, description="是否启用插件")

class SanguoshaPlugin(MaiBotPlugin):
    # 2. 绑定配置模型
    config_model = SanguoshaConfig

    def __init__(self):
        super().__init__()
        self.general_quotes = {}
        self.general_names = []
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))

    async def on_load(self) -> None:
        self.ctx.logger.info("三国杀台词插件已加载，正在读取台词库...")
        txt_path = os.path.join(self.plugin_dir, "sanguosha_quotes.txt")
        
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
            
            self.general_names = sorted(self.general_quotes.keys(), key=len, reverse=True)
            self.ctx.logger.info(f"成功加载了 {len(self.general_names)} 名武将的台词！")
        except Exception as e:
            self.ctx.logger.error(f"读取台词文件失败: {e}")

    async def on_unload(self) -> None:
        pass

    async def on_config_update(self, scope: str, config_data: dict, version: str) -> None:
        pass

    @Command("sanguosha", pattern=r"^/三国杀$")
    async def handle_sanguosha(self, **kwargs):
        all_quotes = [q for quotes in self.general_quotes.values() for q in quotes]
        if not all_quotes:
            line = "台词库为空或读取失败！"
        else:
            line = random.choice(all_quotes)
        await self.ctx.send.text(line, kwargs["stream_id"])
        return True, line, 2

    @EventHandler(
        "sanguosha_passive",
        description="检测群聊中的武将名并回复台词",
        event_type=EventType.ON_MESSAGE_PRE_PROCESS,
        intercept_message=True,
        weight=100,
    )
    async def handle_passive_trigger(self, message, **kwargs):
        raw_message = message.get("raw_message", "").strip()
        
        if raw_message.startswith("/"):
            return {"intercepted": False}
            
        detected_general = None
        for name in self.general_names:
            if len(name) < 2:
                continue
            if name in raw_message:
                detected_general = name
                break
        
        if detected_general:
            quote = random.choice(self.general_quotes[detected_general])
            stream_id = message.get("stream_id") or kwargs.get("stream_id")
            if stream_id:
                await self.ctx.send.text(quote, stream_id)
            return {"intercepted": True}
            
        return {"intercepted": False}

def create_plugin():
    return SanguoshaPlugin()