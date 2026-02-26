"""
AI 摘要服务
使用 litellm 支持多种 LLM 提供商（OpenAI、Claude、DeepSeek、Ollama 等）
"""
import json
from typing import List, Dict, Any, Optional

from app.services.database import db
from app.utils.logger import logger


DEFAULT_AI_CONFIG = {
    "enabled": False,
    "model": "gpt-4o-mini",
    "api_key": "",
    "base_url": "",
    "summary_style": "brief",
}

SUMMARY_PROMPTS = {
    "brief": """你是一位专业的新闻编辑。请根据以下来自多个平台的热门话题，生成一份简洁的热点速递摘要。

要求：
1. 按话题主题分组（如：社会热点、科技、娱乐等），而非按平台分组
2. 识别在多个平台同时出现的热门话题，重点关注
3. 每个话题用1-2句话概括核心内容
4. 使用自然、流畅的中文
5. 控制在500字以内
6. 适当使用 emoji 标注分类

热点数据：
{items_text}

请直接输出摘要内容，不需要额外的开头语或结束语。""",

    "detailed": """你是一位资深新闻编辑。请根据以下来自多个平台的热门话题，生成一份详细的热点分析报告。

要求：
1. 按话题主题分组（如：时事、科技、财经、娱乐、体育等）
2. 识别跨平台热门话题，分析其传播趋势
3. 每个重要话题提供2-3句话的背景分析
4. 对今日整体热点趋势做简要点评
5. 使用专业但易读的中文
6. 控制在800字以内

热点数据：
{items_text}

请直接输出分析内容，不需要额外的开头语或结束语。""",

    "morning_briefing": """你是一位新闻早报编辑。请根据以下热门话题，生成一份精炼的早间资讯简报。

要求：
1. 开头用一句话概括今日热点整体趋势
2. 分3-5个主题版块整理（如 🔥 焦点、💡 科技、🎬 文娱、💰 财经等）
3. 每个版块2-4条核心信息，每条一句话
4. 语气简洁有力，像专业的晨间简报
5. 控制在400字以内

热点数据：
{items_text}

请直接输出简报内容。""",
}


class AIService:
    """AI 摘要服务"""

    def get_config(self) -> Dict[str, Any]:
        config_str = db.get_setting("ai_config")
        if config_str:
            try:
                return json.loads(config_str)
            except json.JSONDecodeError:
                pass
        return DEFAULT_AI_CONFIG.copy()

    def set_config(self, config: Dict[str, Any]):
        full_config = DEFAULT_AI_CONFIG.copy()
        full_config.update(config)
        db.set_setting("ai_config", json.dumps(full_config))
        logger.info(f"AI 配置已更新: model={full_config.get('model')}, enabled={full_config.get('enabled')}")

    def _build_items_text(self, hot_lists) -> str:
        """将热榜数据格式化为文本，供 LLM 处理"""
        lines = []
        for hot_list in hot_lists:
            lines.append(f"\n【{hot_list.source_name}】")
            for i, item in enumerate(hot_list.items[:15], 1):
                score_str = f" (热度: {item.hot_score})" if item.hot_score else ""
                lines.append(f"  {i}. {item.title}{score_str}")
        return "\n".join(lines)

    async def generate_summary(self, hot_lists, style: str = "brief") -> Optional[str]:
        """生成 AI 摘要

        Args:
            hot_lists: HotList 对象列表
            style: 摘要风格 (brief / detailed / morning_briefing)

        Returns:
            AI 生成的摘要文本，失败返回 None
        """
        config = self.get_config()

        if not config.get("enabled"):
            return None

        model = config.get("model", "gpt-4o-mini")
        api_key = config.get("api_key", "")
        base_url = config.get("base_url", "").rstrip("/")

        if not api_key:
            logger.warning("AI API Key 未配置，跳过 AI 摘要")
            return None

        items_text = self._build_items_text(hot_lists)
        if not items_text.strip():
            return None

        prompt_template = SUMMARY_PROMPTS.get(style, SUMMARY_PROMPTS["brief"])
        prompt = prompt_template.format(items_text=items_text)

        try:
            import litellm
            litellm.suppress_debug_info = True

            if base_url:
                if not model.startswith("openai/"):
                    model = f"openai/{model}"
                if not base_url.endswith("/v1"):
                    base_url = f"{base_url}/v1"

            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "api_key": api_key,
                "temperature": 0.7,
                "max_tokens": 2000,
            }
            if base_url:
                kwargs["api_base"] = base_url

            logger.info(f"正在调用 AI 生成摘要... model={model}, style={style}")
            response = await litellm.acompletion(**kwargs)

            summary = response.choices[0].message.content.strip()
            logger.info(f"AI 摘要生成成功，长度: {len(summary)} 字符")
            return summary

        except ImportError:
            logger.error("litellm 未安装，请运行: pip install litellm")
            return None
        except Exception as e:
            logger.error(f"AI 摘要生成失败: {e}")
            return None


ai_service = AIService()
