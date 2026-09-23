from .models import AnalysisResult


def to_markdown(result: AnalysisResult) -> str:
    lines = [
        "# Аналитическое заключение",
        "",
        result.conclusion,
        "",
        "> Результаты автоматического анализа носят рекомендательный характер "
        "и требуют экспертной проверки.",
        "",
        "## Сводка",
        "",
        f"- Найдено наблюдений: **{len(result.findings)}**",
        f"- Функций в версии «До»: **{len(result.functions_before)}**",
        f"- Функций в версии «После»: **{len(result.functions_after)}**",
        "",
        "## Наблюдения",
        "",
    ]

    for number, finding in enumerate(result.findings, start=1):
        lines += [
            f"### {number}. {finding.title}",
            "",
            finding.details,
            "",
            "Источники:",
        ]

        if finding.sources:
            lines += [
                f"- **{source.label}**: «{source.excerpt}»"
                for source in finding.sources
            ]
        else:
            lines.append("- Источники не указаны.")

        lines.append("")

    return "\n".join(lines)