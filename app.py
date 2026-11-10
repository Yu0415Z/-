import json
import time
from datetime import datetime

import streamlit as st

from agent.react_agent import ReactAgent
from rag.rag_service import RagSummarizeService
from rag.vector_store import VectorStoreService


st.set_page_config(page_title="扫地机器人智能客服", page_icon="🤖", layout="wide")
st.title("🤖 扫地机器人智能客服")
st.caption("基于 RAG 知识检索与 ReAct 工具调用的智能问答和使用报告助手")

if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "rag_service" not in st.session_state:
    st.session_state.rag_service = RagSummarizeService()

with st.sidebar:
    st.header("项目控制台")
    st.subheader("知识库")
    try:
        stats = VectorStoreService().collection_stats()
        st.metric("已索引文本片段", stats["documents"])
    except Exception as exc:
        st.warning(f"暂时无法读取向量库状态：{exc}")
    if st.button("扫描并增量导入 data/", use_container_width=True):
        with st.spinner("正在读取、切分并索引知识文件…"):
            VectorStoreService().load_document()
        st.success("知识库扫描完成。重复文件会按 MD5 跳过。")
        st.rerun()
    st.caption("支持 data/ 下的 TXT、PDF；新增文件后点击上方按钮导入。")
    st.divider()
    st.subheader("会话管理")
    if st.button("清空当前会话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    history = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
    st.download_button("导出聊天记录 JSON", history,
                       file_name=f"chat_{datetime.now():%Y%m%d_%H%M%S}.json",
                       mime="application/json", use_container_width=True)
    st.caption(f"当前会话 {len(st.session_state.messages)} 条消息")

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            with st.expander("查看检索到的参考资料"):
                for source in message["sources"]:
                    page = f" · 第 {source['page'] + 1} 页" if isinstance(source.get("page"), int) else ""
                    st.markdown(f"**{source['source']}**{page} · 距离 {source['distance']:.3f}")
                    st.caption(source["content"][:1200])
        if message["role"] == "assistant":
            left, right, _ = st.columns([1, 1, 8])
            if left.button("👍", key=f"up_{index}"):
                st.session_state.feedback.append({"message": message["content"], "rating": 1,
                                                  "time": datetime.now().isoformat(timespec="seconds")})
                st.toast("感谢反馈")
            if right.button("👎", key=f"down_{index}"):
                st.session_state.feedback.append({"message": message["content"], "rating": -1,
                                                  "time": datetime.now().isoformat(timespec="seconds")})
                st.toast("已记录反馈，感谢帮助改进")

prompt = st.chat_input("例如：扫地机器人拖布有异味怎么办？")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("正在检索资料并组织回答…"):
            response_parts = []
            try:
                for chunk in st.session_state.agent.execute_stream(prompt):
                    response_parts.append(chunk)
                answer = "".join(response_parts).strip() or "暂时没有生成回答，请稍后重试。"
            except Exception as exc:
                answer = f"本次请求处理失败：{exc}"
                st.exception(exc)
        st.markdown(answer)
        sources = []
        try:
            sources = st.session_state.rag_service.retrieve_sources(prompt)
            if sources:
                with st.expander("查看相关知识库资料"):
                    for source in sources:
                        page = f" · 第 {source['page'] + 1} 页" if isinstance(source.get("page"), int) else ""
                        st.markdown(f"**{source['source']}**{page} · 距离 {source['distance']:.3f}")
                        st.caption(source["content"][:1200])
        except Exception:
            pass
    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
    st.rerun()
