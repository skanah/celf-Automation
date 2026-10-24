from config import Config


class CellReportFiller:
    def __init__(self, session, log=print):
        self.session = session
        self.log = log

    async def submit(self, row: dict) -> dict:
        acc = self.session.account_id
        result = {"account": acc, "type": "cell",
                  "date": row.get("date_of_meeting"),
                  "status": "failed", "error": None}
        page = self.session.page

        try:
            self.log(f"[{acc}] → Cell Report form")
            await page.goto(Config.CELL_REPORT_URL, wait_until="networkidle")

            # ---- Type of meeting (radio) ----
            meeting_type = str(row.get("type_of_meeting", "")).strip()
            if meeting_type:
                # Try both value and label match
                radio = page.locator(
                    'input[name="CmisCellLeadersReport[type_of_meeting]"]'
                )
                count = await radio.count()
                matched = False
                for i in range(count):
                    r = radio.nth(i)
                    val = await r.get_attribute("value") or ""
                    if val.strip().lower() == meeting_type.lower():
                        await r.check()
                        matched = True
                        break
                if not matched:
                    # fallback: use label
                    await page.check(
                        f'label:has-text("{meeting_type}") input'
                    )

            # ---- Date / time ----
            if row.get("date_of_meeting"):
                await page.fill('#CmisCellLeadersReport_date_of_meeting',
                                str(row["date_of_meeting"]))
            if row.get("time_meeting_started"):
                await page.fill('#CmisCellLeadersReport_time_meeting_started',
                                str(row["time_meeting_started"]))
            if row.get("time_meeting_ended"):
                await page.fill('#CmisCellLeadersReport_time_meeting_ended',
                                str(row["time_meeting_ended"]))

            # ---- Numbers ----
            await self._fill_number(page,
                '#CmisCellLeadersReport_total_no_at_cell_meeting',
                row.get("total_no_at_cell_meeting"))
            await self._fill_number(page,
                '#CmisCellLeadersReport_1_total_no_at_bible_study',
                row.get("total_no_at_bible_study"))
            await self._fill_number(page,
                '#CmisCellLeadersReport_no_of_first_timers',
                row.get("no_of_first_timers"))
            await self._fill_number(page,
                '#CmisCellLeadersReport_no_of_new_converts',
                row.get("no_of_new_converts"))
            await self._fill_number(page,
                '#CmisCellLeadersReport_no_of_infilling',
                row.get("no_of_infilling"))
            await self._fill_number(page,
                '#CmisCellLeadersReport_no_of_members_at_wed_service',
                row.get("no_of_members_at_wed_service"))
            await self._fill_number(page,
                '#CmisCellLeadersReport_no_of_members_at_sun_service',
                row.get("no_of_members_at_sun_service"))

            # ---- Testimony ----
            if row.get("testimony"):
                await page.fill('#CmisCellLeadersReport_testimony',
                                str(row["testimony"]))

            # ---- Submit ----
            self.log(f"[{acc}] Submitting cell report…")
            await page.click('input[name="yt0"]')
            await page.wait_for_load_state("networkidle")

            # Detect validation errors
            if await page.locator('.error-summary, .has-error, .alert-danger').count() > 0:
                err_text = await page.locator('.error-summary, .has-error').first.inner_text()
                raise RuntimeError(f"Validation: {err_text[:200]}")

            result["status"] = "success"
            self.log(f"[{acc}] ✅ Cell report saved for {row.get('date_of_meeting')}")

        except Exception as e:
            result["error"] = str(e)
            self.log(f"[{acc}] ❌ Cell report failed: {e}")

        return result

    async def _fill_number(self, page, selector, value):
        if value is None or value == "":
            return
        try:
            await page.fill(selector, str(value))
        except Exception:
            pass