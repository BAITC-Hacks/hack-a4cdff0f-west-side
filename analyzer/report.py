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
        "## Наблюдения",
        "",
    ]

    for finding in result.findings:
        lines += [
            f"### {finding.title}",
            finding.details,
            "",
            "Источники:",
        ]
        lines += [
            f"- **{source.label}**: «{source.excerpt}»"
            for source in finding.sources
        ]
        lines.append("")

    return "\n".join(lines)