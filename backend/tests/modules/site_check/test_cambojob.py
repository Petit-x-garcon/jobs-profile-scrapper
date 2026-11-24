from app.modules.site_check import cambojob
from app.modules.site_check.schemas import SiteCheckOut


def test_hidden_tabs_directory_and_job_detail() -> None:
    base = "https://www.cambojob.com"
    result = SiteCheckOut(url=base, result="successful", robots_status="allowed", message="")
    panels = [
        f'<div class="content-part2" style="display:none"><div class="left">'
        f'<h3 data-href="/jobs/jobs-show-{job_id}-.htm">{title}</h3></div></div>'
        for job_id, title in [
            (123, "Sales Supervisor"),
            (124, "Designer"),
            (123, "Sales Supervisor"),
        ]
    ]
    html = (
        '<span data-event="new_job">latest</span><span data-event="popular_job">popular</span>'
        '<span data-event="high_salary_job">High-paying</span><div id="jobsContent">'
        + "".join(panels)
        + '</div><a data-url="/jobs/jobs_list.htm">More Positions</a>'
        + '<a href="https://other.test/jobs/jobs-show-1-.htm">Offsite</a>'
    )
    assert cambojob.inspect_page(html, result) == []
    assert result.job_count == 2
    assert result.job_tabs["High-paying"] == ["Sales Supervisor"]
    assert result.links == [f"{base}/jobs/jobs_list.htm", *result.job_urls]
    assert len(result.links) == 3

    result.url = result.links[0]
    cambojob.inspect_page('<a href="/jobs/jobs_list/page/2.htm">2</a>', result)
    assert result.links == [f"{base}/jobs/jobs_list/page/2.htm"]

    result.url = f"{base}/jobs/jobs-show-123-.htm"
    detail = (
        '<div class="job-detail-left"><h3 class="jobs_name">Sales Supervisor</h3></div>'
        '<div class="job-desc"><div class="job-news-body">Lead the team.</div></div>'
        '<h3><a href="/company/company-show-1-.htm">The FLORA</a></h3>'
    )
    (job,) = cambojob.inspect_page(detail, result)
    assert (job.title, job.company, job.description) == (
        "Sales Supervisor",
        "The FLORA",
        "Lead the team.",
    )
    assert result.job_urls == [result.url]
