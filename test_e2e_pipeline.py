"""
E2E 테스트: 설문 응답 -> 가상 뇌파 -> DB 검색 -> PDF 생성 파이프라인을 5회 반복 실행.
단계별 소요 시간 수집, 병목 구간 및 에러 리포트 생성.
"""
import os
import sys
import time
from typing import Dict, List

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import run_full_pipeline, PipelineResult


def make_responses_from_loader(vary_run: int = 0) -> Dict[int, int]:
    """survey_items.csv 기반 96문항 응답 생성. vary_run으로 5회 중 약간씩 다른 응답 가능."""
    from data_loader import SurveyDataLoader
    loader = SurveyDataLoader()
    responses = {}
    for item in loader.items:
        base = item.예시문항 if hasattr(item, "예시문항") else 3
        # 1~5 유지: run별로 일부 문항만 ±1 (경계 처리)
        if vary_run > 0:
            shift = (item.전체순번 + vary_run) % 5
            if shift == 0:
                base = min(5, base + 1)
            elif shift == 1:
                base = max(1, base - 1)
        responses[item.전체순번] = max(1, min(5, base))
    return responses


def run_e2e_five_times() -> List[PipelineResult]:
    """파이프라인 5회 실행, 회차별 결과 리스트 반환."""
    results = []
    for run in range(1, 6):
        print(f"[Run {run}/5] 파이프라인 실행 중...")
        responses = make_responses_from_loader(vary_run=run)
        r = run_full_pipeline(
            responses=responses,
            customer_name="E2E테스트",
            output_pdf_name=f"e2e_run_{run}_{int(time.time())}.pdf",
        )
        results.append(r)
        if r.success:
            print(f"  -> 성공, PDF: {r.pdf_path}, total={r.timings_ms.get('total', 0):.0f}ms")
        else:
            print(f"  -> 실패: {r.error}")
    return results


def build_report(results: List[PipelineResult]) -> str:
    """병목 구간 및 에러 리포트 텍스트 생성."""
    lines = [
        "# E2E 파이프라인 5회 반복 테스트 리포트",
        "",
        f"**총 실행**: 5회",
        f"**성공**: {sum(1 for r in results if r.success)}회",
        f"**실패**: {sum(1 for r in results if not r.success)}회",
        "",
        "---",
        "",
        "## 1. 단계별 소요 시간 (ms)",
        "",
    ]

    step_names = ["1_survey_scoring", "2_mock_eeg", "3_combined_sbi", "4_db_search", "5_pdf_generate", "total"]
    step_labels = ["설문 채점", "가상 뇌파", "통합 SBI/리포트", "DB 검색", "PDF 생성", "전체"]

    # 성공한 회차만 시간 집계
    success_results = [r for r in results if r.success and r.timings_ms]
    if success_results:
        lines.append("| 단계 | 평균(ms) | 최소(ms) | 최대(ms) |")
        lines.append("|------|----------|----------|----------|")
        for step, label in zip(step_names, step_labels):
            vals = [r.timings_ms.get(step) for r in success_results if r.timings_ms.get(step) is not None]
            if vals:
                avg = sum(vals) / len(vals)
                mn, mx = min(vals), max(vals)
                lines.append(f"| {label} | {avg:.1f} | {mn:.1f} | {mx:.1f} |")
            else:
                lines.append(f"| {label} | - | - | - |")

        # 병목: 평균 기준 가장 느린 단계
        avg_by_step = {}
        for step in step_names:
            if step == "total":
                continue
            vals = [r.timings_ms.get(step) for r in success_results if r.timings_ms.get(step) is not None]
            if vals:
                avg_by_step[step] = sum(vals) / len(vals)
        if avg_by_step:
            bottleneck = max(avg_by_step, key=avg_by_step.get)
            idx = step_names.index(bottleneck)
            lines.append("")
            lines.append(f"**병목 구간**: {step_labels[idx]} (평균 {avg_by_step[bottleneck]:.1f} ms)")
    else:
        lines.append("성공한 실행이 없어 단계별 시간을 집계할 수 없습니다.")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. 회차별 요약")
    lines.append("")
    for i, r in enumerate(results, 1):
        status = "성공" if r.success else "실패"
        line = f"- **Run {i}**: {status}"
        if r.success and r.timings_ms:
            line += f", total={r.timings_ms.get('total', 0):.0f} ms"
        if not r.success and r.error:
            line += " - " + (r.error or "")
        lines.append(line)

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. 에러 목록")
    lines.append("")
    errors = [(i, r.error) for i, r in enumerate(results, 1) if not r.success and r.error]
    if errors:
        for run_no, err in errors:
            lines.append(f"- **Run {run_no}**: `{err}`")
    else:
        lines.append("발생한 에러 없음.")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. 결론 및 권장 사항")
    lines.append("")
    if not success_results:
        lines.append("- 5회 모두 실패했습니다. 위 에러 목록을 확인해 수정이 필요합니다.")
    else:
        lines.append("- 병목 구간을 확인해 해당 단계(채점/DB/PDF 등) 최적화를 권장합니다.")
        if errors:
            lines.append("- 일부 회차 실패 시 네트워크/파일 경로/DB 초기화 등을 점검하세요.")
    return "\n".join(lines)


def main():
    print("E2E 파이프라인 5회 반복 테스트 시작")
    results = run_e2e_five_times()
    report = build_report(results)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "E2E_PIPELINE_REPORT.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n리포트 저장: {out_path}")
    try:
        print(report)
    except UnicodeEncodeError:
        print(report.encode("utf-8", errors="replace").decode("utf-8"))


if __name__ == "__main__":
    main()
