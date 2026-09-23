from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    document: str
    location: str
    excerpt: str

    @property
    def label(self) -> str:
        return f"{self.document} — {self.location}"


@dataclass(frozen=True)
class Segment:
    source: Source
    text: str


@dataclass
class ExtractedDocument:
    name: str
    kind: str
    segments: list[Segment] = field(default_factory=list)


@dataclass
class FunctionRecord:
    unit: str
    text: str
    source: Source


@dataclass
class Finding:
    category: str
    title: str
    details: str
    sources: list[Source]
    confidence: str = "Предварительно"


@dataclass
class AnalysisResult:
    units_before: list[str]
    units_after: list[str]
    functions_before: list[FunctionRecord]
    functions_after: list[FunctionRecord]
    findings: list[Finding]
    conclusion: str
