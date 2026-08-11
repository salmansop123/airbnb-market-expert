from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_user_plan_tier
from app.core.entitlements import assert_can_report, record_usage
from app.db.models import Prediction, Report, User
from app.db.session import get_db
from app.modules.agents import agents
from app.modules.properties.storage import upload_file

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportOut(BaseModel):
    id: UUID
    prediction_id: UUID
    title: str
    summary: str | None
    url: str | None
    status: str
    content_markdown: str | None

    model_config = {"from_attributes": True}


def _report_html(payload: dict, markdown: str) -> str:
    recs = payload.get("recommendations") or []
    rec_html = "".join(
        f"<li><strong>{(r.get('title') if isinstance(r, dict) else r)}</strong>"
        f"{(' — ' + r.get('detail', '')) if isinstance(r, dict) else ''}</li>"
        for r in recs[:8]
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  body {{ font-family: Georgia, serif; color: #0B1220; margin: 40px; }}
  h1 {{ font-size: 28px; margin-bottom: 4px; }}
  .muted {{ color: #5B6B7C; }}
  .hero {{ background: #0B1220; color: #F7F3EC; padding: 24px; border-radius: 12px; margin: 24px 0; }}
  .grid {{ display: flex; gap: 16px; }}
  .card {{ flex: 1; border: 1px solid #E8EEF7; border-radius: 10px; padding: 16px; }}
  .price {{ font-size: 40px; color: #E85D4C; }}
  ul {{ padding-left: 18px; }}
  pre {{ white-space: pre-wrap; font-family: Georgia, serif; font-size: 12px; color: #5B6B7C; }}
</style></head><body>
  <p class="muted">StayPrice AI · Professional Report</p>
  <h1>{payload.get('property')}</h1>
  <p class="muted">{payload.get('city') or ''}</p>
  <div class="hero">
    <div class="muted">Suggested nightly rate</div>
    <div class="price">${payload.get('suggested_price') or '—'}</div>
    <div>Band ${payload.get('min_price')} – ${payload.get('max_price')} · Occupancy {round((payload.get('occupancy') or 0)*100)}%</div>
  </div>
  <div class="grid">
    <div class="card"><div class="muted">Monthly revenue</div><strong>${payload.get('monthly_revenue')}</strong></div>
    <div class="card"><div class="muted">Annual revenue</div><strong>${payload.get('annual_revenue')}</strong></div>
    <div class="card"><div class="muted">Vision overall</div><strong>{(payload.get('vision') or {}).get('overall') or '—'}</strong></div>
  </div>
  <h2>Recommendations</h2>
  <ul>{rec_html or '<li>No recommendations</li>'}</ul>
  <h2>AI summary</h2>
  <pre>{markdown}</pre>
</body></html>"""


@router.post("/predictions/{prediction_id}/report", response_model=ReportOut)
async def generate_report(
    prediction_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    tier = get_user_plan_tier(user)
    await assert_can_report(tier)

    result = await db.execute(
        select(Prediction)
        .options(
            selectinload(Prediction.property),
            selectinload(Prediction.vision_analysis),
            selectinload(Prediction.report),
        )
        .where(Prediction.id == prediction_id)
    )
    pred = result.scalar_one_or_none()
    if not pred or pred.property.user_id != user.id:
        raise HTTPException(status_code=404, detail="Prediction not found")

    if pred.report and pred.report.status == "ready":
        return ReportOut.model_validate(pred.report)

    payload = {
        "property": pred.property.title,
        "city": pred.property.city,
        "suggested_price": pred.suggested_price,
        "min_price": pred.min_price,
        "max_price": pred.max_price,
        "monthly_revenue": pred.monthly_revenue,
        "annual_revenue": pred.annual_revenue,
        "occupancy": pred.expected_occupancy,
        "strengths": pred.strengths,
        "weaknesses": pred.weaknesses,
        "recommendations": pred.recommendations,
        "explanation": pred.explanation,
        "vision": {
            "overall": pred.vision_analysis.overall_score if pred.vision_analysis else None,
            "luxury": pred.vision_analysis.luxury_score if pred.vision_analysis else None,
        },
    }
    markdown = await agents.report_agent(payload)
    html = _report_html(payload, markdown)
    try:
        from weasyprint import HTML

        pdf_bytes = HTML(string=html).write_pdf()
    except Exception:
        pdf_bytes = html.encode("utf-8")

    key = f"reports/{prediction_id}.pdf"
    url = await upload_file(key, pdf_bytes, "application/pdf")

    report = pred.report
    if not report:
        report = Report(prediction_id=pred.id, title=f"Report — {pred.property.title}")
        db.add(report)
    report.summary = (markdown[:400] + "…") if len(markdown) > 400 else markdown
    report.content_markdown = markdown
    report.s3_key = key
    report.url = url
    report.status = "ready"
    await record_usage(db, user.id, "report", resource_type="prediction", resource_id=str(prediction_id))
    await db.flush()
    return ReportOut.model_validate(report)


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.prediction).selectinload(Prediction.property))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report or report.prediction.property.user_id != user.id:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportOut.model_validate(report)
