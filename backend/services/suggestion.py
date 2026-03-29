def make_suggestion(result: str, kind: str = "") -> str:
    title = f"识别结果：{result}"
    kind_text = f"（分类：{kind}）" if kind else ""
    return (
        f"🌱 {title}{kind_text}<br><br>"
        "📌 可能原因：当前症状通常与环境湿度、通风不足或病原菌传播有关。<br><br>"
        "🧑‍🌾 种植建议：优先清理病叶、控制浇水频率、提升通风和光照，减少再次感染风险。<br><br>"
        "🛠️ 治理方式：先做小范围对照处理，再按7天一个周期复查；若扩散明显，及时更换药剂策略并隔离病株。"
    )
