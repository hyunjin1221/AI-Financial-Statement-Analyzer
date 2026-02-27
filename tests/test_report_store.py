from pathlib import Path

from app.services.report_store import list_recent_reports, save_markdown_report


def test_save_and_list_reports(tmp_path: Path) -> None:
    out_dir = tmp_path / "reports"
    p1 = save_markdown_report("# report1", "AAA", "10-K", output_dir=str(out_dir))
    p2 = save_markdown_report("# report2", "BBB", "10-Q", output_dir=str(out_dir))

    assert p1.exists()
    assert p2.exists()

    recent = list_recent_reports(limit=5, output_dir=str(out_dir))
    assert len(recent) == 2
    assert all(path.suffix == ".md" for path in recent)
