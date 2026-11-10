import os
import random
import csv
from utils.logger_handler import logger
from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path

rag = RagSummarizeService()

user_ids = ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"]
month_arr = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
             "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]

external_data = {}

@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)


@tool(description="获取指定城市的天气, 以消息字符串的形式返回")
def get_weather(city: str) -> str:
    return f"城市{city}天气为晴天, 气温26摄氏度, 空气湿度50%, 南风1级, AQI21, 最近6小时降雨概率极低"


@tool(description="获取指定城市的天气, 以消息字符串的形式返回")
def get_user_location() -> str:
    return random.choice(["深圳", "合肥", "杭州"])


@tool(description="获取用户的ID, 以纯字符串形式返回")
def get_user_id() -> str:
    return random.choice(user_ids)


@tool(description="获取当前月份, 以纯字符串形式返回")
def get_current_month() -> str:
    return random.choice(month_arr)


def generate_external_data():
    """
    {
    "user_id": {
        "month" : {"特征": xxx, "效率": xxx, ...}
        "month" : {"特征": xxx, "效率": xxx, ...}
        "month" : {"特征": xxx, "效率": xxx, ...}
        ...
    },
    "user_id": {
        "month" : {"特征": xxx, "效率": xxx, ...}
        "month" : {"特征": xxx, "效率": xxx, ...}
        "month" : {"特征": xxx, "效率": xxx, ...}
        ...
    },
    "user_id": {
        "month" : {"特征": xxx, "效率": xxx, ...}
        "month" : {"特征": xxx, "效率": xxx, ...}
        "month" : {"特征": xxx, "效率": xxx, ...}
        ...
    },
    ...
    }
    :return:
    """
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")

        with open(external_data_path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                user_id = row.get("user_id", row.get("用户ID", "")).strip()
                time = row.get("time", row.get("月份", "")).strip()
                if not user_id or not time:
                    continue

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "特征": row.get("feature", row.get("特征", "")),
                    "效率": row.get("efficiency", row.get("清洁效率", row.get("效率", ""))),
                    "消耗": row.get("consumable", row.get("耗材", row.get("消耗", ""))),
                    "对比": row.get("comparison", row.get("对比", ""))
                }


@tool(description="从外部系统中, 获取用户的使用记录, 以纯字符串形式返回, 如果未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        # 该工具声明返回 str, 这里返回 dict 会与输出约定不一致, 需转为字符串
        return str(external_data[user_id][month])
    except KeyError:
        logger.warning(f"[fetch_external_data]未能检索到用户: {user_id}在{month}的使用记录数据")
        return ""


@tool(description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词拼接提供上下文")
def fill_context_for_report():
    return "fill_context_for_report已调用"



if __name__ == '__main__':
    print(fetch_external_data("1011", "2025-01"))
