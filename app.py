from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.extractors import extract_document
from analyzer.findings import analyze
from analyzer.matching import best_match
from analyzer.report import to_markdown

st.set_page_config(page_title="Оргструктура: до и после", page_icon="🏢", layout="wide")
st.title("Анализ организационной структуры и функций")
st.caption("Предварительный анализ документов с привязкой каждого наблюдения к исходному фрагменту.")

left, right = st.columns(2)
with left:
    before_files = st.file_uploader("Документы «До»", type=["docx", "pdf", "xlsx", "xlsm"], accept_multiple_files=True, key="before")
with right:
    after_files = st.file_uploader("Документы «После»", type=["docx", "pdf", "xlsx", "xlsm"], accept_multiple_files=True, key="after")

st.info(
    "Загрузите документы в обе группы: исходную версию в «До», "
    "а обновлённую версию в «После». Поддерживаются DOCX, PDF, XLSX и XLSM."
)

if st.button("Запустить анализ", type="primary", disabled=not (before_files and after_files)):
    try:
        before_docs = [extract_document(f.name, f.getvalue()) for f in before_files]
        after_docs = [extract_document(f.name, f.getvalue()) for f in after_files]
        result = analyze(before_docs, after_docs)
        st.session_state["analysis_result"] = result
    except Exception as exc:
        st.error(f"Не удалось выполнить анализ: {exc}")

result = st.session_state.get("analysis_result")
if result:
    st.info(result.conclusion)
    findings = result.findings
    categories = ["Изменения", "Сопоставление функций", "Потенциальные потери", "Дублирование", "Пересечения", "Конфликты интересов", "Подразделения", "Заключение"]
    tabs = st.tabs(categories)
    with tabs[0]:
        st.subheader("Найденные изменения")
        for f in findings:
            with st.expander(f"{f.category}: {f.title}"):
                st.write(f.details)
                st.caption(f"Уровень: {f.confidence}. Наблюдение рекомендательное, требует проверки.")
                for source in f.sources:
                    st.markdown(f"**{source.label}**\n\n> {source.excerpt}")
    with tabs[1]:
        rows = []
        for old in result.functions_before:
            idx, score = best_match(old.text, [x.text for x in result.functions_after])
            match = result.functions_after[idx] if idx is not None else None
            rows.append({"Подразделение до": old.unit, "Функция до": old.text, "Источник до": old.source.label,
                         "Подразделение после": match.unit if match else "Не найдено", "Функция после": match.text if match else "—",
                         "Источник после": match.source.label if match else "—", "Сходство": f"{score:.0%}" if match else "—"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    with tabs[2]:
        for f in findings:
            if f.category == "Потенциальная потеря функции":
                st.warning(f.title + "\n\n" + f.details)
                st.markdown(f"Источник: **{f.sources[0].label}**\n\n> {f.sources[0].excerpt}")
    with tabs[3]:
        for f in findings:
            if f.category == "Возможное дублирование":
                st.warning(f.title + "\n\n" + f.details)
                for source in f.sources:
                    st.markdown(f"**{source.label}**\n\n> {source.excerpt}")
    with tabs[4]:
        for f in findings:
            if f.category == "Возможное пересечение ответственности":
                st.warning(f.title + "\n\n" + f.details)
                for source in f.sources:
                    st.markdown(f"**{source.label}**\n\n> {source.excerpt}")
    with tabs[5]:
        for f in findings:
            if f.category == "Возможный конфликт интересов":
                st.warning(f.title + "\n\n" + f.details)
                for source in f.sources:
                    st.markdown(f"**{source.label}**\n\n> {source.excerpt}")
    with tabs[6]:
        st.write("**До:**", ", ".join(result.units_before) or "Не удалось надёжно извлечь названия подразделений")
        st.write("**После:**", ", ".join(result.units_after) or "Не удалось надёжно извлечь названия подразделений")
        for f in findings:
            if f.category == "Подразделение":
                st.markdown(f"**{f.title}:** {f.details}")
                for source in f.sources:
                    st.caption(source.label + " — " + source.excerpt)
    with tabs[7]:
        st.markdown(to_markdown(result))
        st.download_button("Скачать заключение (Markdown)", to_markdown(result), file_name="analytical_conclusion.md", mime="text/markdown")

st.caption(
    "Результаты автоматического анализа носят рекомендательный характер "
    "и требуют экспертной проверки."
)


st.divider()
st.caption("Поддерживаются .docx, .pdf, .xlsx и .xlsm. Старые форматы .doc/.xls сначала сохраните в современном формате. Прототип использует локальные правила сопоставления без отправки документов во внешние AI-сервисы.")
