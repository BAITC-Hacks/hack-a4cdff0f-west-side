"""Rule based, source-backed analysis. Findings are prompts for expert review."""
from __future__ import annotations

import re

from .matching import best_match, normalize, similarity
from .models import AnalysisResult, ExtractedDocument, Finding, FunctionRecord

UNIT_RE = re.compile(r"(?:управлени[ея]|департамент[а-я]*|отдел[а-я]*|служб[а-я]*|центр[а-я]*|дирекци[яи])\s+(?:по\s+)?[А-ЯЁA-Z0-9][\wЁёА-Яа-я -]{1,55}?(?=\s+(?:обеспеч|организ|осуществ|координир|контрол|разработ|ведени|проведени|формирован|управлен|анализ|подготов|сопровожд|мониторинг|отвечает|выполняет)|[,;:.()|]|$)", re.I)
FUNCTION_MARKERS = ("обеспеч", "организует", "организовывает", "осуществ", "координир", "контрол", "разработ", "ведени", "проведени", "формирован", "управлен", "анализ", "подготов", "сопровожд", "мониторинг", "отвечает за", "функци")


def _records(docs: list[ExtractedDocument]) -> tuple[list[str], list[FunctionRecord]]:
    units: list[str] = []
    records: list[FunctionRecord] = []
    for doc in docs:
        current_unit = "Подразделение не определено в фрагменте"
        for segment in doc.segments:
            text = segment.text.strip()
            unit_match = UNIT_RE.search(text)
            if unit_match:
                current_unit = " ".join(unit_match.group(0).split()).strip(" .,:;—–-")
                if len(current_unit) > 4 and current_unit.lower() not in {u.lower() for u in units}:
                    units.append(current_unit)
            if len(text) >= 25 and any(marker in text.lower() for marker in FUNCTION_MARKERS):
                records.append(FunctionRecord(current_unit, text, segment.source))
    return units, records


def _finding(category: str, title: str, details: str, *records: FunctionRecord) -> Finding:
    return Finding(category, title, details, [record.source for record in records])


def analyze(before_docs: list[ExtractedDocument], after_docs: list[ExtractedDocument]) -> AnalysisResult:
    if not before_docs or not after_docs:
        raise ValueError("Загрузите документы и в группу «До», и в группу «После».")
    before_units, before = _records(before_docs)
    after_units, after = _records(after_docs)
    findings: list[Finding] = []
    for record in before:
        idx, score = best_match(record.text, [r.text for r in after])
        if idx is None:
            findings.append(_finding("Потенциальная потеря функции", "Функция до реорганизации не найдена после", record.text, record))
        elif score < 0.78:
            findings.append(_finding("Изменение функции", "Формулировка функции могла измениться", f"До: {record.text}\nПосле: {after[idx].text}", record, after[idx]))
    for record in after:
        if best_match(record.text, [r.text for r in before])[0] is None:
            findings.append(_finding("Новая функция", "Функция появилась после реорганизации", record.text, record))
    for i, first in enumerate(after):
        for second in after[i + 1:]:
            if first.unit.lower() != second.unit.lower() and similarity(first.text, second.text) >= 0.72:
                findings.append(_finding("Возможное дублирование", "Похожие функции закреплены за разными подразделениями", f"Сходство формулировок: {similarity(first.text, second.text):.0%}. Требуется экспертная проверка зон ответственности.", first, second))
            common = normalize(first.text) & normalize(second.text)
            if first.unit.lower() != second.unit.lower() and len(common) >= 3 and any(w in common for w in {"контроль", "координация", "обеспечение", "организация", "управление", "мониторинг"}):
                findings.append(_finding("Возможное пересечение ответственности", "Есть общие смысловые элементы в функциях разных подразделений", f"Общие термины: {', '.join(sorted(common)[:8])}. Проверьте границы ответственности.", first, second))
    execution_terms = ("закуп", "провод", "исполня", "разработ", "предостав", "начисл", "распредел")
    oversight_terms = ("контрол", "аудит", "провер", "надзор")
    by_unit: dict[str, list[FunctionRecord]] = {}
    for record in after:
        by_unit.setdefault(record.unit.casefold(), []).append(record)
    for records in by_unit.values():
        for first in records:
            for second in records:
                if first is second:
                    continue
                if any(word in first.text.lower() for word in execution_terms) and any(word in second.text.lower() for word in oversight_terms):
                    findings.append(_finding("Возможный конфликт интересов", "Подразделению могут быть поручены исполнение и контроль", "В документах есть функция исполнения и отдельная функция контроля у одного подразделения. Это индикатор для проверки разделения обязанностей, а не установленный конфликт.", first, second))
                    break
            else:
                continue
            break
    before_set = {u.lower() for u in before_units}
    after_set = {u.lower() for u in after_units}
    for unit in before_units:
        if unit.lower() not in after_set:
            refs = [r for r in before if r.unit.lower() == unit.lower()]
            if refs:
                findings.append(_finding("Подразделение", "Подразделение до реорганизации не найдено после", unit, refs[0]))
    for unit in after_units:
        if unit.lower() not in before_set:
            refs = [r for r in after if r.unit.lower() == unit.lower()]
            if refs:
                findings.append(_finding("Подразделение", "В документах после найдено новое подразделение", unit, refs[0]))
    # Every displayed finding has at least one direct source reference by construction.
    conclusion = (f"Сопоставлено функций: до — {len(before)}, после — {len(after)}; "
                 f"подразделений: до — {len(before_units)}, после — {len(after_units)}. "
                 f"Выявлено {len(findings)} предварительных наблюдений. Они основаны на извлечённых фрагментах "
                 "и требуют проверки ответственным специалистом; отсутствие совпадения не доказывает фактическую утрату функции.")
    return AnalysisResult(before_units, after_units, before, after, findings, conclusion)
